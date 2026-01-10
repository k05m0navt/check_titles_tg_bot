"""Settings repository interface."""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any


class ISettingsRepository(ABC):
    """Abstract interface for settings repository."""

    @abstractmethod
    async def get(self, key: str) -> Optional[str]:
        """Get setting value by key."""
        pass

    @abstractmethod
    async def set(self, key: str, value: str, description: Optional[str] = None) -> None:
        """Set setting value."""
        pass

    @abstractmethod
    async def get_global_average_period(self) -> int:
        """Get global average period in days (0 = all-time)."""
        pass

    @abstractmethod
    async def set_global_average_period(self, period_days: int) -> None:
        """Set global average period in days (0 = all-time)."""
        pass

    @abstractmethod
    async def get_all(self) -> Dict[str, str]:
        """Get all settings as dictionary."""
        pass

    @abstractmethod
    async def get_default_title(self) -> str:
        """Get default title from bot_settings (key: 'default_title'). Returns empty string if not set."""
        pass

    @abstractmethod
    async def set_default_title(self, title: str) -> None:
        """Set default title in bot_settings (key: 'default_title'). Validates title before setting."""
        pass
