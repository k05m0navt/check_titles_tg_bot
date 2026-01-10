"""Delete user use case (admin only)."""

from typing import Optional

from ...domain.repositories.user_repository import IUserRepository
from ...domain.exceptions import UserNotFoundError
from ...application.services.admin_service import AdminService


class DeleteUserUseCase:
    """Use case for deleting a user (admin only)."""

    def __init__(
        self,
        user_repository: IUserRepository,
        admin_service: AdminService,
    ):
        """
        Initialize delete user use case.
        
        Args:
            user_repository: User repository interface
            admin_service: Admin service for validation
        """
        self._user_repository = user_repository
        self._admin_service = admin_service

    async def execute(
        self,
        target_telegram_user_id: int,
        admin_telegram_user_id: int,
        admin_username: Optional[str] = None,
    ) -> None:
        """
        Execute delete user use case.
        
        Args:
            target_telegram_user_id: Telegram user ID of target user to delete
            admin_telegram_user_id: Telegram user ID of admin
            admin_username: Admin username (optional, for fallback validation)
            
        Raises:
            PermissionError: If user is not admin
            UserNotFoundError: If target user not found
        """
        # Validate admin access
        if not self._admin_service.is_admin(admin_telegram_user_id, admin_username):
            raise PermissionError("Admin access required")

        # Check if target user exists
        user = await self._user_repository.get_by_telegram_id(target_telegram_user_id)
        if not user:
            raise UserNotFoundError(
                f"User with Telegram ID {target_telegram_user_id} not found"
            )

        # Delete user (cascade will handle related records)
        deleted = await self._user_repository.delete(target_telegram_user_id)
        if not deleted:
            raise UserNotFoundError(
                f"User with Telegram ID {target_telegram_user_id} not found"
            )
