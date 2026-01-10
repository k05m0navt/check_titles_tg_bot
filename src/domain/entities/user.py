"""User entity representing a Telegram bot user."""

from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional

from ..value_objects.title import Title
from ..value_objects.percentage import Percentage
from ..value_objects.timezone import Timezone


@dataclass
class User:
    """User entity with title management and preferences."""

    id: Optional[int] = None
    telegram_user_id: int = 0
    telegram_username: Optional[str] = None
    display_name: Optional[str] = None
    full_title: Title = Title("")  # Base title set by admin
    title: Title = Title("")  # Displayed title calculated from full_title based on percentage
    title_letter_count: int = 0
    title_locked: bool = False
    timezone: Timezone = Timezone.default()
    language: str = "en"
    last_percentage: Optional[Percentage] = None
    last_processed_date: Optional[date] = None
    migration_batch_id: Optional[str] = None
    migration_timestamp: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def update_title(self, new_title: Title) -> None:
        """
        Update user's title and recalculate letter count.
        
        Args:
            new_title: New title value object
        """
        self.title = new_title
        self.title_letter_count = new_title.letter_count()

    def lock_title(self) -> None:
        """Lock title to prevent automatic updates."""
        self.title_locked = True

    def unlock_title(self) -> None:
        """Unlock title to allow automatic updates."""
        self.title_locked = False

    def set_full_title(self, full_title: Title) -> None:
        """
        Set full/base title (admin only).
        
        Args:
            full_title: Full title value object set by admin
        """
        self.full_title = full_title

    def update_language(self, language: str) -> None:
        """
        Update user's language preference.
        
        Args:
            language: Language code ('en' or 'ru')
        """
        if language not in ("en", "ru"):
            raise ValueError(f"Invalid language: {language}")
        self.language = language

    def update_timezone(self, timezone: Timezone) -> None:
        """
        Update user's timezone preference.
        
        Args:
            timezone: Timezone value object
        """
        self.timezone = timezone

    def update_last_processed_date(self, processed_date: date) -> None:
        """
        Update last processed date for first-message-per-day tracking.
        
        Args:
            processed_date: Date when message was processed
        """
        self.last_processed_date = processed_date

    def is_first_message_today(self, message_date: date) -> bool:
        """
        Check if this is the first message today (timezone-aware).
        
        Args:
            message_date: Date of the message
            
        Returns:
            True if this is the first message today, False otherwise
        """
        if self.last_processed_date is None:
            return True
        return self.last_processed_date < message_date
