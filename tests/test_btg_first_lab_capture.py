"""Offline tests for the controlled BTG Data Services first-lab harness."""

import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from scripts import btg_first_lab_capture as capture

from btg_ai_trader.observer.btg_dataservices import BtgDataServicesSettings
from btg_ai_trader.observer.storage_records import EvidenceRecord, decode_record


class FakeVendorClient:
    def __init__(
        self,
        *,
        discovery_payload: str = (
            '{"event":"available_to_subscribe","tickers":["WINV26","WINZ26"]}'
        ),
        emit_trade: bool = True,
    ) -> None:
        self.discovery_payload = discovery_payload
        self.emit_trade = emit_trade
        self.on_message: Callable[[object], None] | None = None
        self.on_error: Callable[[object], None] | None = None
        self.on_close: Callable[[object, object], None] | None = None
        self.subscriptions: list[list[str]] = []
        self.unsubscriptions: list[list[str]] = []
        self.discovery_requests = 0
        self.closed = False
        self.run_options: dict[str, object] = {}

    def run(
        self,
        on_open: object | None = None,
        on_message: Callable[[object], None] | None = None,
        on_error: Callable[[object], None] | None = None,
        on_close: Callable[[object, object], None] | None = None,
        reconnect: bool = True,
        spawn_thread: bool = True,
        default_logs: bool = True,
    ) -> None:
        del on_open
        self.on_message = on_message
        self.on_error = on_error
        self.on_close = on_close
        self.run_options = {
            "reconnect": reconnect,
            "spawn_thread": spawn_thread,
            "default_logs": default_logs,
        }

    def subscribe(
        self,
        list_instruments: list[str],
        n: int | None = None,
        initial_snapshot: bool = False,
    ) -> None:
        assert n is None
        assert initial_snapshot is False
        self.subscriptions.append(list_instruments)
        assert self.on_message is not None
        instrument = list_instruments[0]
        self.on_message('{"event":"subscribed","symbol":"' + instrument + '"}')
        if self.emit_trade:
            self.on_message(
                '{"event":"trade","symbol":"'
                + instrument
                + '","time":"10:00:00:001","qty":1,"px":123456.0}'
            )

    def unsubscribe(self, list_instruments: list[str]) -> None:
        self.unsubscriptions.append(list_instruments)

    def available_to_subscribe(self) -> None:
        self.discovery_requests += 1
        assert self.on_message is not None
        self.on_message(self.discovery_payload)

    def close(self) -> None:
        self.closed = True


class FakeFactory:
    def __init__(
        self,
        *,
        discovery_payload: str = (
            '{"event":"available_to_subscribe","tickers":["WINV26","WINZ26"]}'
        ),
        emit_trade: bool = True,
    ) -> None:
        self.discovery_payload = discovery_payload
        self.emit_trade = emit_trade
        self.clients: list[FakeVendorClient] = []
        self.credentials: list[str] = []
        self.settings: list[BtgDataServicesSettings] = []

    def __call__(self, credential: str, settings: BtgDataServicesSettings) -> Any:
        client = FakeVendorClient(
            discovery_payload=self.discovery_payload,
            emit_trade=self.emit_trade,
        )
        self.clients.append(client)
        self.credentials.append(credential)
        self.settings.append(settings)
        return client


def _no_sleep(_seconds: float) -> None:
    return None


def _all_file_bytes(root: Path) -> bytes:
    return b"".join(path.read_bytes() for path in sorted(root.rglob("*")) if path.is_file())


def test_discovery_confirmation_requires_exact_symbol_in_string_list() -> None:
    payloads = [b'{"tickers":["WINV26","WINZ26"]}']
    assert capture.discovery_confirms_instrument(payloads, "WINV26") is True
    assert capture.discovery_confirms_instrument(payloads, "WINQ26") is False
    assert capture.discovery_confirms_instrument([b"not-json", *payloads], "WINV26") is True
    assert (
        capture.discovery_confirms_instrument(
            [b'{"response":{"symbols":["WINV26","WINZ26"]}}'],
            "WINV26",
        )
        is True
    )

    for invalid in ("WIN", "WING26X", "INDV26", "winv26"):
        with pytest.raises(ValueError):
            capture.discovery_confirms_instrument(payloads, invalid)


def test_discovery_scalar_echo_does_not_confirm_instrument() -> None:
    payloads = [
        b'{"requested":"WINV26","error":"not-available"}',
        b'{"message":"WINV26"}',
    ]
    assert capture.discovery_confirms_instrument(payloads, "WINV26") is False


def test_confirmed_trade_requires_trade_event_and_exact_symbol() -> None:
    assert (
        capture.is_confirmed_trade(
            b'{"event":"trade","symbol":"WINV26","qty":1,"px":123456.0}',
            "WINV26",
        )
        is True
    )
    assert (
        capture.is_confirmed_trade(
            b'{"event":"trade","symbol":"WINZ26","qty":1,"px":123456.0}',
            "WINV26",
        )
        is False
    )
    assert (
        capture.is_confirmed_trade(
            b'{"event":"subscribed","symbol":"WINV26"}',
            "WINV26",
        )
        is False
    )
    assert capture.is_confirmed_trade(b"not-json", "WINV26") is False


def test_credential_source_requires_authorized_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(capture.API_KEY_ENV, raising=False)
    with pytest.raises(RuntimeError, match=capture.API_KEY_ENV):
        capture._credential_source()

    monkeypatch.setenv(capture.API_KEY_ENV, "synthetic-read-only-key")
    assert capture._credential_source() == "synthetic-read-only-key"


