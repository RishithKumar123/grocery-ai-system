from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional


class RefreshTokenRepositoryInterface(ABC):
    @abstractmethod
    def save_token(self, token: str, user_id: int, expires_at: datetime) -> None:
        """Save a new refresh token to the database."""
        pass

    @abstractmethod
    def get_token(self, token: str) -> Optional[dict]:
        """Retrieve a refresh token by string."""
        pass

    @abstractmethod
    def revoke_token(self, token: str) -> None:
        """Revoke a single refresh token."""
        pass

    @abstractmethod
    def revoke_all_user_tokens(self, user_id: int) -> None:
        """Revoke all active refresh tokens for a user."""
        pass
