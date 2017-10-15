"""Shared functions for all input methods."""

class Cancelled(RuntimeError):
    """Signals that the user cancelled the input."""
    pass

class Invalid(RuntimeError):
    """Signals that the user gave invalid input."""
    pass
