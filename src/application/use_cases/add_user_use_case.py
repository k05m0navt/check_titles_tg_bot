"""Add user use case for admin to manually add users."""

from typing import Optional

from ...domain.repositories.user_repository import IUserRepository
from ...domain.exceptions import UserNotFoundError
from ...application.services.admin_service import AdminService
from ...infrastructure.telegram.telegram_user_resolver import TelegramUserResolver
from .register_user_use_case import RegisterUserUseCase


class AddUserUseCase:
    """Use case for admin to manually add users."""

    def __init__(
        self,
        telegram_user_resolver: TelegramUserResolver,
        register_user_use_case: RegisterUserUseCase,
        user_repository: IUserRepository,
        admin_service: AdminService,
    ):
        """
        Initialize add user use case.
        
        Args:
            telegram_user_resolver: Telegram user resolver service (injected, uses bot_instance internally)
            register_user_use_case: Register user use case (delegates user creation logic)
            user_repository: User repository for checking existing users
            admin_service: Admin service for validation
        """
        self._telegram_user_resolver = telegram_user_resolver
        self._register_user_use_case = register_user_use_case
        self._user_repository = user_repository
        self._admin_service = admin_service

    async def execute(
        self,
        username: str,
        chat_id: int,
        admin_user_id: int,
        admin_username: Optional[str] = None,
    ) -> bool:
        """
        Execute add user use case (admin only).
        
        Args:
            username: Telegram username (with or without @)
            chat_id: Chat ID where username should be resolved (required by Telegram API)
            admin_user_id: Telegram user ID of admin
            admin_username: Admin username (optional, for validation)
            
        Returns:
            True if user was added/created, False if user already existed (idempotent)
            
        Raises:
            PermissionError: If user is not admin
            ValueError: If inputs are invalid or resolver fails
            UserNotFoundError: If username doesn't exist in Telegram chat
        """
        # Validate admin access
        if not self._admin_service.is_admin(admin_user_id, admin_username):
            raise PermissionError("Admin access required")
        
        # Validate inputs
        if not username or not username.strip():
            raise ValueError("Username cannot be empty")
        
        if not isinstance(chat_id, int) or chat_id == 0:
            raise ValueError("Invalid chat_id: must be a valid integer")
        
        # Resolve username to Telegram user ID
        try:
            telegram_user_id = await self._telegram_user_resolver.resolve_username_to_user_id(
                username, chat_id
            )
        except UserNotFoundError:
            # Re-raise with friendly message
            raise UserNotFoundError(
                f"User @{username.lstrip('@')} not found in Telegram chat {chat_id}. "
                "Please check the username and chat_id."
            )
        except ValueError as e:
            # Resolver failed due to network/API error
            raise ValueError(f"Error resolving username @{username.lstrip('@')}: {str(e)}")
        
        # Check if user already exists (idempotent)
        existing_user = await self._user_repository.get_by_telegram_id(telegram_user_id)
        if existing_user:
            return False  # User already exists, return success (idempotent)
        
        # Get display_name from Telegram API (via resolver's bot instance)
        # Note: We already have telegram_user_id, but we need display_name if available
        # For now, we'll use username as display_name fallback (can be enhanced later)
        display_name = None  # Will be set to username if needed, but Telegram API doesn't provide it directly from username resolution
        
        # Call register_user_use_case to create user (handles default title logic)
        try:
            result = await self._register_user_use_case.execute(
                telegram_user_id=telegram_user_id,
                telegram_username=username.lstrip("@"),
                display_name=display_name,
            )
            return result
        except Exception as e:
            # Handle errors from register_user_use_case
            if isinstance(e, (ValueError, ConnectionError)):
                raise
            # Wrap other exceptions
            raise ValueError(f"Error creating user: {str(e)}")
