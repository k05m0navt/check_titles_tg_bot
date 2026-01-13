"""Set full title for all users use case - admin command to set base title for all users."""

from typing import Optional
from ...domain.value_objects.title import Title
from ...domain.repositories.user_repository import IUserRepository
from ...domain.repositories.title_history_repository import ITitleHistoryRepository
from ...domain.services.title_calculation_service import TitleCalculationService
from ...application.services.admin_service import AdminService


class SetFullTitleForAllUseCase:
    """Use case for setting full/base title for all users (admin only)."""

    def __init__(
        self,
        user_repository: IUserRepository,
        title_history_repository: ITitleHistoryRepository,
        title_calculation_service: TitleCalculationService,
    ):
        """
        Initialize set full title for all users use case.
        
        Args:
            user_repository: User repository interface
            title_history_repository: Title history repository interface
            title_calculation_service: Title calculation service (for recalculating displayed titles)
        """
        self._user_repository = user_repository
        self._title_history_repository = title_history_repository
        self._title_calculation_service = title_calculation_service

    async def execute(
        self,
        full_title: str,
        admin_telegram_user_id: Optional[int] = None,
        admin_username: Optional[str] = None,
    ) -> int:
        """
        Execute set full title for all users use case.
        
        Args:
            full_title: Full/base title string to set for all users (e.g., "Super Gay Title")
            admin_telegram_user_id: Telegram user ID of admin (for validation)
            admin_username: Telegram username of admin (for validation, fallback)
            
        Returns:
            Number of users updated
            
        Raises:
            PermissionError: If user is not admin
        """
        # Validate admin access
        if not AdminService.is_admin(admin_telegram_user_id, admin_username):
            raise PermissionError("Admin access required to set full title for all users")

        # Create Title value object from string
        full_title_vo = Title(full_title)

        # Get all users
        users = await self._user_repository.find_all(limit=None, offset=0)
        
        updated_count = 0
        
        # Update each user
        for user in users:
            # Save old full_title for history
            old_full_title_str = str(user.full_title)

            # Set full_title
            user.set_full_title(full_title_vo)

            # Recalculate displayed title if user has a last_percentage
            if user.last_percentage:
                from ...domain.value_objects.percentage import Percentage
                displayed_title = await self._title_calculation_service.calculate_displayed_title(
                    full_title_vo, user.last_percentage, user.title
                )
                user.update_title(displayed_title)
            else:
                # If no last_percentage, preserve current title (will be calculated on next message)
                # Don't set to empty to avoid losing the current title
                pass

            # Save user
            saved_user = await self._user_repository.save(user)
            
            if not saved_user.id:
                continue  # Skip if ID not set (shouldn't happen, but safe guard)
            
            # Create title history entry for full_title change
            await self._title_history_repository.save(
                user_id=saved_user.id,
                old_title=old_full_title_str if old_full_title_str else None,
                new_title=str(full_title_vo),
                percentage=None,  # Full title change is not triggered by percentage
                change_type="manual_admin",
            )
            
            updated_count += 1
        
        return updated_count
