"""Title history repository interface."""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime


class ITitleHistoryRepository(ABC):
    """Abstract interface for title history repository."""

    @abstractmethod
    async def save(
        self, user_id: int, old_title: Optional[str], new_title: str,
        percentage: Optional[int], change_type: str
    ) -> None:
        """
        Save title history entry.
        
        Args:
            user_id: User ID
            old_title: Previous title (None for initial creation)
            new_title: New title
            percentage: Percentage that triggered change (if applicable)
            change_type: Type of change ('created', 'automatic', 'manual_admin')
        """
        pass

    @abstractmethod
    async def get_by_user(
        self, user_id: int, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get title history for user (most recent first)."""
        pass

    @abstractmethod
    async def get_recent(
        self, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get recent title changes across all users."""
        pass
