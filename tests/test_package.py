"""Structural smoke tests for the package."""

from btg_ai_trader import __version__


def test_initial_version() -> None:
    assert __version__ == "0.0.0"
