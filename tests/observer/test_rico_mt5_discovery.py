"""Offline tests for passive Rico/MT5 provider-symbol discovery snapshots."""

from pathlib import Path

import pytest

from btg_ai_trader.observer.rico_mt5_discovery import (
    DiscoveryContinuityError,
    DiscoveryProtocolError,
    RicoMt5DiscoveryReader,
    RicoMt5DiscoverySettings,
)

ROOT = Path(__file__).resolve().parents[2]
INDICATOR = ROOT / "tools" / "mt5" / "RicoMarketDataBridge.mq5"
PYTHON_DISCOVERY = ROOT / "src" / "btg_ai_trader" / "observer" / "rico_mt5_discovery.py"


def _snapshot(
    *symbols: str,
    prefix_errors: int = 0,
    enumeration_errors: int = 0,
) -> bytes:
    records = [
        b'{"schema":1,"record_type":"snapshot_begin","snapshot_id":"s1",'
        b'"prefix":"WIN","server_symbol_total":100}\n'
    ]
    for symbol in symbols:
        records.append(
            (
                '{"schema":1,"record_type":"symbol","snapshot_id":"s1",'
                f'"symbol":"{symbol}","custom":false}}\n'
            ).encode("ascii")
        )
    prefix_matches = len(symbols) + prefix_errors
    records.append(
        (
            '{"schema":1,"record_type":"snapshot_end","snapshot_id":"s1",'
            f'"prefix_matches":{prefix_matches},"emitted_symbols":{len(symbols)},'
            f'"excluded_custom":0,"prefix_errors":{prefix_errors},'
            f'"enumeration_errors":{enumeration_errors}}}\n'
        ).encode("ascii")
    )
    return b"".join(records)


def _reader(path: Path) -> RicoMt5DiscoveryReader:
    return RicoMt5DiscoveryReader(RicoMt5DiscoverySettings(path=path))


def test_complete_snapshot_preserves_all_candidates_without_ranking(tmp_path: Path) -> None:
    path = tmp_path / "discovery.ndjson"
    path.write_bytes(_snapshot("WINV26", "WINZ26"))
    reader = _reader(path)

    snapshot = reader.poll_snapshot()
    assert snapshot is not None
    assert snapshot.snapshot_id == "s1"
    assert snapshot.prefix == "WIN"
    assert snapshot.server_symbol_total == 100
    assert tuple(item.symbol for item in snapshot.symbols) == ("WINV26", "WINZ26")
    assert snapshot.enumeration_complete is True
    assert not hasattr(snapshot, "selected")
    assert not hasattr(snapshot, "front_contract")
    assert reader.poll_snapshot() is None


def test_incomplete_snapshot_does_not_advance_offset(tmp_path: Path) -> None:
    path = tmp_path / "discovery.ndjson"
    full = _snapshot("WINV26")
    cut = full.rfind(b'{"schema":1,"record_type":"snapshot_end"')
    path.write_bytes(full[:cut])
    reader = _reader(path)

    assert reader.poll_snapshot() is None
    assert reader.offset == 0

    with path.open("ab") as sink:
        sink.write(full[cut:])
    snapshot = reader.poll_snapshot()
    assert snapshot is not None
    assert tuple(item.symbol for item in snapshot.symbols) == ("WINV26",)


def test_multiple_snapshots_are_consumed_in_append_order(tmp_path: Path) -> None:
    path = tmp_path / "discovery.ndjson"
    first = _snapshot("WINV26")
    second = _snapshot("WINZ26").replace(b'"s1"', b'"s2"')
    path.write_bytes(first + second)
    reader = _reader(path)

    one = reader.poll_snapshot()
    two = reader.poll_snapshot()
    assert one is not None and two is not None
    assert one.snapshot_id == "s1"
    assert two.snapshot_id == "s2"
    assert tuple(item.symbol for item in two.symbols) == ("WINZ26",)


def test_custom_symbol_or_bad_accounting_fails_closed(tmp_path: Path) -> None:
    path = tmp_path / "discovery.ndjson"
    custom = _snapshot("WINV26").replace(b'"custom":false', b'"custom":true')
    path.write_bytes(custom)
    with pytest.raises(DiscoveryProtocolError, match="custom symbols"):
        _reader(path).poll_snapshot()

    bad_count = _snapshot("WINV26").replace(b'"prefix_matches":1', b'"prefix_matches":2')
    path.write_bytes(bad_count)
    with pytest.raises(DiscoveryProtocolError, match="accounting"):
        _reader(path).poll_snapshot()


def test_duplicate_or_out_of_prefix_symbol_fails_closed(tmp_path: Path) -> None:
    path = tmp_path / "discovery.ndjson"
    path.write_bytes(_snapshot("WINV26", "WINV26"))
    with pytest.raises(DiscoveryProtocolError, match="duplicate"):
        _reader(path).poll_snapshot()

    path.write_bytes(_snapshot("WDOU26"))
    with pytest.raises(DiscoveryProtocolError, match="outside configured prefix"):
        _reader(path).poll_snapshot()


def test_discovery_errors_are_preserved_instead_of_hidden(tmp_path: Path) -> None:
    path = tmp_path / "discovery.ndjson"
    path.write_bytes(_snapshot("WINV26", prefix_errors=1, enumeration_errors=2))
    snapshot = _reader(path).poll_snapshot()
    assert snapshot is not None
    assert snapshot.prefix_errors == 1
    assert snapshot.enumeration_errors == 2
    assert snapshot.prefix_matches == 2
    assert snapshot.enumeration_complete is False


def test_file_shrink_or_disappearance_after_consumption_breaks_continuity(
    tmp_path: Path,
) -> None:
    path = tmp_path / "discovery.ndjson"
    path.write_bytes(_snapshot("WINV26") + _snapshot("WINZ26").replace(b'"s1"', b'"s2"'))
    reader = _reader(path)
    assert reader.poll_snapshot() is not None

    path.write_bytes(b"x")
    with pytest.raises(DiscoveryContinuityError):
        reader.poll_snapshot()

    path.write_bytes(_snapshot("WINV26"))
    fresh = _reader(path)
    assert fresh.poll_snapshot() is not None
    path.unlink()
    with pytest.raises(DiscoveryContinuityError):
        fresh.poll_snapshot()


def test_python_discovery_has_no_mt5_control_or_execution_surface() -> None:
    source = PYTHON_DISCOVERY.read_text(encoding="utf-8")
    prohibited = (
        "import MetaTrader5",
        "from MetaTrader5",
        "order_send",
        "order_check",
        "account_info",
        "positions_get",
        "symbol_select",
    )
    for token in prohibited:
        assert token not in source


def test_indicator_discovery_enumerates_without_market_watch_mutation() -> None:
    source = INDICATOR.read_text(encoding="utf-8")
    assert "DiscoveryBridgeFile" in source
    assert 'DiscoveryPrefix = "WIN"' in source
    assert "SymbolsTotal(false)" in source
    assert "SymbolName(i, false)" in source
    assert "SymbolExist(name, custom)" in source
    assert '"custom\\\":false' in source
    assert "prefix_errors" in source

    prohibited = (
        "SymbolSelect(",
        "SYMBOL_START_TIME",
        "SYMBOL_EXPIRATION_TIME",
        "SYMBOL_DIGITS",
        "OrderSend",
        "OrderCheck",
        "OrderCalcMargin",
        "OrderCalcProfit",
        "AccountInfo",
        "PositionGet",
        "CTrade",
    )
    for token in prohibited:
        assert token not in source
