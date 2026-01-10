"""Daily snapshot job for statistics."""

import asyncio
from datetime import date, timedelta
from typing import List
import structlog

from ...domain.repositories.user_repository import IUserRepository
from ...domain.repositories.statistics_repository import IStatisticsRepository

logger = structlog.get_logger(__name__)


class DailySnapshotJob:
    """Job for creating daily snapshots."""

    def __init__(
        self,
        user_repository: IUserRepository,
        statistics_repository: IStatisticsRepository,
    ):
        """Initialize daily snapshot job."""
        self._user_repository = user_repository
        self._statistics_repository = statistics_repository

    async def create_daily_snapshots(self, snapshot_date: date) -> int:
        """
        Create daily snapshots for all users with activity on given date.
        
        Args:
            snapshot_date: Date to create snapshots for
            
        Returns:
            Number of snapshots created
        """
        logger.info("Starting daily snapshot job", snapshot_date=snapshot_date.isoformat())

        # Get all users (would need to filter by last_processed_date = snapshot_date)
        # For now, get all users and check their last_processed_date
        all_users = await self._user_repository.find_all(limit=10000)

        created_count = 0
        for user in all_users:
            if user.last_processed_date == snapshot_date:
                # Create snapshot for this user
                try:
                    await self._statistics_repository.create_daily_snapshot(
                        user_id=user.id or 0,
                        snapshot_date=snapshot_date,
                        percentage=int(user.last_percentage) if user.last_percentage else None,
                        title=str(user.title),
                        title_letter_count=user.title_letter_count,
                    )
                    created_count += 1
                except Exception as e:
                    logger.error(
                        "Error creating snapshot for user",
                        user_id=user.id,
                        error=str(e),
                        exc_info=True
                    )

        logger.info("Daily snapshot job complete", created_count=created_count)
        return created_count

    async def check_missed_days(self, days_back: int = 7) -> None:
        """Check for missed snapshots and backfill."""
        logger.info("Checking for missed snapshots", days_back=days_back)
        
        today = date.today()
        for i in range(days_back):
            check_date = today - timedelta(days=i)
            await self.create_daily_snapshots(check_date)
