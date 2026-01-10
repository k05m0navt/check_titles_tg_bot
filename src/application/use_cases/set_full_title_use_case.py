"""Set full title use case - admin command to set base title for user."""

from typing import Optional

from ...domain.entities.user import User
from ...domain.value_objects.title import Title
from ...domain.repositories.user_repository import IUserRepository
from ...domain.repositories.title_history_repository import ITitleHistoryRepository
from ...domain.services.title_calculation_service import TitleCalculationService
from ...domain.exceptions import UserNotFoundError
from ...application.services.admin_service import AdminService


class SetFullTitleUseCase:
    """Use case for setting full/base title for a user (admin only)."""

    def __init__(
        self,
        user_repository: IUserRepository,
        title_history_repository: ITitleHistoryRepository,
        title_calculation_service: TitleCalculationService,
    ):
        """
        Initialize set full title use case.
        
        Args:
            user_repository: User repository interface
            title_history_repository: Title history repository interface
            title_calculation_service: Title calculation service (for recalculating displayed title)
        """
        self._user_repository = user_repository
        self._title_history_repository = title_history_repository
        self._title_calculation_service = title_calculation_service

    async def execute(
        self,
        telegram_user_id: int,
        full_title: str,
        admin_telegram_user_id: Optional[int] = None,
        admin_username: Optional[str] = None,
    ) -> None:
        """
        Execute set full title use case.
        
        Args:
            telegram_user_id: Telegram user ID of the user whose full_title will be set
            full_title: Full/base title string to set (e.g., "Super Gay Title")
            admin_telegram_user_id: Telegram user ID of admin (for validation)
            admin_username: Telegram username of admin (for validation, fallback)
            
        Raises:
            UserNotFoundError: If user not found
            PermissionError: If user is not admin
        """
        # Validate admin access
        if not AdminService.is_admin(admin_telegram_user_id, admin_username):
            raise PermissionError("Admin access required to set full title")

        # Get user by Telegram user ID
        user = await self._user_repository.get_by_telegram_id(telegram_user_id)
        if not user:
            raise UserNotFoundError(f"User with Telegram ID {telegram_user_id} not found")

        # Create Title value object from string
        full_title_vo = Title(full_title)

        # Save old full_title for history
        old_full_title_str = str(user.full_title)

        # Set full_title
        user.set_full_title(full_title_vo)

        # Recalculate displayed title if user has a last_percentage
        # This ensures displayed title is updated based on current percentage
        if user.last_percentage:
            from ...domain.value_objects.percentage import Percentage
            displayed_title = await self._title_calculation_service.calculate_displayed_title(
                full_title_vo, user.last_percentage
            )
            user.update_title(displayed_title)
        else:
            # If no last_percentage, set displayed title to empty (will be calculated on next message)
            user.update_title(Title(""))

        # Save user
        await self._user_repository.save(user)

        # Get saved user to ensure ID is set
        saved_user = await self._user_repository.get_by_telegram_id(telegram_user_id)
        if not saved_user or not saved_user.id:
            raise ValueError("User ID not set after save")

        # Create title history entry for full_title change
        await self._title_history_repository.save(
            user_id=saved_user.id,
            old_title=old_full_title_str if old_full_title_str else None,
            new_title=str(full_title_vo),
            percentage=None,  # Full title change is not triggered by percentage
            change_type="manual_admin",
        )
