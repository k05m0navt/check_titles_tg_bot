"""Statistics repository interface."""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import date, datetime

from ..entities.user import User


class IDailySnapshot(ABC):
    """Daily snapshot data structure."""

    user_id: int
    snapshot_date: date
    percentage: Optional[int]
    title: str
    title_letter_count: int


class IStatisticsRepository(ABC):
    """Abstract interface for statistics repository."""

    @abstractmethod
    async def create_daily_snapshot(
        self, user_id: int, snapshot_date: date, percentage: Optional[int],
        title: str, title_letter_count: int
    ) -> None:
        """Create daily snapshot for user."""
        pass

    @abstractmethod
    async def get_snapshots_by_period(
        self, start_date: date, end_date: date, user_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get snapshots for period (optionally filtered by user)."""
        pass

    @abstractmethod
    async def get_global_average(
        self, period_days: int = 0
    ) -> Optional[float]:
        """Get global average percentage for period (0 = all-time)."""
        pass

    @abstractmethod
    async def cache_statistics(
        self, calculation_type: str, period_days: int, value: float,
        expires_at: datetime
    ) -> None:
        """Cache statistics calculation."""
        pass

    @abstractmethod
    async def get_cached_statistics(
        self, calculation_type: str, period_days: int
    ) -> Optional[float]:
        """Get cached statistics if valid."""
        pass

    @abstractmethod
    async def is_cache_valid(
        self, calculation_type: str, period_days: int
    ) -> bool:
        """Check if cache entry exists and is not expired."""
        pass

    @abstractmethod
    async def invalidate_cache(
        self, calculation_type: str, period_days: Optional[int] = None
    ) -> None:
        """Invalidate cache entries (delete expired or specific entries)."""
        pass
