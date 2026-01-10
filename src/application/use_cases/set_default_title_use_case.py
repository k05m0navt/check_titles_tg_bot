"""Set default title use case for admin to set default title for new users."""

from typing import Optional

from ...domain.repositories.settings_repository import ISettingsRepository
from ...application.services.admin_service import AdminService


class SetDefaultTitleUseCase:
    """Use case for admin to set default title for new user registrations."""

    def __init__(
        self,
        settings_repository: ISettingsRepository,
        admin_service: AdminService,
    ):
        """
        Initialize set default title use case.
        
        Args:
            settings_repository: Settings repository interface
            admin_service: Admin service for validation
        """
        self._settings_repository = settings_repository
        self._admin_service = admin_service

    async def execute(
        self,
        default_title: str,
        admin_user_id: int,
        admin_username: Optional[str] = None,
    ) -> str:
        """
        Execute set default title use case (admin only).
        
        Args:
            default_title: Default title string (will be trimmed)
            admin_user_id: Telegram user ID of admin
            admin_username: Admin username (optional, for validation)
            
        Returns:
            Confirmation message with new default title
            
        Raises:
            PermissionError: If user is not admin
            ValueError: If title validation fails (too long or invalid characters)
        """
        # Validate admin access
        if not self._admin_service.is_admin(admin_user_id, admin_username):
            raise PermissionError("Admin access required")
        
        # Validate and set default title (repository validates again, but we validate first for better error messages)
        try:
            await self._settings_repository.set_default_title(default_title)
        except ValueError as e:
            # Re-raise with specific error message
            if "too long" in str(e).lower():
                raise ValueError("Title too long (max 500 characters)")
            elif "invalid characters" in str(e).lower() or "control characters" in str(e).lower():
                raise ValueError("Title contains invalid characters (control characters not allowed)")
            raise  # Re-raise other ValueErrors as-is
        
        # Return confirmation message
        trimmed_title = default_title.strip()
        if trimmed_title:
            return f"Default title updated to '{trimmed_title}'. New registrations will use this title."
        else:
            return "Default title cleared. New registrations will have no default title."
