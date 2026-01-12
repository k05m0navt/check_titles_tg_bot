"""Message parsing service for extracting percentage values from @HowGayBot messages."""

import re
from typing import Optional, TYPE_CHECKING

from ...domain.value_objects.percentage import Percentage
from ...domain.exceptions import InvalidPercentageError

if TYPE_CHECKING:
    from telegram import Message


class MessageParser:
    """Service for parsing messages from @HowGayBot."""

    # Regex pattern to match @HowGayBot message format: "I am X% gay!"
    PERCENTAGE_PATTERN = re.compile(r"I am (\d+)% gay!", re.IGNORECASE)

    @classmethod
    def should_process_message(cls, message: "Message") -> bool:
        """
        Check if message should be processed (from or via @HowGayBot).
        
        Messages can be:
        1. Directly from @HowGayBot (message.from_user.username == "HowGayBot")
        2. Sent via @HowGayBot (message.via_bot.username == "HowGayBot")
        
        Args:
            message: Telegram message object
            
        Returns:
            True if message is from or via @HowGayBot, False otherwise
        """
        if not message:
            return False
        
        # Check if message is directly from HowGayBot
        if message.from_user and message.from_user.username == "HowGayBot":
            return True
        
        # Check if message is sent via HowGayBot
        if message.via_bot and message.via_bot.username == "HowGayBot":
            return True
        
        return False

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
