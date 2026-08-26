from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from app.domain.interfaces.refresh_token_repository import RefreshTokenRepositoryInterface
from app.data.models.refresh_token_model import RefreshTokenModel


class SQLAlchemyRefreshTokenRepository(RefreshTokenRepositoryInterface):
    def __init__(self, db: Session):
        self.db = db

    def save_token(self, token: str, user_id: int, expires_at: datetime) -> None:
        model = RefreshTokenModel(
            token=token,
            user_id=user_id,
            expires_at=expires_at,
            is_revoked=False
        )
        self.db.add(model)
        self.db.commit()

    def get_token(self, token: str) -> Optional[dict]:
        model = self.db.query(RefreshTokenModel).filter(RefreshTokenModel.token == token).first()
        if not model:
            return None
        return {
            "id": model.id,
            "token": model.token,
            "user_id": model.user_id,
            "expires_at": model.expires_at,
            "is_revoked": model.is_revoked,
            "created_at": model.created_at
        }

    def revoke_token(self, token: str) -> None:
        model = self.db.query(RefreshTokenModel).filter(RefreshTokenModel.token == token).first()
        if model:
            model.is_revoked = True
            self.db.commit()

    def revoke_all_user_tokens(self, user_id: int) -> None:
        models = self.db.query(RefreshTokenModel).filter(
            RefreshTokenModel.user_id == user_id,
            RefreshTokenModel.is_revoked == False
        ).all()
        for model in models:
            model.is_revoked = True
        self.db.commit()
