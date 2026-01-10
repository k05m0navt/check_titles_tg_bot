"""Set global average period use case (admin only)."""

from typing import Optional

from ...domain.repositories.settings_repository import ISettingsRepository
from ...application.services.admin_service import AdminService


class SetGlobalAveragePeriodUseCase:
    """Use case for setting global average period (admin only)."""

    def __init__(
        self,
        settings_repository: ISettingsRepository,
        admin_service: AdminService,
    ):
        """
        Initialize set global average period use case.
        
        Args:
            settings_repository: Settings repository interface
            admin_service: Admin service for validation
        """
        self._settings_repository = settings_repository
        self._admin_service = admin_service

    async def execute(
        self,
        period_days: int,
        admin_telegram_user_id: int,
        admin_username: Optional[str] = None,
    ) -> None:
        """
        Execute set global average period use case.
        
        Args:
            period_days: Period in days (0 = all-time)
            admin_telegram_user_id: Telegram user ID of admin
            admin_username: Admin username (optional, for fallback validation)
            
        Raises:
            PermissionError: If user is not admin
            ValueError: If period_days is negative
        """
        # Validate admin access
        if not self._admin_service.is_admin(admin_telegram_user_id, admin_username):
            raise PermissionError("Admin access required")

        # Validate period
        if period_days < 0:
            raise ValueError("Period days must be non-negative")

        # Set global average period
        await self._settings_repository.set_global_average_period(period_days)
