import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.core.security import get_current_patient
from app.main import app
from app.models.patient import Patient


@pytest.fixture
def mock_patient():
    """Create a mock patient for testing."""
    return Patient(
        id=uuid.uuid4(),
        cognito_sub="test-user-123",
        display_name="Test Patient",
        consent_accepted=True,
        consent_accepted_on=datetime.now(timezone.utc).date(),
    )


@pytest.fixture
def valid_jwt_payload(mock_patient):
    """Create a valid JWT payload for testing."""
    now = datetime.now(timezone.utc)
    return {
        "sub": mock_patient.cognito_sub,
        "aud": "test-client-id",
        "token_use": "id",
        "auth_time": int(now.timestamp()),
        "exp": int((now + timedelta(hours=1)).timestamp()),
        "iat": int(now.timestamp()),
        "iss": f"https://cognito-idp.us-east-1.amazonaws.com/us-east-1_XXXXXXXXX",
    }


@pytest.fixture
def mock_jwks():
    """Create mock JWKS response for Cognito."""
    return {
        "keys": [
            {
                "alg": "RS256",
                "e": "AQAB",
                "kid": "test-key-id",
                "kty": "RSA",
                "n": "test-key-modulus",
                "use": "sig",
            }
        ]
    }


class TestGetCurrentPatient:
    """Test suite for get_current_patient FastAPI dependency."""

    async def test_valid_token_returns_patient(
        self, mock_patient, valid_jwt_payload, mock_jwks, db_session
    ):
        """
        GREEN TEST: Should pass after implementing get_current_patient.
        
        Given a valid Cognito JWT token
        When get_current_patient is called
        It should return the corresponding Patient object
        """
        # Arrange
        db_session.add(mock_patient)
        await db_session.commit()

        # Mock the entire verify_token function to return our payload
        mock_token = "valid.jwt.token"
        
        with patch("app.core.security.verify_token") as mock_verify:
            mock_verify.return_value = valid_jwt_payload

            # Create mock credentials
            from fastapi.security import HTTPAuthorizationCredentials
            mock_credentials = HTTPAuthorizationCredentials(
                scheme="Bearer",
                credentials=mock_token
            )

            # Act
            result = await get_current_patient(
                credentials=mock_credentials,
                db=db_session
            )
            
            # Assert
            assert result is not None
            assert result.id == mock_patient.id
            assert result.cognito_sub == mock_patient.cognito_sub

    async def test_invalid_signature_returns_401(self, db_session):
        """
        GREEN TEST: Should pass after implementing get_current_patient.
        
        Given a JWT with invalid signature
        When get_current_patient is called
        It should raise HTTPException with 401 status
        """
        # Arrange
        mock_token = "invalid.signature.token"
        
        with patch("app.core.security.verify_token", side_effect=Exception("Invalid signature")):
            # Create mock credentials
            from fastapi.security import HTTPAuthorizationCredentials
            mock_credentials = HTTPAuthorizationCredentials(
                scheme="Bearer",
                credentials=mock_token
            )

            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                await get_current_patient(credentials=mock_credentials, db=db_session)
            
            assert exc_info.value.status_code == 401
            assert exc_info.value.detail in ["Invalid token", "Authentication error"]

    async def test_expired_token_returns_401(self, db_session):
        """
        GREEN TEST: Should pass after implementing get_current_patient.
        
        Given an expired JWT token
        When get_current_patient is called
        It should raise HTTPException with 401 status
        """
        # Arrange
        mock_token = "expired.jwt.token"
        
        with patch("app.core.security.verify_token", side_effect=Exception("Token has expired")):
            # Create mock credentials
            from fastapi.security import HTTPAuthorizationCredentials
            mock_credentials = HTTPAuthorizationCredentials(
                scheme="Bearer",
                credentials=mock_token
            )

            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                await get_current_patient(credentials=mock_credentials, db=db_session)
            
            assert exc_info.value.status_code == 401
            assert exc_info.value.detail in ["Invalid token", "Authentication error"]

    async def test_patient_not_found_returns_401(self, valid_jwt_payload, db_session):
        """
        GREEN TEST: Should pass after implementing get_current_patient.
        
        Given a valid JWT for a patient that doesn't exist in database
        When get_current_patient is called
        It should raise HTTPException with 401 status
        """
        # Arrange
        mock_token = "valid.jwt.for.nonexistent.user"
        
        with patch("app.core.security.verify_token") as mock_verify:
            mock_verify.return_value = valid_jwt_payload

            # Create mock credentials
            from fastapi.security import HTTPAuthorizationCredentials
            mock_credentials = HTTPAuthorizationCredentials(
                scheme="Bearer",
                credentials=mock_token
            )

            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                await get_current_patient(credentials=mock_credentials, db=db_session)
            
            assert exc_info.value.status_code == 401
            assert "Patient not found" in str(exc_info.value.detail)


class TestMeEndpoint:
    """Test suite for GET /me endpoint."""

    def test_get_me_returns_patient_id_with_valid_token(
        self, mock_patient
    ):
        """
        GREEN TEST: Should pass after implementing GET /me endpoint.
        
        Given a valid Cognito JWT token
        When GET /me is called
        It should return the patient's ID
        """
        # Create test client with dependency override
        def override_get_current_patient():
            return mock_patient

        app.dependency_overrides[get_current_patient] = override_get_current_patient
        
        client = TestClient(app)

        try:
            # Act
            response = client.get("/me", headers={"Authorization": "Bearer valid.token"})

            # Assert
            assert response.status_code == 200
            assert response.json() == {"patient_id": str(mock_patient.id)}
        finally:
            # Clean up dependency override
            app.dependency_overrides.clear()

    def test_get_me_returns_401_without_token(self):
        """
        GREEN TEST: Should pass after implementing GET /me endpoint.
        
        Given no Authorization header
        When GET /me is called
        It should return 401 Unauthorized
        """
        # Arrange
        client = TestClient(app)

        # Act
        response = client.get("/me")

        # Assert
        assert response.status_code == 401