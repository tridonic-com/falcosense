"""Exceptions for the FalcoSENSE client."""

from __future__ import annotations


class FalcoSenseError(Exception):
    """Base error for all FalcoSENSE failures."""


class FalcoSenseConnectionError(FalcoSenseError):
    """Raised when the device cannot be reached."""


class FalcoSenseAuthError(FalcoSenseError):
    """Raised when authentication is rejected by the device."""
