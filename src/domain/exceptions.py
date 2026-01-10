"""Domain-specific exceptions."""


class DomainError(Exception):
    """Base exception for all domain errors."""
    pass


class TitleLockedError(DomainError):
    """Raised when attempting to update a locked title."""
    pass


class InvalidPercentageError(DomainError):
    """Raised when percentage is outside valid range (0-100)."""
    pass


class UserNotFoundError(DomainError):
    """Raised when user is not found in database."""
    pass


class InvalidTimezoneError(DomainError):
    """Raised when timezone string is invalid."""
    pass