def test_controlled_first_lab_uses_one_session_and_never_persists_secret(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    factory = FakeFactory()
    secret = "synthetic-read-only-key-never-persist"
    monkeypatch.setenv(capture.API_KEY_ENV, secret)
    monkeypatch.setattr(capture, "_vendor_factory", factory)
    monkeypatch.setattr(time, "sleep", _no_sleep)

    session_root = capture.run_first_lab(
        instrument="WINV26",
        capture_scope="first-lab",
        code_revision="a" * 40,
        output_root=tmp_path,
        discovery_seconds=0.01,
        capture_seconds=0.01,
    )

    assert len(factory.clients) == 1
    client = factory.clients[0]
    assert factory.credentials == [secret]
    assert len(factory.settings) == 1
    assert factory.settings[0].stream_type == "realtime"
    assert factory.settings[0].data_type == "trades"
    assert not hasattr(factory.settings[0], "instrument")

    assert client.discovery_requests == 1
    assert client.subscriptions == [["WINV26"]]
    assert client.unsubscriptions == [["WINV26"]]
    assert client.closed is True
    assert client.run_options == {
        "reconnect": False,
        "spawn_thread": False,
        "default_logs": False,
    }

    archive = session_root / "archive"
    journal = session_root / "journal"
    assert archive.is_dir()
    assert journal.is_dir()
    assert not (session_root / "session-summary.json").exists()

    records = [decode_record(path.read_bytes()) for path in archive.glob("*.json")]
    evidence = [record for record in records if isinstance(record, EvidenceRecord)]
    raw_evidence = [record.raw for record in evidence]
    assert any(b'"event":"available_to_subscribe"' in raw for raw in raw_evidence)
    assert any(
        b'"confirmation":"provider-discovery-listed-exact-match"' in raw
        for raw in raw_evidence
    )
    assert any(b'"event":"subscribed"' in raw for raw in raw_evidence)
    assert any(b'"event":"trade"' in raw for raw in raw_evidence)
    assert any(b'"confirmed_trade_frames":1' in raw for raw in raw_evidence)
    assert any(b'"other_post_subscription_frames":1' in raw for raw in raw_evidence)

    run_ids = {
        record.capture.run_id.value
        for record in evidence
        if record.capture is not None
    }
    assert len(run_ids) == 1
    assert len(list(journal.glob("*.json"))) >= 2

    persisted = _all_file_bytes(session_root)
    assert secret.encode("utf-8") not in persisted


def test_missing_discovery_confirmation_never_subscribes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    factory = FakeFactory(
        discovery_payload='{"event":"available_to_subscribe","tickers":["WINZ26"]}'
    )
    monkeypatch.setenv(capture.API_KEY_ENV, "synthetic-read-only-key")
    monkeypatch.setattr(capture, "_vendor_factory", factory)
    monkeypatch.setattr(time, "sleep", _no_sleep)

    with pytest.raises(RuntimeError, match="did not confirm"):
        capture.run_first_lab(
            instrument="WINV26",
            capture_scope="first-lab",
            code_revision="b" * 40,
            output_root=tmp_path,
            discovery_seconds=0.01,
            capture_seconds=0.01,
        )

    assert len(factory.clients) == 1
    client = factory.clients[0]
    assert client.discovery_requests == 1
    assert client.subscriptions == []
    assert client.unsubscriptions == []
    assert client.closed is True


def test_scalar_echo_discovery_never_subscribes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    factory = FakeFactory(
        discovery_payload='{"requested":"WINV26","error":"not-available"}'
    )
    monkeypatch.setenv(capture.API_KEY_ENV, "synthetic-read-only-key")
    monkeypatch.setattr(capture, "_vendor_factory", factory)
    monkeypatch.setattr(time, "sleep", _no_sleep)

    with pytest.raises(RuntimeError, match="did not confirm"):
        capture.run_first_lab(
            instrument="WINV26",
            capture_scope="first-lab",
            code_revision="e" * 40,
            output_root=tmp_path,
            discovery_seconds=0.01,
            capture_seconds=0.01,
        )

    client = factory.clients[0]
    assert client.subscriptions == []
    assert client.closed is True


def test_subscription_ack_without_confirmed_trade_is_not_success(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    factory = FakeFactory(emit_trade=False)
    monkeypatch.setenv(capture.API_KEY_ENV, "synthetic-read-only-key")
    monkeypatch.setattr(capture, "_vendor_factory", factory)
    monkeypatch.setattr(time, "sleep", _no_sleep)

    with pytest.raises(RuntimeError, match="without a confirmed trade frame"):
        capture.run_first_lab(
            instrument="WINV26",
            capture_scope="first-lab",
            code_revision="d" * 40,
            output_root=tmp_path,
            discovery_seconds=0.01,
            capture_seconds=0.01,
        )

    client = factory.clients[0]
    assert client.discovery_requests == 1
    assert client.subscriptions == [["WINV26"]]
    assert client.unsubscriptions == [["WINV26"]]
    assert client.closed is True


def test_first_lab_rejects_non_win_instrument(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="WIN contract"):
        capture.run_first_lab(
            instrument="PETR4",
            capture_scope="first-lab",
            code_revision="c" * 40,
            output_root=tmp_path,
            discovery_seconds=0.01,
            capture_seconds=0.01,
        )


def test_first_lab_rejects_unbounded_discovery_window(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="discovery_seconds"):
        capture.run_first_lab(
            instrument="WINV26",
            capture_scope="first-lab",
            code_revision="c" * 40,
            output_root=tmp_path,
            discovery_seconds=31.0,
            capture_seconds=0.01,
        )


def test_first_lab_rejects_unbounded_capture_window(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="capture_seconds"):
        capture.run_first_lab(
            instrument="WINV26",
            capture_scope="first-lab",
            code_revision="c" * 40,
            output_root=tmp_path,
            discovery_seconds=0.01,
            capture_seconds=301.0,
        )
