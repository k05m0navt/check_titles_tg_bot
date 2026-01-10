"""Migrate users to default title use case for admin bulk migration."""

from typing import Optional

from ...domain.repositories.user_repository import IUserRepository
from ...domain.repositories.settings_repository import ISettingsRepository
from ...domain.entities.user import User
from ...domain.value_objects.title import Title
from ...domain.services.title_calculation_service import TitleCalculationService
from ...application.services.admin_service import AdminService


class MigrateUsersToDefaultTitleUseCase:
    """Use case for admin to migrate all existing users to default title."""

    def __init__(
        self,
        user_repository: IUserRepository,
        settings_repository: ISettingsRepository,
        title_calculation_service: TitleCalculationService,
        admin_service: AdminService,
    ):
        """
        Initialize migrate users to default title use case.
        
        Args:
            user_repository: User repository interface
            settings_repository: Settings repository interface
            title_calculation_service: Title calculation service for recalculating displayed titles
            admin_service: Admin service for validation
        """
        self._user_repository = user_repository
        self._settings_repository = settings_repository
        self._title_calculation_service = title_calculation_service
        self._admin_service = admin_service

    async def execute(
        self,
        admin_user_id: int,
        admin_username: Optional[str] = None,
    ) -> int:
        """
        Execute migrate users to default title use case (admin only).
        
        Args:
            admin_user_id: Telegram user ID of admin
            admin_username: Admin username (optional, for validation)
            
        Returns:
            Count of users updated
            
        Raises:
            PermissionError: If user is not admin
            ValueError: If default title is not set (empty)
        """
        # Validate admin access
        if not self._admin_service.is_admin(admin_user_id, admin_username):
            raise PermissionError("Admin access required")
        
        # Get default title from settings
        default_title_str = await self._settings_repository.get_default_title()
        if not default_title_str or not default_title_str.strip():
            raise ValueError("Default title is not set. Use /set_default_title first.")
        
        default_title = Title(default_title_str.strip())
        
        # Get all users
        all_users = await self._user_repository.find_all()
        
        updated_count = 0
        
        # Update each user's full_title and recalculate displayed title if they have percentage
        for user in all_users:
            # Update full_title to default title
            user.set_full_title(default_title)
            
            # Recalculate displayed title if user has percentage
            if user.last_percentage is not None:
                new_displayed_title = await self._title_calculation_service.calculate_displayed_title(
                    user.full_title, user.last_percentage
                )
                user.update_title(new_displayed_title)
            
            # Save user
            await self._user_repository.save(user)
            updated_count += 1
        
        return updated_count
