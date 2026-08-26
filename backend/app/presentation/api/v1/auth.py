import secrets
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import (
    verify_password, 
    get_password_hash, 
    create_access_token, 
    create_refresh_token, 
    decode_access_token
)
from app.core.exceptions import AuthenticationException, EntityAlreadyExistsException, EntityNotFoundException
from app.core.logging import logger
from app.data.repositories.sqlalchemy_user_repository import SQLAlchemyUserRepository
from app.data.repositories.sqlalchemy_refresh_token_repository import SQLAlchemyRefreshTokenRepository
from app.domain.entities.user import User
from app.presentation.schemas.auth_schemas import (
    UserCreate, 
    UserLogin, 
    TokenResponse, 
    UserOut, 
    VerifyEmailRequest, 
    ForgotPasswordRequest, 
    ResetPasswordRequest, 
    RefreshTokenRequest,
    UserProfileUpdate,
    ChangePasswordRequest,
    ResendVerificationRequest
)

router = APIRouter(prefix="/auth", tags=["authentication"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Dependency to validate JWT token and return current User entity."""
    payload = decode_access_token(token)
    if not payload:
        raise AuthenticationException("Could not validate credentials or token expired")
    
    email: str = payload.get("sub")
    if email is None:
        raise AuthenticationException("Invalid token payload")
        
    repo = SQLAlchemyUserRepository(db)
    user = repo.get_by_email(email)
    if user is None:
        raise AuthenticationException("User not found")
    return user


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Registers a new system user with Role selection and triggers email verification."""
    repo = SQLAlchemyUserRepository(db)
    existing_user = repo.get_by_email(user_data.email)
    if existing_user:
        raise EntityAlreadyExistsException("User", user_data.email)
    
    hashed_pwd = get_password_hash(user_data.password)
    verification_token = secrets.token_hex(32)
    
    new_user = User(
        id=None,
        email=user_data.email,
        hashed_password=hashed_pwd,
        full_name=user_data.full_name,
        is_active=True,
        role=user_data.role,
        is_verified=False,
        verification_token=verification_token,
        reset_token=None,
        reset_token_expires=None,
        created_at=None,
        updated_at=None
    )
    
    created_user = repo.create(new_user)
    
    # Simulate sending verification email
    verify_link = f"http://localhost:3000/verify-email?token={verification_token}"
    logger.info(f"--- SIMULATED VERIFICATION EMAIL SENT TO {user_data.email} ---")
    logger.info(f"Verification link: {verify_link}")
    logger.info("-------------------------------------------------------------")
    
    return created_user


@router.post("/verify-email")
def verify_email(payload: VerifyEmailRequest, db: Session = Depends(get_db)):
    """Verifies a user's account using the token from their verification link."""
    repo = SQLAlchemyUserRepository(db)
    user = repo.get_by_verification_token(payload.token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )
    
    user.is_verified = True
    user.verification_token = None
    repo.update(user)
    
    logger.info(f"User {user.email} successfully verified their email.")
    return {"success": True, "message": "Email verified successfully."}


@router.post("/login", response_model=TokenResponse)
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    """Logs in an existing user and returns JWT access and refresh tokens."""
    user_repo = SQLAlchemyUserRepository(db)
    token_repo = SQLAlchemyRefreshTokenRepository(db)
    
    user = user_repo.get_by_email(login_data.email)
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise AuthenticationException("Incorrect email or password")
        
    access_token = create_access_token(subject=user.email)
    refresh_token = create_refresh_token(subject=user.email)
    
    # Store refresh token with 7-day expiration
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    token_repo.save_token(token=refresh_token, user_id=user.id, expires_at=expires_at)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(payload: RefreshTokenRequest, db: Session = Depends(get_db)):
    """Refreshes the access token using a valid, non-revoked refresh token."""
    token_repo = SQLAlchemyRefreshTokenRepository(db)
    user_repo = SQLAlchemyUserRepository(db)
    
    # Decode token claims
    claims = decode_access_token(payload.refresh_token)
    if not claims or claims.get("type") != "refresh":
        raise AuthenticationException("Invalid refresh token")
        
    # Check database to see if token is valid and not revoked
    token_db = token_repo.get_token(payload.refresh_token)
    if not token_db or token_db["is_revoked"] or token_db["expires_at"].replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise AuthenticationException("Refresh token is expired or has been revoked")
        
    email = claims.get("sub")
    user = user_repo.get_by_email(email)
    if not user:
        raise AuthenticationException("User associated with token not found")
        
    # Generate new tokens
    new_access_token = create_access_token(subject=user.email)
    new_refresh_token = create_refresh_token(subject=user.email)
    
    # Revoke old refresh token and save the new one
    token_repo.revoke_token(payload.refresh_token)
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    token_repo.save_token(token=new_refresh_token, user_id=user.id, expires_at=expires_at)
    
    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }


@router.post("/forgot-password")
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """Triggers password reset flow, generating a reset token."""
    repo = SQLAlchemyUserRepository(db)
    user = repo.get_by_email(payload.email)
    
    # We return success even if user not found to prevent user enumeration
    if user:
        reset_token = secrets.token_hex(32)
        user.reset_token = reset_token
        user.reset_token_expires = datetime.now(timezone.utc) + timedelta(minutes=15)
        repo.update(user)
        
        # Simulate sending email
        reset_link = f"http://localhost:3000/reset-password?token={reset_token}"
        logger.info(f"--- SIMULATED RESET PASSWORD EMAIL SENT TO {user.email} ---")
        logger.info(f"Reset link: {reset_link}")
        logger.info("-------------------------------------------------------------")
        
    return {"success": True, "message": "If this email is registered, a password reset link has been dispatched."}


@router.post("/reset-password")
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Validates the reset token and updates the user's password."""
    repo = SQLAlchemyUserRepository(db)
    user = repo.get_by_reset_token(payload.token)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
        
    # Check expiry
    expires = user.reset_token_expires.replace(tzinfo=timezone.utc)
    if expires < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has expired"
        )
        
    # Update password
    user.hashed_password = get_password_hash(payload.new_password)
    user.reset_token = None
    user.reset_token_expires = None
    repo.update(user)
    
    logger.info(f"Password reset successful for user {user.email}")
    return {"success": True, "message": "Password reset successfully."}


