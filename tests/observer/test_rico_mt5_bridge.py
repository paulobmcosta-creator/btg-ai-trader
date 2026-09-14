"""Offline tests for the passive Rico/MT5 append-only bridge."""

from pathlib import Path

import pytest

from btg_ai_trader.observer.provider import CapabilitySupport, FidelityMode
from btg_ai_trader.observer.raw_source import RawChannel
from btg_ai_trader.observer.rico_mt5_bridge import (
    RICO_MT5_PROVIDER,
    BridgeContinuityError,
    BridgeRecordTooLargeError,
    RicoMt5BridgeReader,
    RicoMt5BridgeSettings,
)
from btg_ai_trader.observer.values import MissingReason

ROOT = Path(__file__).resolve().parents[2]
INDICATOR = ROOT / "tools" / "mt5" / "RicoMarketDataBridge.mq5"
PYTHON_BRIDGE = ROOT / "src" / "btg_ai_trader" / "observer" / "rico_mt5_bridge.py"


def settings(path: Path, *, max_record_bytes: int = 16_384) -> RicoMt5BridgeSettings:
    return RicoMt5BridgeSettings(
        capture_scope="rico-mt5-offline-fixture",
        symbol="WINV26",
        path=path,
        max_record_bytes=max_record_bytes,
    )


def test_capabilities_do_not_claim_unverified_runtime_fidelity(tmp_path: Path) -> None:
    descriptor = RicoMt5BridgeReader(settings(tmp_path / "bridge.ndjson")).describe_capabilities()
    assert descriptor.provider == RICO_MT5_PROVIDER
    assert descriptor.capture_scope == "rico-mt5-offline-fixture"
    assert descriptor.ticks is CapabilitySupport.SUPPORTED
    assert descriptor.candles is CapabilitySupport.UNSUPPORTED
    assert descriptor.source_sequence is CapabilitySupport.UNKNOWN
    assert descriptor.timestamp_resolution is MissingReason.UNKNOWN
    assert descriptor.fidelity is FidelityMode.UNKNOWN


def test_missing_or_incomplete_file_does_not_fabricate_exhaustion_or_frame(tmp_path: Path) -> None:
    path = tmp_path / "bridge.ndjson"
    reader = RicoMt5BridgeReader(settings(path))
    assert reader.poll_next() is None
    assert reader.offset == 0

    path.write_bytes(b'{"schema":1}')
    assert reader.poll_next() is None
    assert reader.offset == 0

    with path.open("ab") as sink:
        sink.write(b"\n")
    frame = reader.poll_next()
    assert frame is not None
    assert frame.payload == b'{"schema":1}\n'
    assert frame.channel is RawChannel.TICK
    assert frame.reference.provider == RICO_MT5_PROVIDER
    assert frame.reference.scope == "rico-mt5-offline-fixture"
    assert frame.reference.symbol == "WINV26"
    assert reader.offset == len(frame.payload)


def test_order_and_duplicate_records_are_preserved(tmp_path: Path) -> None:
    path = tmp_path / "bridge.ndjson"
    line = b'{"bridge_sequence":1}\n'
    path.write_bytes(line + line + b'{"bridge_sequence":2}\n')
    reader = RicoMt5BridgeReader(settings(path))

    first = reader.poll_next()
    second = reader.poll_next()
    third = reader.poll_next()
    assert first is not None and second is not None and third is not None
    assert first.payload == line
    assert second.payload == line
    assert third.payload == b'{"bridge_sequence":2}\n'
    assert reader.poll_next() is None


def test_oversized_complete_and_partial_records_fail_closed(tmp_path: Path) -> None:
    complete = tmp_path / "complete.ndjson"
    complete.write_bytes(b"12345\n")
    with pytest.raises(BridgeRecordTooLargeError):
        RicoMt5BridgeReader(settings(complete, max_record_bytes=4)).poll_next()

    partial = tmp_path / "partial.ndjson"
    partial.write_bytes(b"12345")
    with pytest.raises(BridgeRecordTooLargeError):
        RicoMt5BridgeReader(settings(partial, max_record_bytes=4)).poll_next()


def test_file_shrink_or_disappearance_after_consumption_breaks_continuity(tmp_path: Path) -> None:
    path = tmp_path / "bridge.ndjson"
    path.write_bytes(b"first\nsecond\n")
    reader = RicoMt5BridgeReader(settings(path))
    assert reader.poll_next() is not None

    path.write_bytes(b"x")
    with pytest.raises(BridgeContinuityError):
        reader.poll_next()

    path.write_bytes(b"again\n")
    fresh = RicoMt5BridgeReader(settings(path))
    assert fresh.poll_next() is not None
    path.unlink()
    with pytest.raises(BridgeContinuityError):
        fresh.poll_next()


def test_python_bridge_has_no_mt5_or_execution_surface() -> None:
    source = PYTHON_BRIDGE.read_text(encoding="utf-8")
    prohibited = (
        "import MetaTrader5",
        "from MetaTrader5",
        "order_send",
        "order_check",
        "order_calc_margin",
        "positions_get",
        "account_info",
    )
    for token in prohibited:
        assert token not in source


def test_mql5_bridge_is_custom_indicator_with_shared_append_only_transport() -> None:
    source = INDICATOR.read_text(encoding="utf-8")
    assert "#property indicator_chart_window" in source
    assert "#property indicator_plots 0" in source
    assert "OnCalculate(" in source
    assert "FILE_READ | FILE_WRITE" in source
    assert "FILE_SHARE_READ" in source
    assert "FILE_COMMON" in source
    assert "FileSeek(bridge_handle, 0, SEEK_END)" in source
    assert "SymbolInfoTick(_Symbol, tick)" in source

    prohibited = (
        "OrderSend",
        "OrderCheck",
        "OrderCalcMargin",
        "OrderCalcProfit",
        "CTrade",
        "AccountInfo",
        "PositionGet",
        "OnTrade(",
        "OnTick(",
    )
    for token in prohibited:
        assert token not in source
