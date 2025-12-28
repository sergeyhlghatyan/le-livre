"""Authentication service for password hashing and JWT token management."""
from datetime import datetime, timedelta
from typing import Optional
from passlib.context import CryptContext
from jose import JWTError, jwt
from ..config import get_settings

settings = get_settings()

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.

    Args:
        plain_password: The plain text password to verify
        hashed_password: The bcrypt hashed password

    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: The plain text password to hash

    Returns:
        The bcrypt hashed password
    """
    return pwd_context.hash(password)


def create_access_token(data: dict) -> str:
    """
    Create a JWT access token.

    Args:
        data: Dictionary containing token claims (must include 'sub' and 'user_id')

    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.jwt_access_token_expire_minutes)
    to_encode.update({"exp": expire, "type": "access"})

    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """
    Create a JWT refresh token.

    Args:
        data: Dictionary containing token claims (must include 'sub' and 'user_id')

    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.jwt_refresh_token_expire_days)
    to_encode.update({"exp": expire, "type": "refresh"})

    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )
    return encoded_jwt


def verify_token(token: str, expected_type: str = "access") -> dict:
    """
    Verify and decode a JWT token.

    Args:
        token: The JWT token to verify
        expected_type: Expected token type ('access' or 'refresh')

    Returns:
        Decoded token payload

    Raises:
        JWTError: If token is invalid or expired
        ValueError: If token type doesn't match expected type
    """
    payload = jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm]
    )

    token_type = payload.get("type")
    if token_type != expected_type:
        raise ValueError(f"Invalid token type: expected {expected_type}, got {token_type}")

    return payload


def get_user_by_email(email: str, conn) -> Optional[dict]:
    """
    Get user by email from database.

    Args:
        email: User's email address
        conn: Database connection

    Returns:
        User dict or None if not found
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, email, hashed_password, is_active, is_superuser, created_at
            FROM users
            WHERE email = %s
            """,
            (email,)
        )
        row = cur.fetchone()

        if not row:
            return None

        return {
            "id": row[0],
            "email": row[1],
            "hashed_password": row[2],
            "is_active": row[3],
            "is_superuser": row[4],
            "created_at": row[5]
        }


def get_user_by_id(user_id: int, conn) -> Optional[dict]:
    """
    Get user by ID from database.

    Args:
        user_id: User's ID
        conn: Database connection

    Returns:
        User dict (without hashed_password) or None if not found
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, email, is_active, is_superuser, created_at
            FROM users
            WHERE id = %s
            """,
            (user_id,)
        )
        row = cur.fetchone()

        if not row:
            return None

        return {
            "id": row[0],
            "email": row[1],
            "is_active": row[2],
            "is_superuser": row[3],
            "created_at": row[4]
        }


def authenticate_user(email: str, password: str, conn) -> Optional[dict]:
    """
    Authenticate a user by email and password.

    Args:
        email: User's email address
        password: Plain text password
        conn: Database connection

    Returns:
        User dict (without hashed_password) if authentication succeeds, None otherwise
    """
    user = get_user_by_email(email, conn)

    if not user:
        return None

    if not verify_password(password, user["hashed_password"]):
        return None

    # Remove hashed_password from return value
    user_without_password = {
        "id": user["id"],
        "email": user["email"],
        "is_active": user["is_active"],
        "is_superuser": user["is_superuser"],
        "created_at": user["created_at"]
    }

    return user_without_password


def create_user(email: str, password: str, is_superuser: bool, conn) -> dict:
    """
    Create a new user in the database.

    Args:
        email: User's email address
        password: Plain text password (will be hashed)
        is_superuser: Whether user is a superuser
        conn: Database connection

    Returns:
        Created user dict (without hashed_password)

    Raises:
        Exception: If user with email already exists
    """
    hashed_password = get_password_hash(password)

    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO users (email, hashed_password, is_active, is_superuser)
            VALUES (%s, %s, %s, %s)
            RETURNING id, email, is_active, is_superuser, created_at
            """,
            (email, hashed_password, True, is_superuser)
        )
        row = cur.fetchone()
        conn.commit()

        return {
            "id": row[0],
            "email": row[1],
            "is_active": row[2],
            "is_superuser": row[3],
            "created_at": row[4]
        }
