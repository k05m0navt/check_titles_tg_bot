"""Configuration management using environment variables."""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings:
    """Application settings loaded from environment variables."""

    # Telegram configuration
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    ADMIN_USER_ID: Optional[int] = (
        int(os.getenv("ADMIN_USER_ID", 0)) if os.getenv("ADMIN_USER_ID") else None
    )
    ADMIN_USERNAME: Optional[str] = os.getenv("ADMIN_USERNAME")

    # Supabase configuration
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")

    # Google Sheets migration (optional, migration only)
    GOOGLE_SHEET_ID: Optional[str] = os.getenv("GOOGLE_SHEET_ID")
    GOOGLE_CREDENTIALS: Optional[str] = os.getenv("GOOGLE_CREDENTIALS")

    @classmethod
    def validate(cls) -> None:
        """Validate required settings are present."""
        if not cls.TELEGRAM_BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")
        if not cls.SUPABASE_URL:
            raise ValueError("SUPABASE_URL environment variable is required")
        if not cls.SUPABASE_KEY:
            raise ValueError("SUPABASE_KEY environment variable is required")
        if not cls.ADMIN_USER_ID and not cls.ADMIN_USERNAME:
            raise ValueError(
                "At least one of ADMIN_USER_ID or ADMIN_USERNAME must be set"
            )

    @classmethod
    def is_admin(cls, telegram_user_id: Optional[int], username: Optional[str] = None) -> bool:
        """Check if user is admin by user_id (primary) or username (fallback)."""
        if cls.ADMIN_USER_ID and telegram_user_id == cls.ADMIN_USER_ID:
            return True
        if cls.ADMIN_USERNAME and username and username == cls.ADMIN_USERNAME:
            return True
        return False


# Global settings instance
settings = Settings()
