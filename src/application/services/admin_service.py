"""Admin service for validating admin access."""

from typing import Optional

from ...infrastructure.config.settings import settings as app_settings


class AdminService:
    """Service for admin validation."""

    @staticmethod
    def is_admin(
        telegram_user_id: Optional[int], username: Optional[str] = None
    ) -> bool:
        """
        Check if user is admin by user_id (primary) or username (fallback).
        
        Args:
            telegram_user_id: Telegram user ID
            username: Telegram username (optional fallback)
            
        Returns:
            True if user is admin, False otherwise
        """
        return app_settings.is_admin(telegram_user_id, username)