@router.post("/logout")
def logout(payload: RefreshTokenRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Revokes refresh tokens to securely log out a user session."""
    token_repo = SQLAlchemyRefreshTokenRepository(db)
    token_repo.revoke_token(payload.refresh_token)
    logger.info(f"User {current_user.email} logged out successfully (token revoked).")
    return {"success": True, "message": "Logged out successfully."}


@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    """Returns profile details of the logged-in user."""
    return current_user


@router.put("/profile", response_model=UserOut)
def update_profile(
    payload: UserProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Allows user to update full profile parameters."""
    repo = SQLAlchemyUserRepository(db)
    
    if payload.full_name is not None:
        current_user.full_name = payload.full_name
    if payload.phone_number is not None:
        current_user.phone_number = payload.phone_number
    if payload.profile_photo is not None:
        current_user.profile_photo = payload.profile_photo
    if payload.language is not None:
        current_user.language = payload.language
    if payload.timezone is not None:
        current_user.timezone = payload.timezone
    if payload.notification_preferences is not None:
        current_user.notification_preferences = payload.notification_preferences

    return repo.update(current_user)


@router.post("/change-password")
def change_password(
    payload: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Verifies old password and registers a hashed new password."""
    repo = SQLAlchemyUserRepository(db)
    if not verify_password(payload.old_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect existing password"
        )
        
    current_user.hashed_password = get_password_hash(payload.new_password)
    repo.update(current_user)
    logger.info(f"User {current_user.email} successfully updated their password.")
    return {"success": True, "message": "Password updated successfully."}


@router.post("/resend-verification")
def resend_verification(
    payload: ResendVerificationRequest,
    db: Session = Depends(get_db)
):
    """Generates a new verification link for the user email."""
    repo = SQLAlchemyUserRepository(db)
    user = repo.get_by_email(payload.email)
    
    if user and not user.is_verified:
        new_token = secrets.token_hex(32)
        user.verification_token = new_token
        repo.update(user)
        
        # Simulate verification link dispatch
        verify_link = f"http://localhost:3000/verify-email?token={new_token}"
        logger.info(f"--- SIMULATED VERIFICATION EMAIL RESENT TO {user.email} ---")
        logger.info(f"Verification link: {verify_link}")
        logger.info("-------------------------------------------------------------")
        
    return {"success": True, "message": "If the email is unverified, a new link has been dispatched."}


@router.get("/sessions")
def get_active_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Returns active session tokens linked to the user."""
    from app.data.models.refresh_token_model import RefreshTokenModel
    
    tokens = db.query(RefreshTokenModel).filter(
        RefreshTokenModel.user_id == current_user.id,
        RefreshTokenModel.is_revoked == False,
        RefreshTokenModel.expires_at > datetime.utcnow()
    ).all()
    
    return [
        {
            "id": t.id,
            "expires_at": t.expires_at,
            "created_at": t.created_at,
            "is_current": True  # Simplification for demo tracking
        }
        for t in tokens
    ]


@router.delete("/session/{id}")
def terminate_session(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Revokes a specific session token."""
    from app.data.models.refresh_token_model import RefreshTokenModel
    
    token = db.query(RefreshTokenModel).filter(
        RefreshTokenModel.id == id,
        RefreshTokenModel.user_id == current_user.id
    ).first()
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
        
    token.is_revoked = True
    db.commit()
    return {"success": True, "message": "Session terminated."}


@router.get("/devices")
def get_active_devices(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Returns active devices matched to active user refresh tokens."""
    sessions = get_active_sessions(db, current_user)
    return [
        {
            "id": s["id"],
            "device_name": "Web Browser (Chrome/Firefox)",
            "last_active": s["created_at"],
            "is_current": s["is_current"]
        }
        for s in sessions
    ]


@router.delete("/device/{id}")
def terminate_device(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Revokes the refresh token matching the device ID."""
    return terminate_session(id, db, current_user)
