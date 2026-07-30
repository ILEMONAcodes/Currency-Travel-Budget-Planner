"""Domain-specific custom exceptions."""


class PlannerException(Exception):
    """Base exception for all application and domain errors."""

    pass


class ValidationError(PlannerException):
    """Raised when user input or schema validation fails."""

    pass


class StorageError(PlannerException):
    """Raised when JSON/CSV file reading, writing, or storage operations fail."""

    pass


class APIError(PlannerException):
    """Raised when external API requests fail or return error responses."""

    pass


class CurrencyNotFoundError(APIError):
    """Raised when a specified currency code is invalid or unsupported by the API."""

    pass