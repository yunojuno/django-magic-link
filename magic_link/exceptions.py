class InvalidLink(Exception):
    """Generic base exception for invalid link errors."""


class InactiveLink(InvalidLink):
    """Raised if link is marked as inactive."""


class ExpiredLink(InvalidLink):
    """Raised if link has expired."""


class UsedLink(InvalidLink):
    """Raised if the link has already been used."""
