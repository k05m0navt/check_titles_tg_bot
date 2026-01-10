"""Get user stats use case."""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import date, timedelta

from ...domain.repositories.user_repository import IUserRepository
from ...domain.repositories.statistics_repository import IStatisticsRepository
from ...domain.repositories.title_history_repository import ITitleHistoryRepository
from ...domain.entities.user import User
from ..use_cases.get_leaderboard_use_case import GetLeaderboardUseCase


@dataclass
class UserStats:
    """User statistics data structure."""

    telegram_user_id: int
    telegram_username: Optional[str]
    display_name: Optional[str]
    title: str
    title_letter_count: int
    current_percentage: Optional[int]
    position_in_leaderboard: Optional[int]
    recent_title_changes: List[Dict[str, Any]]
    daily_trend: Optional[float]  # Average percentage for last day
    weekly_trend: Optional[float]  # Average percentage for last 7 days
    monthly_trend: Optional[float]  # Average percentage for last 30 days


class GetUserStatsUseCase:
    """Use case for getting user statistics."""

    def __init__(
        self,
        user_repository: IUserRepository,
        statistics_repository: IStatisticsRepository,
        title_history_repository: ITitleHistoryRepository,
        get_leaderboard_use_case: GetLeaderboardUseCase,
    ):
        """
        Initialize get user stats use case.
        
        Args:
            user_repository: User repository interface
            statistics_repository: Statistics repository interface
            title_history_repository: Title history repository interface
            get_leaderboard_use_case: Get leaderboard use case for position
        """
        self._user_repository = user_repository
        self._statistics_repository = statistics_repository
        self._title_history_repository = title_history_repository
        self._get_leaderboard_use_case = get_leaderboard_use_case

    async def execute(self, telegram_user_id: int) -> Optional[UserStats]:
        """
        Execute get user stats use case.
        
        Args:
            telegram_user_id: Telegram user ID
            
        Returns:
            UserStats object or None if user not found
        """
        # Get user
        user = await self._user_repository.get_by_telegram_id(telegram_user_id)
        if not user:
            return None

        # Get position in leaderboard
        position = await self._get_leaderboard_use_case.get_user_position(
            telegram_user_id, sort_order="asc"
        )

        # Get recent title changes (last 5)
        recent_changes = await self._title_history_repository.get_by_user(
            user.id or 0, limit=5
        )

        # Calculate trends from daily snapshots
        today = date.today()
        daily_trend = await self._calculate_trend(user.id or 0, today, today)
        weekly_trend = await self._calculate_trend(
            user.id or 0, today - timedelta(days=7), today
        )
        monthly_trend = await self._calculate_trend(
            user.id or 0, today - timedelta(days=30), today
        )

        return UserStats(
            telegram_user_id=user.telegram_user_id,
            telegram_username=user.telegram_username,
            display_name=user.display_name,
            title=str(user.title),
            title_letter_count=user.title_letter_count,
            current_percentage=int(user.last_percentage) if user.last_percentage else None,
            position_in_leaderboard=position,
            recent_title_changes=recent_changes,
            daily_trend=daily_trend,
            weekly_trend=weekly_trend,
            monthly_trend=monthly_trend,
        )

    async def _calculate_trend(
        self, user_id: int, start_date: date, end_date: date
    ) -> Optional[float]:
        """Calculate average percentage trend for period."""
        snapshots = await self._statistics_repository.get_snapshots_by_period(
            start_date, end_date, user_id=user_id
        )

        if not snapshots:
            return None

        percentages = [
            s["percentage"] for s in snapshots if s.get("percentage") is not None
        ]

        if not percentages:
            return None

        return sum(percentages) / len(percentages)
