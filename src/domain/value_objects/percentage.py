"""Percentage value object with validation."""

from dataclasses import dataclass
from typing import Optional

from ..exceptions import InvalidPercentageError


@dataclass(frozen=True)
class Percentage:
    """Immutable percentage value object (0-100)."""

    value: int

    def __post_init__(self) -> None:
        """Validate percentage value is in valid range."""
        if not isinstance(self.value, int):
            raise InvalidPercentageError(
                f"Percentage must be an integer, got {type(self.value)}"
            )
        if self.value < 0 or self.value > 100:
            raise InvalidPercentageError(
                f"Percentage must be between 0 and 100, got {self.value}"
            )

    def __int__(self) -> int:
        """Convert to integer."""
        return self.value

    @classmethod
    def from_string(cls, value: str) -> "Percentage":
        """Create Percentage from string."""
        try:
            return cls(int(value))
        except ValueError as e:
            raise InvalidPercentageError(
                f"Invalid percentage string: {value}"
            ) from e

    @classmethod
    def from_optional(cls, value: Optional[int]) -> Optional["Percentage"]:
        """Create Percentage from optional integer."""
        if value is None:
            return None
        return cls(value)
