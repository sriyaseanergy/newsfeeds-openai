class EmailError(Exception):
    """Base exception for email notification failures."""


class EmailAuthenticationError(EmailError):
    """Raised when Graph authentication fails."""


class EmailSendError(EmailError):
    """Raised when sending email via Graph fails."""

