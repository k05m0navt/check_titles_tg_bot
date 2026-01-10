"""Get leaderboard use case."""

from typing import List, Optional
from dataclasses import dataclass

from ...domain.repositories.user_repository import IUserRepository


@dataclass
class LeaderboardEntry:
    """Leaderboard entry with user info and position."""

    position: int
    telegram_user_id: int
    telegram_username: Optional[str]
    display_name: Optional[str]
    title: str
    title_letter_count: int


class GetLeaderboardUseCase:
    """Use case for getting leaderboard sorted by title letter count."""

    def __init__(self, user_repository: IUserRepository):
        """
        Initialize get leaderboard use case.
        
        Args:
            user_repository: User repository interface
        """
        self._user_repository = user_repository

    async def execute(
        self,
        limit: int = 10,
        offset: int = 0,
        sort_order: str = "asc",
    ) -> List[LeaderboardEntry]:
        """
        Execute get leaderboard use case.
        
        Args:
            limit: Maximum number of entries to return
            offset: Offset for pagination
            sort_order: Sort order ('asc' or 'desc')
            
        Returns:
            List of leaderboard entries with positions
        """
        # Get users sorted by title letter count
        users = await self._user_repository.find_by_title_letter_count_range(
            min_count=None,
            max_count=None,
            limit=limit,
            offset=offset,
            sort_order=sort_order,
        )

        # Convert to leaderboard entries with positions
        entries = []
        position = offset + 1
        for user in users:
            entries.append(
                LeaderboardEntry(
                    position=position,
                    telegram_user_id=user.telegram_user_id,
                    telegram_username=user.telegram_username,
                    display_name=user.display_name,
                    title=str(user.title),
                    title_letter_count=user.title_letter_count,
                )
            )
            position += 1

        return entries

    async def get_user_position(
        self, telegram_user_id: int, sort_order: str = "asc"
    ) -> Optional[int]:
        """
        Get user's position in leaderboard.
        
        Args:
            telegram_user_id: Telegram user ID
            sort_order: Sort order ('asc' or 'desc')
            
        Returns:
            User's position (1-based) or None if not found
        """
        # Get user
        user = await self._user_repository.get_by_telegram_id(telegram_user_id)
        if not user:
            return None

        # Count users with better (lower or higher) letter count
        if sort_order == "asc":
            # Position = count of users with fewer letters + 1
            better_users = await self._user_repository.find_by_title_letter_count_range(
                max_count=user.title_letter_count - 1,
                limit=None,
                offset=0,
                sort_order="asc",
            )
        else:
            # Position = count of users with more letters + 1
            better_users = await self._user_repository.find_by_title_letter_count_range(
                min_count=user.title_letter_count + 1,
                limit=None,
                offset=0,
                sort_order="desc",
            )

        return len(better_users) + 1
