# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.
"""Custom exceptions for charms."""

from .charm_status_exceptions import (
    BaseStatusError,
    BlockedStatusError,
    MaintenanceStatusError,
    WaitingStatusError,
)

__all__ = ["BaseStatusError", "BlockedStatusError", "MaintenanceStatusError", "WaitingStatusError"]
