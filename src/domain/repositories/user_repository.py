"""User repository interface."""

from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import date

from ..entities.user import User


class IUserRepository(ABC):
    """Abstract interface for user repository."""

    @abstractmethod
    async def get_by_telegram_id(self, telegram_user_id: int) -> Optional[User]:
        """Get user by Telegram user ID."""
        pass

    @abstractmethod
    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by Telegram username."""
        pass

    @abstractmethod
    async def save(self, user: User) -> User:
        """Save or update user."""
        pass

    @abstractmethod
    async def find_all(self, limit: Optional[int] = None, offset: int = 0) -> List[User]:
        """Find all users with pagination."""
        pass

    @abstractmethod
    async def find_by_title_letter_count_range(
        self, min_count: Optional[int] = None, max_count: Optional[int] = None,
        limit: Optional[int] = None, offset: int = 0, sort_order: str = "asc"
    ) -> List[User]:
        """Find users by title letter count range with sorting."""
        pass

    @abstractmethod
    async def count_active_users(self) -> int:
        """Count active users (all users in database)."""
        pass

    @abstractmethod
    async def delete(self, telegram_user_id: int) -> bool:
        """
        Delete user by Telegram user ID.
        
        Args:
            telegram_user_id: Telegram user ID of user to delete
            
        Returns:
            True if user was deleted, False if user not found
        """
        pass
