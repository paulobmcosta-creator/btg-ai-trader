"""Offline tests for the Rico/MT5 controlled local evidence harness."""

import datetime
from collections.abc import Callable
from pathlib import Path

import pytest
from scripts import rico_mt5_first_lab_capture as capture

from btg_ai_trader.observer.storage_records import EvidenceRecord, decode_record


DISCOVERY = (
    b'{"schema":1,"record_type":"snapshot_begin","snapshot_id":"s1",'
    b'"prefix":"WIN","server_symbol_total":10}\n'
    b'{"schema":1,"record_type":"symbol","snapshot_id":"s1",'
    b'"symbol":"WINV26","custom":false}\n'
    b'{"schema":1,"record_type":"snapshot_end","snapshot_id":"s1",'
    b'"prefix_matches":1,"emitted_symbols":1,"excluded_custom":0,'
    b'"prefix_errors":0,"enumeration_errors":0}\n'
)
TICKS = (
    b'{"schema":1,"provider":"rico-mt5","symbol":"WINV26","time_msc":1,'
    b'"bid":1,"ask":2,"last":1,"volume":1,"volume_real":1,"flags":1,'
    b'"bridge_sequence":1}\n'
    b'{"schema":1,"provider":"rico-mt5","symbol":"WINV26","time_msc":2,'
    b'"bid":1,"ask":2,"last":1,"volume":1,"volume_real":1,"flags":1,'
    b'"bridge_sequence":2}\n'
)
CANDLE = (
    b'{"schema":1,"provider":"rico-mt5","symbol":"WINV26",'
    b'"interval_start":1,"interval_end":61,"timeframe_seconds":60,'
    b'"finality":"FINAL","open":1,"high":2,"low":1,"close":2,'
    b'"tick_volume":2,"volume":2,"spread":1,"bridge_sequence":1}\n'
)


