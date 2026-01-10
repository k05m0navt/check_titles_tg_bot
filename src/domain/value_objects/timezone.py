"""Timezone value object with validation."""

from dataclasses import dataclass
from typing import Optional
import pytz

from ..exceptions import InvalidTimezoneError


@dataclass(frozen=True)
class Timezone:
    """Immutable timezone value object."""

    value: str

    def __post_init__(self) -> None:
        """Validate timezone string is valid."""
        try:
            pytz.timezone(self.value)
        except pytz.exceptions.UnknownTimeZoneError:
            raise InvalidTimezoneError(
                f"Invalid timezone: {self.value}"
            )

    def __str__(self) -> str:
        """Return timezone value as string."""
        return self.value

    @classmethod
    def from_string(cls, value: str, default: str = "UTC") -> "Timezone":
        """Create Timezone from string, with fallback to default."""
        try:
            return cls(value)
        except InvalidTimezoneError:
            if default:
                return cls(default)
            raise

    @classmethod
    def default(cls) -> "Timezone":
        """Get default timezone (UTC)."""
        return cls("UTC")
