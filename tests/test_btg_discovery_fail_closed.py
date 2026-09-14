"""Regression tests for fail-closed BTG discovery confirmation."""

from scripts import btg_first_lab_capture as capture


def test_discovery_requires_recognized_availability_shape() -> None:
    assert capture.discovery_confirms_instrument(
        [b'{"event":"available_to_subscribe","tickers":["WINV26","WINZ26"]}'],
        "WINV26",
    )

    ambiguous = [
        b'{"requested":["WINV26"],"error":"not-available"}',
        b'{"event":"other","tickers":["WINV26"]}',
        b'{"event":"available_to_subscribe","requested":["WINV26"]}',
        b'{"event":"available_to_subscribe","tickers":["WINV26"],"error":"not-available"}',
    ]
    assert capture.discovery_confirms_instrument(ambiguous, "WINV26") is False
