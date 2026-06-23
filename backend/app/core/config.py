from pathlib import Path
from pydantic import AliasChoices, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
 
BASE_DIR = Path(__file__).resolve().parents[2]

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "GlucoChef Backend"
    debug: bool = False
    environment: str = "development"
    database_url: str  # Required — set via DATABASE_URL in .env or environment
    # Kept separate from debug: SQL echo logs bind parameters which may contain PHI.
    # Never enable in staging or production.
    sql_echo: bool = False
    
    # AWS Cognito configuration
    cognito_user_pool_id: str  # Required — set via COGNITO_USER_POOL_ID in .env
    cognito_region: str  # Required — set via COGNITO_REGION in .env  
    cognito_app_client_id: str  # Required — set via COGNITO_APP_CLIENT_ID in .env

    # PHI field-level encryption key (Phase 5)
    # Must be a valid Fernet key (32 url-safe base64 bytes).
    # Generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    encryption_key: str  # Required — set via ENCRYPTION_KEY in .env

    # AI provider configuration (Phase 8)
    ai_provider: str = "openai"  # Only "openai" supported in MVP
    ai_api_key: str = Field(
        default="",
        validation_alias=AliasChoices("AI_API_KEY", "OPENAI_API_KEY"),
    )
    ai_model: str = "gpt-4o-mini"  # Default model; override via AI_MODEL in .env

    @field_validator("ai_provider")
    @classmethod
    def validate_ai_provider(cls, v: str) -> str:
        """Only 'openai' is supported in MVP."""
        if v != "openai":
            raise ValueError(
                f"Unsupported AI provider '{v}'. Only 'openai' is supported in MVP."
            )
        return v

    @field_validator("encryption_key")
    @classmethod
    def validate_encryption_key(cls, v: str) -> str:
        """Fail at startup — not mid-request — if the key is not a valid Fernet key."""
        from cryptography.fernet import Fernet, InvalidToken  # noqa: F401 (lazy import)
        try:
            Fernet(v.encode())
        except Exception as exc:
            raise ValueError(
                "ENCRYPTION_KEY is not a valid Fernet key. "
                "Generate one with: python -c \"from cryptography.fernet import Fernet; "
                "print(Fernet.generate_key().decode())\""
            ) from exc
        return v

    @model_validator(mode="after")
    def validate_cognito_config_production(self):
        """Validate Cognito configuration in production environments."""
        # Skip validation in development to allow empty defaults
        if self.environment == "development":
            return self
        
        # Validate user pool ID
        if not self.cognito_user_pool_id or self.cognito_user_pool_id.strip() == "":
            raise ValueError("Cognito user pool ID cannot be empty in production")
        if self.cognito_user_pool_id == "us-east-1_XXXXXXXXX" or len(self.cognito_user_pool_id) < 10:
            raise ValueError("Invalid Cognito user pool ID format")
        self.cognito_user_pool_id = self.cognito_user_pool_id.strip()
        
        # Validate region (AWS regions are like us-east-1, eu-west-1, ap-southeast-2, etc.)
        if not self.cognito_region or self.cognito_region.strip() == "":
            raise ValueError("Cognito region cannot be empty in production")
        if not (len(self.cognito_region) >= 9 and len(self.cognito_region) <= 15):
            raise ValueError("Invalid AWS region format")
        self.cognito_region = self.cognito_region.strip()
        
        # Validate app client ID
        if not self.cognito_app_client_id or self.cognito_app_client_id.strip() == "":
            raise ValueError("Cognito app client ID cannot be empty in production")
        if len(self.cognito_app_client_id) < 10:
            raise ValueError("Invalid Cognito app client ID format")
        self.cognito_app_client_id = self.cognito_app_client_id.strip()
        
        return self


settings = Settings()
