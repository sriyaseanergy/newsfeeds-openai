class InvalidIdTokenError(Exception):
    """Raised when the Azure AD ID token fails validation."""


class MissingEmailClaimError(Exception):
    """Raised when the ID token does not contain a usable email claim."""


class InactiveEmployeeError(Exception):
    """Raised when the token is valid but no active MyWork employee matches."""
