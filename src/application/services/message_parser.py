"""Message parsing service for extracting percentage values from @HowGayBot messages."""

import re
from typing import Optional

from ...domain.value_objects.percentage import Percentage
from ...domain.exceptions import InvalidPercentageError


class MessageParser:
    """Service for parsing messages from @HowGayBot."""

    # Regex pattern to match @HowGayBot message format: "I am X% gay!"
    PERCENTAGE_PATTERN = re.compile(r"I am (\d+)% gay!", re.IGNORECASE)

    @classmethod
    def should_process_message(cls, from_username: Optional[str]) -> bool:
        """
        Check if message should be processed (from @HowGayBot).
        
        Args:
            from_username: Username of message sender (from message.from_user.username)
            
        Returns:
            True if message is from @HowGayBot, False otherwise
        """
        return from_username == "HowGayBot"

    @classmethod
    def extract_percentage(cls, message_text: str) -> Percentage:
        """
        Extract percentage value from message text.
        
        Args:
            message_text: Text content of the message
            
        Returns:
            Percentage value object (0-100)
            
        Raises:
            InvalidPercentageError: If percentage cannot be extracted or is invalid
        """
        match = cls.PERCENTAGE_PATTERN.search(message_text)
        if not match:
            raise InvalidPercentageError(
                f"Message does not match expected pattern: {message_text}"
            )
        
        percentage_str = match.group(1)
        return Percentage.from_string(percentage_str)

    @classmethod
    def can_extract_percentage(cls, message_text: str) -> bool:
        """
        Check if percentage can be extracted from message text (without raising exception).
        
        Args:
            message_text: Text content of the message
            
        Returns:
            True if percentage can be extracted, False otherwise
        """
        try:
            cls.extract_percentage(message_text)
            return True
        except InvalidPercentageError:
            return False
