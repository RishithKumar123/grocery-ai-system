from typing import Optional
from sqlalchemy.orm import Session
from app.domain.entities.user import User
from app.domain.interfaces.user_repository import UserRepositoryInterface
from app.data.models.user_model import UserModel


class SQLAlchemyUserRepository(UserRepositoryInterface):
    def __init__(self, db: Session):
        self.db = db

    def _to_entity(self, model: UserModel) -> User:
        return User(
            id=model.id,
            email=model.email,
            hashed_password=model.hashed_password,
            full_name=model.full_name,
            is_active=model.is_active,
            role=model.role,
            is_verified=model.is_verified,
            verification_token=model.verification_token,
            reset_token=model.reset_token,
            reset_token_expires=model.reset_token_expires,
            phone_number=model.phone_number,
            profile_photo=model.profile_photo,
            language=model.language,
            timezone=model.timezone,
            notification_preferences=model.notification_preferences,
            status=model.status,
            created_at=model.created_at,
            updated_at=model.updated_at
        )

    def get_by_id(self, user_id: int) -> Optional[User]:
        model = self.db.query(UserModel).filter(UserModel.id == user_id).first()
        return self._to_entity(model) if model else None

    def get_by_email(self, email: str) -> Optional[User]:
        model = self.db.query(UserModel).filter(UserModel.email == email).first()
        return self._to_entity(model) if model else None

    def create(self, user: User) -> User:
        model = UserModel(
            email=user.email,
            hashed_password=user.hashed_password,
            full_name=user.full_name,
            is_active=user.is_active,
            role=user.role,
            is_verified=user.is_verified,
            verification_token=user.verification_token,
            reset_token=user.reset_token,
            reset_token_expires=user.reset_token_expires,
            phone_number=user.phone_number,
            profile_photo=user.profile_photo,
            language=user.language,
            timezone=user.timezone,
            notification_preferences=user.notification_preferences,
            status=user.status
        )
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._to_entity(model)

    def update(self, user: User) -> User:
        model = self.db.query(UserModel).filter(UserModel.id == user.id).first()
        if not model:
            raise ValueError(f"User with id {user.id} not found for updates.")
        
        model.email = user.email
        model.full_name = user.full_name
        model.hashed_password = user.hashed_password
        model.is_active = user.is_active
        model.role = user.role
        model.is_verified = user.is_verified
        model.verification_token = user.verification_token
        model.reset_token = user.reset_token
        model.reset_token_expires = user.reset_token_expires
        
        # Profile updates mapping
        model.phone_number = user.phone_number
        model.profile_photo = user.profile_photo
        model.language = user.language
        model.timezone = user.timezone
        model.notification_preferences = user.notification_preferences
        model.status = user.status
        
        self.db.commit()
        self.db.refresh(model)
        return self._to_entity(model)

    def get_by_verification_token(self, token: str) -> Optional[User]:
        model = self.db.query(UserModel).filter(UserModel.verification_token == token).first()
        return self._to_entity(model) if model else None

    def get_by_reset_token(self, token: str) -> Optional[User]:
        model = self.db.query(UserModel).filter(UserModel.reset_token == token).first()
        return self._to_entity(model) if model else None
