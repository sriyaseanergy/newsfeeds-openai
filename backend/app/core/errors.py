class ApplicationError(Exception):
    """Base exception for application-level failures."""


class ConfigurationError(ApplicationError):
    """Raised when required configuration is missing or invalid."""


class ExternalServiceError(ApplicationError):
    """Raised when an external service call fails."""


class ExternalServiceAuthenticationError(ExternalServiceError):
    """Raised when external service authentication fails."""


class ExternalServiceRateLimitError(ExternalServiceError):
    """Raised when an external service rate limit is hit."""


class ExternalServiceTimeoutError(ExternalServiceError):
    """Raised when an external service call times out."""


class ResourceNotFoundError(ApplicationError):
    """Raised when a requested resource cannot be found."""


class ConflictError(ApplicationError):
    """Raised when a request conflicts with existing state."""

