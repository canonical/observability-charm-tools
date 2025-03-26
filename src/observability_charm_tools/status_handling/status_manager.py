# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.
"""A context manager that catches known exceptions and maps them to charm statuses."""

from typing import Dict, List, Optional, Type

from ops import ActiveStatus, BlockedStatus, MaintenanceStatus, StatusBase, WaitingStatus

from observability_charm_tools.exceptions import (
    BlockedStatusError,
    MaintenanceStatusError,
    WaitingStatusError,
)

DEFAULT_STATUS_MAP = {
    BlockedStatusError: BlockedStatus,
    WaitingStatusError: WaitingStatus,
    MaintenanceStatusError: MaintenanceStatus,
}


class StatusManager:
    """A context manager that catches known exceptions and maps them to charm statuses.

    This is useful when running a series of tasks, perhaps in a charm reconcile function, that each may succeed or
    raise an Exception.  Use this context manager to collect all the statuses independently, then use the worst
    status to set the unit status.

    Example usage:

    ```
    class MyCharm(CharmBase):
        def do_something_that_might_block(self):
            raise BlockedStatusError("Something went wrong")

        def do_something_that_might_wait(self):
            raise WaitingStatusError("Something went wrong")

        ...

        def reconcile(self, _):
            status_manager = StatusManager()
            with status_manager:
                do_something_that_might_block()

            with status_manager:
                do_something_that_might_wait()

            # Set the unit status to the worst observed status.  If problematic statuses observed, set to Active
            self.unit.status = status_manager.worst()
    ```
    """

    def __init__(self, status_map: Optional[Dict[Type[Exception], Type[StatusBase]]] = None):
        """Return a StatusManager.

        Args:
            status_map: A dictionary mapping exception types to status types.  If an exception is raised inside the
                        StatusManager's context, the StatusManager will catch that exception and instead store a Status
                        of the corresponding type.  The message on the status will be the same as the exception's
                        message, for example SomeException("message") will be stored as SomeStatus("message").
                        If an exception is raised and the type is not in the map, the exception will raise as normal.
        """
        self.statuses = []
        if not status_map:
            status_map = DEFAULT_STATUS_MAP
        _validate_status_map(status_map)
        self._status_map = status_map

    def __enter__(self):
        """Return self to be used as a context manager."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Catch known exceptions and store a Status instead, otherwise allow to be raised."""
        try:
            status_type = self._status_map[exc_type]
        except KeyError:
            # Unknown exception - do not catch it.  This means python will raise it like normal.
            return False

        # Store a Status created using the message from the error
        self.statuses.append(status_type(str(exc_val)))

        # Do not raise this known exception
        return True

    def __len__(self):
        """Return the number of statuses tracked by this manager."""
        return len(self.statuses)

    def worst(self) -> StatusBase:
        """Return the worst status in the list, or ActiveStatus if len(statuses)==0.

        Status are ranked, starting with the worst:
            BlockedStatus
            WaitingStatus
            MaintenanceStatus
            ActiveStatus
        """
        if len(self) == 0:
            return ActiveStatus("")

        return get_first_worst_status(self.statuses)


def _validate_status_map(status_map: Dict[Type[Exception], Type[StatusBase]]):
    """Raise if the status map is invalid."""
    for exception_type, status_type in status_map.items():
        try:
            if not issubclass(exception_type, Exception):
                raise TypeError(f"status_map key {exception_type} is not a subclass of Exception")
        except TypeError as e:
            raise TypeError(f"status_map key {exception_type} is not a class") from e

        try:
            if not issubclass(status_type, StatusBase):
                raise TypeError(f"status_map value {status_type} is not a subclass of StatusBase")
        except TypeError as e:
            raise TypeError(f"status_map value {status_type} is not a class") from e


def get_first_worst_status(statuses: List[StatusBase]) -> StatusBase:
    """Return the first of the worst statuses in the list.

    Raises if len(statuses) == 0.

    Status are ranked, starting with the worst:
        BlockedStatus
        WaitingStatus
        MaintenanceStatus
        ActiveStatus
    """
    if len(statuses) == 0:
        raise ValueError("No statuses provided")

    blocked = None
    waiting = None
    maintenance = None
    active = None

    for status in statuses:
        if isinstance(status, BlockedStatus):
            blocked = status
            # Escape immediately, as this is the worst status
            break
        if isinstance(status, WaitingStatus):
            waiting = waiting or status
        elif isinstance(status, MaintenanceStatus):
            maintenance = maintenance or status
        elif isinstance(status, ActiveStatus):
            active = active or status
        else:
            raise TypeError(
                f"found status {status}, expected statuses of one of [BlockedStatus, WaitingStatus, MaintenanceStatus,"
                f" ActiveStatus]"
            )

    status = blocked or waiting or maintenance or active
    return status
