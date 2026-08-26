from typing import List
from fastapi import Depends
from app.domain.entities.user import User
from app.core.exceptions import AuthorizationException
from app.presentation.api.v1.auth import get_current_user


class RoleChecker:
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in self.allowed_roles:
            raise AuthorizationException(
                message=f"Role '{current_user.role}' is not authorized to access this resource. Required: {self.allowed_roles}"
            )
        return current_user
