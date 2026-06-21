from sqlalchemy import Text

# EncryptedString placeholder — Phase 3 only.
# Replaced by the real Fernet AES-256 TypeDecorator in Phase 5 (see ADR-002).
# All PHI columns import from here so that the Phase 5 swap is a single-file change.
# ADR-002: docs/decisions/ADR-002-field-level-phi-encryption.md
# TODO(Phase 5): implement PHICryptoService and replace Text with the TypeDecorator.
EncryptedString = Text
