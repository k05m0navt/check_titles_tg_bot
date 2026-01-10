"""Title calculation service based on percentage rules."""

from typing import Protocol
from ..value_objects.title import Title
from ..value_objects.percentage import Percentage


class IActiveUserCounter(Protocol):
    """Protocol for counting active users (used for 100% rule)."""

    async def count_active_users(self) -> int:
        """Count active users in database."""
        ...


class TitleCalculationService:
    """Service for calculating new title based on percentage rules."""

    def __init__(self, active_user_counter: IActiveUserCounter):
        """
        Initialize title calculation service.
        
        Args:
            active_user_counter: Service to count active users for 100% rule
        """
        self._active_user_counter = active_user_counter

    async def calculate_displayed_title(
        self, full_title: Title, percentage: Percentage
    ) -> Title:
        """
        Calculate displayed title from full_title based on percentage rules.
        
        Rules:
        - 0% → Show first 3 letters from full_title
        - 1-5% → Show first 1 letter from full_title
        - 95-99% → Show (full_title_letters - 1) letters from full_title
        - 100% → Show (full_title_letters - active_user_count) letters from full_title
        - Other percentages → No change (return current displayed title based on last_percentage)
        
        Args:
            full_title: Full/base title value object (set by admin)
            percentage: Percentage value object (0-100)
            
        Returns:
            Displayed title value object (substring of full_title)
        """
        # If full_title is empty, return empty title
        if not full_title.value or full_title.letter_count() == 0:
            return Title("")
        
        percent_value = int(percentage)
        full_title_letters = full_title.letter_count()

        if percent_value == 0:
            # Show first 3 letters from full_title
            return full_title.substring_by_letter_count(3)
        elif 1 <= percent_value <= 5:
            # Show first 1 letter from full_title
            return full_title.substring_by_letter_count(1)
        elif 95 <= percent_value <= 99:
            # Show (full_title_letters - 1) letters from full_title
            target_count = max(0, full_title_letters - 1)
            return full_title.substring_by_letter_count(target_count)
        elif percent_value == 100:
            # Show (full_title_letters - active_user_count) letters from full_title
            # CRITICAL: Always query fresh count (never cache)
            active_user_count = await self._active_user_counter.count_active_users()
            target_count = max(0, full_title_letters - active_user_count)
            return full_title.substring_by_letter_count(target_count)
        else:
            # No change for other percentages - return empty (or could use last_percentage if tracked)
            # For now, return empty if percentage doesn't match any rule
            return Title("")

    async def calculate_new_title(
        self, current_title: Title, percentage: Percentage
    ) -> Title:
        """
        DEPRECATED: Use calculate_displayed_title instead.
        
        Kept for backward compatibility but should not be used with new full_title strategy.
        """
        # Legacy implementation - delegate to calculate_displayed_title
        # This maintains backward compatibility but is not the correct approach
        return await self.calculate_displayed_title(current_title, percentage)
