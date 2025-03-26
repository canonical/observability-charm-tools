from contextlib import nullcontext

import pytest
from ops import ActiveStatus, BlockedStatus, MaintenanceStatus, WaitingStatus

from observability_charm_tools.status_handling import get_first_worst_status
from observability_charm_tools.status_handling.status_manager import StatusManager


class CustomError(Exception):
    pass


class AnotherCustomError(Exception):
    pass


@pytest.mark.parametrize(
    "status_map, exceptions, expected_statuses, context_raised",
    [
        # 2 known exceptions
        (
            {CustomError: BlockedStatus},
            [CustomError(0), CustomError(1)],
            [BlockedStatus("0"), BlockedStatus("1")],
            nullcontext(),
        ),
        # 1 unknown exception
        (
            {CustomError: BlockedStatus},
            [AnotherCustomError(0)],
            None,
            pytest.raises(AnotherCustomError),
        ),
        # a few known with one unknown exception
        (
            {CustomError: BlockedStatus},
            [CustomError(0), CustomError(1), AnotherCustomError(2), CustomError(3)],
            None,
            pytest.raises(AnotherCustomError),
        ),
    ],
)
def test_status_manager_catches_errors(status_map, exceptions, expected_statuses, context_raised):
    sm = StatusManager(status_map=status_map)

    with context_raised:
        for exception in exceptions:
            with sm:
                raise exception

        assert sm.statuses == expected_statuses


@pytest.mark.parametrize(
    "statuses, expected_status",
    [
        # The first status among equals is returned
        ([BlockedStatus("0"), BlockedStatus("1")], BlockedStatus("0")),
        # The first status among equals is returned
        ([BlockedStatus("1"), BlockedStatus("0")], BlockedStatus("1")),
        # BlockedStatus is the worst
        (
            [ActiveStatus("0"), MaintenanceStatus("1"), WaitingStatus("2"), BlockedStatus("3")],
            BlockedStatus("3"),
        ),
        # WaitingStatus is worse than Active and Maintenance
        ([ActiveStatus("0"), MaintenanceStatus("1"), WaitingStatus("2")], WaitingStatus("2")),
        # MaintenanceStatus is worse than Active
        ([ActiveStatus("0"), MaintenanceStatus("1")], MaintenanceStatus("1")),
        # ActiveStatus shows up only if there are no worse statuses, and the first one shows
        ([ActiveStatus("0"), ActiveStatus("1")], ActiveStatus("0")),
        # Returns ActiveStatus if there's nothing
        ([], ActiveStatus("")),
    ],
)
def test_status_manager_returns_first_worst_error(statuses, expected_status):
    status_manager = StatusManager()
    status_manager.statuses = statuses
    assert status_manager.worst() == expected_status


@pytest.mark.parametrize(
    "status_map",
    [
        # Status map with a non-Exception key
        {1: BlockedStatus},
        # Status map with a non-Exception key (dict is stand-in for any non-Exception type)
        {dict: BlockedStatus},
        # Status map with a non-StatusBase value
        {CustomError: 1},
        # Status map with a non-StatusBase value (dict is stand-in for any non-StatusBse type)
        {CustomError: dict},
    ],
)
def test_status_manager_rejects_incorrect_status_map(status_map):
    with pytest.raises(TypeError):
        StatusManager(status_map=status_map)  # pyright: ignore


def test_get_first_worst_status_raises_on_empty_list():
    with pytest.raises(ValueError):
        get_first_worst_status([])


def test_get_first_worst_status_raises_on_wrong_status():
    with pytest.raises(TypeError):
        get_first_worst_status(["not a status"])
