"""Authentication router for login, register, and user management."""
from fastapi import APIRouter, HTTPException, Response, Depends, Cookie
from pydantic import BaseModel, EmailStr
from typing import Optional
from ..services.auth import (
    authenticate_user,
    create_user,
    create_access_token,
    create_refresh_token,
    verify_token
)
from ..database import get_postgres_conn
from ..dependencies import get_current_user, get_current_admin
from ..config import get_settings

settings = get_settings()
router = APIRouter(prefix="/auth", tags=["authentication"])


# Request/Response Models
class LoginRequest(BaseModel):
    """Login request with email and password."""
    email: EmailStr
    password: str


class CreateUserRequest(BaseModel):
    """Create user request (admin only)."""
    email: EmailStr
    password: str
    is_superuser: bool = False


class UserResponse(BaseModel):
    """User response model (without password)."""
    id: int
    email: str
    is_active: bool
    is_superuser: bool


class MessageResponse(BaseModel):
    """Simple message response."""
    message: str


# Helper function to set auth cookies
def set_auth_cookies(response: Response, user: dict):
    """Set access and refresh token cookies on response."""
    token_data = {
        "sub": user["email"],
        "user_id": user["id"]
    }

    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    # Access token cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=settings.environment == "production",
        samesite="lax",
        max_age=settings.jwt_access_token_expire_minutes * 60
    )

    # Refresh token cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.environment == "production",
        samesite="lax",
        max_age=settings.jwt_refresh_token_expire_days * 24 * 60 * 60
    )


# Routes
@router.post("/login", response_model=UserResponse)
async def login(request: LoginRequest, response: Response):
    """
    Login with email and password.

    Sets httpOnly cookies for access_token and refresh_token.
    Returns user information.
    """
    try:
        with get_postgres_conn() as conn:
            user = authenticate_user(request.email, request.password, conn)

            if not user:
                raise HTTPException(
                    status_code=401,
                    detail="Incorrect email or password"
                )

            # Set auth cookies
            set_auth_cookies(response, user)

            return UserResponse(**user)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/register", response_model=UserResponse)
async def register(
    request: CreateUserRequest,
    response: Response,
    current_user: dict = Depends(get_current_admin)
):
    """
    Register a new user (admin only).

    Requires authentication with superuser privileges.
    Sets httpOnly cookies for the new user.
    """
    try:
        with get_postgres_conn() as conn:
            user = create_user(
                email=request.email,
                password=request.password,
                is_superuser=request.is_superuser,
                conn=conn
            )

            return UserResponse(**user)

    except Exception as e:
        # Handle unique constraint violation
        if "unique" in str(e).lower():
            raise HTTPException(
                status_code=400,
                detail="User with this email already exists"
            )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/refresh", response_model=MessageResponse)
async def refresh(
    response: Response,
    refresh_token: Optional[str] = Cookie(None)
):
    """
    Refresh access token using refresh token.

    Reads refresh_token from cookie, validates it,
    and issues a new access_token.
    """
    if not refresh_token:
        raise HTTPException(
            status_code=401,
            detail="Refresh token not found"
        )

    try:
        payload = verify_token(refresh_token, "refresh")
        user_id = payload.get("user_id")
        email = payload.get("sub")

        if not user_id or not email:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        # Create new access token
        token_data = {
            "sub": email,
            "user_id": user_id
        }
        access_token = create_access_token(token_data)

        # Set new access token cookie
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=settings.environment == "production",
            samesite="lax",
            max_age=settings.jwt_access_token_expire_minutes * 60
        )

        return MessageResponse(message="Token refreshed successfully")

    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=401, detail="Could not refresh token")


@router.post("/logout", response_model=MessageResponse)
async def logout(response: Response):
    """
    Logout by clearing auth cookies.
    """
    response.delete_cookie(key="access_token")
    response.delete_cookie(key="refresh_token")

    return MessageResponse(message="Logged out successfully")


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    """
    Get current authenticated user information.

    Requires valid access_token in cookie.
    """
    return UserResponse(**current_user)
