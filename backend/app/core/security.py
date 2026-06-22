import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from httpx import AsyncClient
from jose import jwk, jwt
from jose.exceptions import JWTError, JWSError, ExpiredSignatureError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.db.session import get_db
from app.models.patient import Patient

logger = logging.getLogger(__name__)

# HTTP Bearer token scheme
security = HTTPBearer(auto_error=False)

# JWKS cache to avoid repeated network calls
_jwks_cache = {"data": None, "expires_at": None}
_jwks_lock = asyncio.Lock()


async def get_jwks() -> dict:
    """
    Fetch the JSON Web Key Set (JWKS) from AWS Cognito with caching.
    
    JWKS rarely change (only during key rotation), so we cache them for 1 hour
    to avoid unnecessary network calls on every authentication.
    
    Returns:
        dict: The JWKS containing public keys for token verification.
    """
    now = datetime.now(timezone.utc)
    
    async with _jwks_lock:
        # Double-check pattern to avoid holding lock during cache hit
        if _jwks_cache["data"] and _jwks_cache["expires_at"] > now:
            return _jwks_cache["data"]
        
        # Fetch fresh JWKS from Cognito
        jwks_url = f"https://cognito-idp.{settings.cognito_region}.amazonaws.com/{settings.cognito_user_pool_id}/.well-known/jwks.json"
        
        try:
            async with AsyncClient() as client:
                response = await client.get(jwks_url, timeout=10.0)
                response.raise_for_status()
                jwks_data = response.json()
                
                # Cache the result for 1 hour
                _jwks_cache["data"] = jwks_data
                _jwks_cache["expires_at"] = now + timedelta(hours=1)
                
                logger.debug("JWKS refreshed from Cognito")
                return jwks_data
                
        except Exception as e:
            logger.error(f"Failed to fetch JWKS from Cognito: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication service unavailable",
            ) from e


async def _clear_jwks_cache() -> None:
    """Clear the JWKS cache - used during key rotation or auth failures."""
    async with _jwks_lock:
        _jwks_cache["data"] = None
        _jwks_cache["expires_at"] = None


async def verify_token(token: str, _retry_count: int = 0) -> dict:
    """
    Verify a Cognito JWT token and return its payload.
    
    Args:
        token: The JWT token to verify.
        _retry_count: Internal retry counter for cache invalidation.
        
    Returns:
        dict: The decoded token payload.
        
    Raises:
        HTTPException: If token is invalid, expired, or malformed.
    """
    try:
        # Get the JWKS from Cognito
        jwks = await get_jwks()
        
        # Decode the token without verification first to get the key ID
        unverified_header = jwt.get_unverified_header(token)
        key_id = unverified_header.get("kid")
        
        if not key_id:
            logger.warning("Token missing key ID")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token missing key ID",
            )
        
        # Find the matching key in JWKS
        key = None
        for jwk_key in jwks.get("keys", []):
            if jwk_key.get("kid") == key_id:
                key = jwk_key
                break
        
        if not key:
            logger.warning(f"Token key not found: {key_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token key not found",
            )
        
        # Convert JWK to PEM format for jose
        public_key = jwk.construct(key)
        
        # Verify and decode the token
        payload = jwt.decode(
            token,
            public_key.to_pem().decode(),
            algorithms=["RS256"],
            audience=settings.cognito_app_client_id,
            issuer=f"https://cognito-idp.{settings.cognito_region}.amazonaws.com/{settings.cognito_user_pool_id}",
        )
        
        # Validate token type - must be an ID token, not access token
        token_use = payload.get("token_use")
        if token_use != "id":
            logger.warning(f"Invalid token type: {token_use}, expected 'id'")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type: expected ID token",
            )
        
        return payload
        
    except ExpiredSignatureError:
        logger.warning("Token has expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except (JWTError, JWSError) as e:
        logger.warning(f"JWT validation failed: {str(e)}")
        
        # If this is the first attempt and we have cached data, invalidate cache and retry
        if _retry_count == 0 and _jwks_cache["data"] is not None:
            logger.warning("JWT validation failed, invalidating JWKS cache and retrying")
            await _clear_jwks_cache()
            return await verify_token(token, _retry_count=1)
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        ) from e
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Unexpected error during token verification: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication error",
        ) from e


async def get_current_patient(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: AsyncSession = Depends(get_db),
) -> Patient:
    """
    FastAPI dependency that validates Cognito JWT and returns the current Patient.
    
    This dependency:
    1. Extracts the Bearer token from the Authorization header
    2. Verifies the token signature and claims against Cognito JWKS
    3. Looks up the Patient by the 'sub' claim from the token
    4. Returns the Patient object or raises 401 if not found
    
    Args:
        credentials: The HTTP Bearer credentials from the request header.
        db: The database session.
        
    Returns:
        Patient: The authenticated patient object.
        
    Raises:
        HTTPException: If token is invalid or patient not found.
    """
    # Manual validation since auto_error=False
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header is required",
        )
    
    try:
        # Verify the token and get payload
        payload = await verify_token(credentials.credentials)
        
        # Get the Cognito subject (user ID) from the token
        cognito_sub = payload.get("sub")
        if not cognito_sub:
            logger.warning("Token missing subject claim")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token missing subject claim",
            )
        
        # Look up the patient in the database
        result = await db.execute(
            select(Patient).where(Patient.cognito_sub == cognito_sub)
        )
        patient = result.scalar_one_or_none()
        
        if not patient:
            logger.warning(f"Patient not found for cognito_sub: {cognito_sub}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Patient not found",
            )
        
        logger.debug(f"Successfully authenticated patient: {patient.id}")
        return patient
        
    except HTTPException as e:
        # Log failed authentication attempts for security monitoring
        logger.warning(f"Authentication failed: {e.detail}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during patient lookup: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication error",
        ) from e