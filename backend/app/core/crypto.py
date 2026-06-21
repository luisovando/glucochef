from sqlalchemy import Text

# EncryptedString placeholder — Phase 3 only.
# Replaced by the real Fernet AES TypeDecorator in Phase 5 (app/core/crypto.py).
# All PHI columns import from here so that the Phase 5 swap is a single-file change.
EncryptedString = Text
