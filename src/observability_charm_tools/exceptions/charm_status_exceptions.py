"""Exceptions for expressing charm statuses."""


class BaseStatusError(Exception):
    """Base exception for errors that should result in an ops status."""

    pass


class BlockedStatusError(BaseStatusError):
    """Raised when an error should result in a Blocked status."""

    pass


class WaitingStatusError(BaseStatusError):
    """Raised when an error should result in a Waiting status."""

    pass


class MaintenanceStatusError(BaseStatusError):
    """Raised when an error should result in a Maintenance status."""

    pass
