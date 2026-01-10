"""Calculate statistics use case."""

from typing import Optional
from datetime import datetime, timedelta

from ...domain.repositories.statistics_repository import IStatisticsRepository
from ...domain.repositories.settings_repository import ISettingsRepository


class CalculateStatisticsUseCase:
    """Use case for calculating global statistics."""

    def __init__(
        self,
        statistics_repository: IStatisticsRepository,
        settings_repository: ISettingsRepository,
    ):
        """
        Initialize calculate statistics use case.
        
        Args:
            statistics_repository: Statistics repository interface
            settings_repository: Settings repository interface
        """
        self._statistics_repository = statistics_repository
        self._settings_repository = settings_repository

    async def execute(
        self, period_days: Optional[int] = None
    ) -> Optional[float]:
        """
        Execute calculate statistics use case.
        
        Args:
            period_days: Period in days (None = use setting, 0 = all-time)
            
        Returns:
            Global average percentage or None if no data
        """
        # Get period from settings if not provided
        if period_days is None:
            period_days = await self._settings_repository.get_global_average_period()

        # Check cache first
        cache_key = "global_average"
        cached_value = await self._statistics_repository.get_cached_statistics(
            cache_key, period_days
        )

        if cached_value is not None:
            return cached_value

        # Calculate fresh value
        global_average = await self._statistics_repository.get_global_average(
            period_days
        )

        if global_average is not None:
            # Cache with expiration (+1 day from now)
            expires_at = datetime.now() + timedelta(days=1)
            await self._statistics_repository.cache_statistics(
                cache_key, period_days, global_average, expires_at
            )

        return global_average
