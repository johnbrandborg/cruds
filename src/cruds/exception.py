"""
Custom Exceptions
"""


class OAuthAccessTokenError(Exception):
    pass


class OAuthStateError(Exception):
    """Raised when state parameter validation fails (CSRF protection)."""

    pass
