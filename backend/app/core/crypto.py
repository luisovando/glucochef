"""
PHI field-level encryption — Phase 5.

EncryptedString is a SQLAlchemy TypeDecorator that transparently encrypts PHI
column values using Fernet (AES-128-CBC + HMAC-SHA256) before persisting them
and decrypts them when loading from the database.

Design decision (see memory-bank/decisions.md):
  Fernet is used instead of raw AES-256-GCM because it provides authenticated
  encryption with a simpler key-management interface. The key is a 32-byte
  url-safe base64 string stored in ENCRYPTION_KEY env var. Key rotation is
  deferred to v2.

All PHI columns import EncryptedString from this module so that future changes
(e.g. key versioning) are a single-file update.
"""

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import String
from sqlalchemy.engine import Dialect
from sqlalchemy.types import TypeDecorator


def _get_fernet() -> Fernet:
    """Return a Fernet instance using the key from settings."""
    # Import lazily to avoid circular imports at module load time.
    from app.core.config import settings
    return Fernet(settings.encryption_key.encode())


class EncryptedString(TypeDecorator):
    """
    SQLAlchemy TypeDecorator that stores values as Fernet-encrypted ciphertext.

    Usage:
        class LabResult(Base):
            value: Mapped[str] = mapped_column(EncryptedString)

    The underlying column is TEXT. Fernet produces url-safe base64 output
    (always printable ASCII), so no binary column type is required.
    """

    impl = String
    cache_ok = True

    def process_bind_param(self, value: str | None, dialect: Dialect) -> str | None:
        """Encrypt plaintext before writing to the database."""
        if value is None:
            return None
        fernet = _get_fernet()
        return fernet.encrypt(value.encode()).decode()

    def process_result_value(self, value: str | None, dialect: Dialect) -> str | None:
        """Decrypt ciphertext when reading from the database."""
        if value is None:
            return None
        try:
            fernet = _get_fernet()
            return fernet.decrypt(value.encode()).decode()
        except InvalidToken as exc:
            raise ValueError(
                "Failed to decrypt PHI column — key mismatch or data corruption"
            ) from exc
