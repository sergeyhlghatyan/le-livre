"""FastAPI dependency injection for authentication."""
from fastapi import Depends, HTTPException, Cookie
from typing import Optional
from .services.auth import verify_token, get_user_by_id
from .database import get_postgres_conn


async def get_current_user(access_token: Optional[str] = Cookie(None)) -> dict:
    """
    Get current authenticated user from access token cookie.

    Args:
        access_token: JWT access token from httpOnly cookie

    Returns:
        User dict with id, email, is_active, is_superuser

    Raises:
        HTTPException(401): If not authenticated or token invalid
    """
    if not access_token:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"}
        )

    try:
        payload = verify_token(access_token, "access")
        user_id = payload.get("user_id")

        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token payload")

        with get_postgres_conn() as conn:
            user = get_user_by_id(user_id, conn)

            if not user:
                raise HTTPException(status_code=401, detail="User not found")

            if not user["is_active"]:
                raise HTTPException(status_code=401, detail="Inactive user")

            return user

    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=401, detail="Could not validate credentials")


async def get_current_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """
    Require current user to be a superuser (admin).

    Args:
        current_user: Current authenticated user from get_current_user dependency

    Returns:
        User dict (only if is_superuser is True)

    Raises:
        HTTPException(403): If user is not a superuser
    """
    if not current_user.get("is_superuser"):
        raise HTTPException(
            status_code=403,
            detail="Not authorized. Superuser access required."
        )

    return current_user


async def get_optional_user(access_token: Optional[str] = Cookie(None)) -> Optional[dict]:
    """
    Get current user if authenticated, None otherwise.

    Useful for endpoints that work with or without authentication.

    Args:
        access_token: JWT access token from httpOnly cookie

    Returns:
        User dict if authenticated, None otherwise
    """
    if not access_token:
        return None

    try:
        payload = verify_token(access_token, "access")
        user_id = payload.get("user_id")

        if user_id is None:
            return None

        with get_postgres_conn() as conn:
            user = get_user_by_id(user_id, conn)

            if not user or not user["is_active"]:
                return None

            return user

    except:
        return None