class FakeClock:
    def __init__(self, on_first_sleep: Callable[[], None]) -> None:
        self.ns = 0
        self.on_first_sleep = on_first_sleep
        self.sleep_calls = 0
        self.base = datetime.datetime(2026, 9, 14, 19, tzinfo=datetime.UTC)

    def monotonic_ns(self) -> int:
        self.ns += 100_000_000
        return self.ns

    def sleep(self, seconds: float) -> None:
        self.ns += int(seconds * 1_000_000_000)
        if self.sleep_calls == 0:
            self.on_first_sleep()
        self.sleep_calls += 1

    def wall_now(self) -> datetime.datetime:
        return self.base + datetime.timedelta(microseconds=self.ns // 1000)


def _paths(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    transport = tmp_path / "transport"
    output = tmp_path / "output"
    transport.mkdir()
    output.mkdir()
    return (
        transport / "discovery.ndjson",
        transport / "ticks.ndjson",
        transport / "candles.ndjson",
        output,
    )


def _evidence_records(session_root: Path) -> list[EvidenceRecord]:
    records: list[EvidenceRecord] = []
    for path in sorted((session_root / "archive").glob("*.json")):
        decoded = decode_record(path.read_bytes())
        if isinstance(decoded, EvidenceRecord):
            records.append(decoded)
    return records


def test_controlled_capture_preserves_raw_prefixes_health_and_latency(tmp_path: Path) -> None:
    discovery, ticks, candles, output = _paths(tmp_path)

    def emit_transport() -> None:
        discovery.write_bytes(DISCOVERY)
        ticks.write_bytes(TICKS)
        candles.write_bytes(CANDLE)

    clock = FakeClock(emit_transport)
    session_root = capture.run_first_lab(
        instrument="WINV26",
        capture_scope="rico-first-lab",
        code_revision="a" * 40,
        discovery_file=discovery,
        tick_file=ticks,
        candle_file=candles,
        output_root=output,
        clock_scope="rico-local-monotonic",
        discovery_timeout_seconds=5.0,
        capture_seconds=60.0,
        poll_interval_ms=100,
        heartbeat_timeout_ms=5000,
        market_staleness_ms=120_000,
        monotonic_ns=clock.monotonic_ns,
        sleep=clock.sleep,
        wall_now=clock.wall_now,
    )

    records = _evidence_records(session_root)
    raws = [record.raw for record in records]
    assert DISCOVERY in raws
    assert TICKS in raws
    assert CANDLE in raws
    assert any(b'"channel":"TICK"' in raw and b'"sequence":2' in raw for raw in raws)
    assert any(b'"readiness":"READY"' in raw for raw in raws)
    assert any(
        b'"tick_frames":2' in raw
        and b'"candle_frames":1' in raw
        and b'"trading_capability":false' in raw
        for raw in raws
    )


def test_symbol_mismatch_fails_closed_but_preserves_consumed_raw_prefix(tmp_path: Path) -> None:
    discovery, ticks, candles, output = _paths(tmp_path)
    wrong_tick = TICKS.replace(b'"symbol":"WINV26"', b'"symbol":"WINZ26"')

    def emit_transport() -> None:
        discovery.write_bytes(DISCOVERY)
        ticks.write_bytes(wrong_tick)
        candles.write_bytes(CANDLE)

    clock = FakeClock(emit_transport)
    with pytest.raises(RuntimeError, match="provider/symbol"):
        capture.run_first_lab(
            instrument="WINV26",
            capture_scope="rico-first-lab",
            code_revision="b" * 40,
            discovery_file=discovery,
            tick_file=ticks,
            candle_file=candles,
            output_root=output,
            clock_scope="rico-local-monotonic",
            discovery_timeout_seconds=5.0,
            capture_seconds=60.0,
            poll_interval_ms=100,
            heartbeat_timeout_ms=5000,
            market_staleness_ms=120_000,
            monotonic_ns=clock.monotonic_ns,
            sleep=clock.sleep,
            wall_now=clock.wall_now,
        )

    session_roots = tuple(output.iterdir())
    assert len(session_roots) == 1
    raws = [record.raw for record in _evidence_records(session_roots[0])]
    assert wrong_tick.splitlines(keepends=True)[0] in raws
    assert any(b'"outcome":"FAILED"' in raw for raw in raws)


def test_nonfresh_transport_is_rejected_before_session_creation(tmp_path: Path) -> None:
    discovery, ticks, candles, output = _paths(tmp_path)
    ticks.write_bytes(b"stale\n")

    with pytest.raises(ValueError, match="absent or empty"):
        capture.run_first_lab(
            instrument="WINV26",
            capture_scope="rico-first-lab",
            code_revision="c" * 40,
            discovery_file=discovery,
            tick_file=ticks,
            candle_file=candles,
            output_root=output,
            clock_scope="rico-local-monotonic",
            discovery_timeout_seconds=5.0,
            capture_seconds=60.0,
            poll_interval_ms=100,
            heartbeat_timeout_ms=5000,
            market_staleness_ms=120_000,
        )
    assert tuple(output.iterdir()) == ()


def test_capture_requires_complete_exact_discovery_match(tmp_path: Path) -> None:
    discovery, ticks, candles, output = _paths(tmp_path)
    wrong_discovery = DISCOVERY.replace(b"WINV26", b"WINZ26")

    def emit_transport() -> None:
        discovery.write_bytes(wrong_discovery)
        ticks.write_bytes(TICKS)
        candles.write_bytes(CANDLE)

    clock = FakeClock(emit_transport)
    with pytest.raises(RuntimeError, match="absent from discovery"):
        capture.run_first_lab(
            instrument="WINV26",
            capture_scope="rico-first-lab",
            code_revision="d" * 40,
            discovery_file=discovery,
            tick_file=ticks,
            candle_file=candles,
            output_root=output,
            clock_scope="rico-local-monotonic",
            discovery_timeout_seconds=5.0,
            capture_seconds=60.0,
            poll_interval_ms=100,
            heartbeat_timeout_ms=5000,
            market_staleness_ms=120_000,
            monotonic_ns=clock.monotonic_ns,
            sleep=clock.sleep,
            wall_now=clock.wall_now,
        )


def test_harness_has_no_terminal_account_position_or_order_surface() -> None:
    harness = Path(__file__).resolve().parents[1] / "scripts" / "rico_mt5_first_lab_capture.py"
    source = harness.read_text(encoding="utf-8")
    prohibited = (
        "import MetaTrader5",
        "from MetaTrader5",
        "order_send",
        "order_check",
        "order_calc_margin",
        "positions_get",
        "account_info",
        "symbol_select",
        "MT5_PASSWORD",
        "MT5_LOGIN",
    )
    for token in prohibited:
        assert token not in source
