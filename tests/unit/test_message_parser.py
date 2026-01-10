"""Unit tests for message parser."""

import pytest
from src.application.services.message_parser import MessageParser
from src.domain.value_objects.percentage import Percentage
from src.domain.exceptions import InvalidPercentageError


class TestMessageParser:
    """Test cases for MessageParser."""

    def test_should_process_message_from_howgaybot(self):
        """Test message from @HowGayBot should be processed."""
        assert MessageParser.should_process_message("HowGayBot") is True

    def test_should_not_process_message_from_other_bot(self):
        """Test message from other bot should not be processed."""
        assert MessageParser.should_process_message("OtherBot") is False

    def test_extract_percentage_valid(self):
        """Test extracting percentage from valid message."""
        message = "I am 90% gay!"
        percentage = MessageParser.extract_percentage(message)
        assert int(percentage) == 90

    def test_extract_percentage_invalid_range(self):
        """Test extracting percentage from invalid range."""
        message = "I am 150% gay!"
        with pytest.raises(InvalidPercentageError):
            MessageParser.extract_percentage(message)

    def test_can_extract_percentage(self):
        """Test can_extract_percentage helper."""
        assert MessageParser.can_extract_percentage("I am 90% gay!") is True
        assert MessageParser.can_extract_percentage("Invalid message") is False
