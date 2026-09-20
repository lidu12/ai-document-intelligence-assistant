"""Security & Cryptography Utilities

Handles password hashing (bcrypt via passlib) and JSON Web Token (JWT)
encoding and decoding for stateless authentication.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Union
import jwt
from passlib.context import CryptContext

from app.core.config import settings

# ------------------------------------------------------------------------------
# 1. Password Hashing Context (Bcrypt)
# ------------------------------------------------------------------------------
# Passlib handles salting automatically with industry-standard bcrypt.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plaintext password against a stored bcrypt hash.

    Args:
        plain_password: The raw password submitted by the user.
        hashed_password: The salted hash retrieved from the database.

    Returns:
        bool: True if password matches the hash, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generates a secure, salted bcrypt hash from a plaintext password.

    Args:
        password: Plaintext password to hash.

    Returns:
        str: 60-character bcrypt hash string including salt and algorithm version.
    """
    return pwd_context.hash(password)


# ------------------------------------------------------------------------------
# 2. JSON Web Token (JWT) Utilities
# ------------------------------------------------------------------------------
def create_access_token(
    subject: Union[str, int],
    expires_delta: Optional[timedelta] = None,
    extra_claims: Optional[Dict[str, Any]] = None,
) -> str:
    """Encodes a signed JWT access token.

    Args:
        subject: The unique identifier of the user (typically user.id).
        expires_delta: Optional custom token lifespan. Defaults to settings.ACCESS_TOKEN_EXPIRE_MINUTES.
        extra_claims: Optional extra key-value pairs to embed into the token payload.

    Returns:
        str: Encoded, cryptographically signed JWT string.
    """
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    payload: Dict[str, Any] = {
        "sub": str(subject),          # Subject claim (user identifier)
        "iat": int(now.timestamp()),    # Issued-at timestamp (seconds)
        "exp": int(expire.timestamp()), # Expiration timestamp (seconds)
        "type": "access",               # Token type discriminator
    }

    if extra_claims:
        payload.update(extra_claims)

    encoded_jwt: str = jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decodes and cryptographically verifies a JWT access token.

    Args:
        token: The raw JWT string from the HTTP Authorization header.

    Returns:
        Optional[Dict[str, Any]]: The validated token claims dictionary if valid,
                                  or None if the token has expired or is invalid.
    """
    try:
        decoded_payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        return decoded_payload
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None
