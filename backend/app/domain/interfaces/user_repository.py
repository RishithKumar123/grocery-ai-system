from abc import ABC, abstractmethod
from typing import Optional
from app.domain.entities.user import User


class UserRepositoryInterface(ABC):
    @abstractmethod
    def get_by_id(self, user_id: int) -> Optional[User]:
        pass

    @abstractmethod
    def get_by_email(self, email: str) -> Optional[User]:
        pass

    @abstractmethod
    def create(self, user: User) -> User:
        pass

    @abstractmethod
    def update(self, user: User) -> User:
        pass

    @abstractmethod
    def get_by_verification_token(self, token: str) -> Optional[User]:
        pass

    @abstractmethod
    def get_by_reset_token(self, token: str) -> Optional[User]:
        pass
