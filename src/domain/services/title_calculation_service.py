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
        self, full_title: Title, percentage: Percentage, current_title: Title
    ) -> Title:
        """
        Calculate displayed title by incrementing/decrementing from current_title based on percentage rules.
        
        Rules:
        - 0% → Add 3 letters to current title
        - 1-5% → Add 1 letter to current title
        - 95-99% → Remove 1 letter from current title (can become empty)
        - 100% → Remove N letters (active_user_count) from current title (can become empty/negative → empty)
        - Other percentages → No change (return current title)
        
        The result is always a substring of full_title and can be empty.
        If target letter count exceeds full_title length, result is capped at full_title length.
        
        Args:
            full_title: Full/base title value object (set by admin)
            percentage: Percentage value object (0-100)
            current_title: Current displayed title (will be incremented/decremented)
            
        Returns:
            Displayed title value object (substring of full_title, can be empty)
        """
        # If full_title is empty, return empty title
        if not full_title.value or full_title.letter_count() == 0:
            return Title("")
        
        percent_value = int(percentage)
        current_letter_count = current_title.letter_count()
        full_title_letters = full_title.letter_count()
        
        if percent_value == 0:
            # Add 3 letters to current title
            target_count = current_letter_count + 3
            # Cap at full_title length
            target_count = min(target_count, full_title_letters)
            # Can be 0 (empty) if current was empty or negative
            target_count = max(0, target_count)
            return full_title.substring_by_letter_count(target_count)
        elif 1 <= percent_value <= 5:
            # Add 1 letter to current title
            target_count = current_letter_count + 1
            # Cap at full_title length
            target_count = min(target_count, full_title_letters)
            # Can be 0 (empty) if current was -1
            target_count = max(0, target_count)
            return full_title.substring_by_letter_count(target_count)
        elif 95 <= percent_value <= 99:
            # Remove 1 letter from current title (can become empty)
            target_count = current_letter_count - 1
            # Can be negative, but we'll treat negative as 0 (empty)
            target_count = max(0, target_count)
            return full_title.substring_by_letter_count(target_count)
        elif percent_value == 100:
            # Remove N letters (active_user_count) from current title
            active_user_count = await self._active_user_counter.count_active_users()
            target_count = current_letter_count - active_user_count
            # If negative, make it empty (0)
            target_count = max(0, target_count)
            return full_title.substring_by_letter_count(target_count)
        else:
            # No change for other percentages - return current title
            # Ensure current title is still valid substring of full_title
            if current_letter_count > full_title_letters:
                # Current title is longer than full_title (shouldn't happen, but handle gracefully)
                return full_title.substring_by_letter_count(full_title_letters)
            return current_title

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
