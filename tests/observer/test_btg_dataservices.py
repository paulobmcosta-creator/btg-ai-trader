"""Contract tests for the narrow BTG Solutions Data Services Sprint 1 boundary."""

from collections.abc import Callable
from datetime import timedelta
from typing import Any

import pytest

from btg_ai_trader.observer.btg_dataservices import (
    BTG_DATASERVICES_PROVIDER,
    BtgDataServicesSettings,
    BtgDataServicesSubscription,
)
from btg_ai_trader.observer.provider import CapabilitySupport, FidelityMode
from btg_ai_trader.observer.raw_source import RawChannel, RawFrame
from btg_ai_trader.observer.values import MissingReason


class FakeVendorClient:
    def __init__(self) -> None:
        self.on_message: Callable[..., None] | None = None
        self.on_error: Callable[..., None] | None = None
        self.on_close: Callable[..., None] | None = None
        self.run_options: dict[str, object] = {}
        self.subscriptions: list[list[str]] = []
        self.unsubscriptions: list[list[str]] = []
        self.discovery_requests = 0
        self.closed = False

    def run(
        self,
        on_open: Callable[..., None] | None = None,
        on_message: Callable[..., None] | None = None,
        on_error: Callable[..., None] | None = None,
        on_close: Callable[..., None] | None = None,
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

    def unsubscribe(self, list_instruments: list[str]) -> None:
        self.unsubscriptions.append(list_instruments)

    def available_to_subscribe(self) -> None:
        self.discovery_requests += 1

    def close(self) -> None:
        self.closed = True

    def emit(self, data: object) -> None:
        assert self.on_message is not None
        self.on_message(data)

    def fail(self, error: object) -> None:
        assert self.on_error is not None
        self.on_error(error)


class FakeFactory:
    def __init__(self, client: FakeVendorClient) -> None:
        self.client = client
        self.credentials: list[str] = []
        self.settings: list[BtgDataServicesSettings] = []

    def __call__(self, credential: str, settings: BtgDataServicesSettings) -> Any:
        self.credentials.append(credential)
        self.settings.append(settings)
        return self.client


def _settings(**overrides: Any) -> BtgDataServicesSettings:
    values: dict[str, object] = {
        "capture_scope": "lab-a",
        "instrument": "TEST-DERIV-1",
    }
    values.update(overrides)
    return BtgDataServicesSettings(**values)  # type: ignore[arg-type]


def test_subscription_preserves_websocket_text_as_raw_utf8_before_domain_decode() -> None:
    client = FakeVendorClient()
    factory = FakeFactory(client)
    frames: list[RawFrame] = []
    credential_reads = 0

    def credential_source() -> str:
        nonlocal credential_reads
        credential_reads += 1
        return "test-only-placeholder"

    subscription = BtgDataServicesSubscription(
        _settings(),
        credential_source,
        frames.append,
        client_factory=factory,
    )
    subscription.start()
    raw = '{"event":"trade","symbol":"TEST-DERIV-1","px":123456.0}'
    client.emit(raw)

    assert credential_reads == 1
    assert factory.credentials == ["test-only-placeholder"]
    assert factory.settings == [_settings()]
    assert client.run_options == {
        "reconnect": False,
        "spawn_thread": False,
        "default_logs": False,
    }
    assert client.subscriptions == [["TEST-DERIV-1"]]
    assert frames == [
        RawFrame(
            raw.encode("utf-8"),
            _settings().reference,
            RawChannel.TICK,
        )
    ]


def test_adapter_exposes_passive_discovery_and_lifecycle_only() -> None:
    client = FakeVendorClient()
    subscription = BtgDataServicesSubscription(
        _settings(),
        lambda: "test-only-placeholder",
        lambda _frame: None,
        client_factory=FakeFactory(client),
    )

    forbidden = {
        "order_send",
        "order_check",
        "order_calc_margin",
        "trade",
        "execute",
        "account_info",
        "positions_get",
    }
    assert forbidden.isdisjoint(dir(subscription))

    subscription.start()
    subscription.request_available_instruments()
    subscription.close()

    assert client.discovery_requests == 1
    assert client.unsubscriptions == [["TEST-DERIV-1"]]
    assert client.closed is True
    with pytest.raises(RuntimeError, match="not started"):
        subscription.request_available_instruments()


def test_capabilities_are_scoped_and_do_not_invent_sequence_or_resolution() -> None:
    trade = BtgDataServicesSubscription(
        _settings(),
        lambda: "test-only-placeholder",
        lambda _frame: None,
        client_factory=FakeFactory(FakeVendorClient()),
    ).describe_capabilities()
    candle = BtgDataServicesSubscription(
        _settings(data_type="candles-1M"),
        lambda: "test-only-placeholder",
        lambda _frame: None,
        client_factory=FakeFactory(FakeVendorClient()),
    ).describe_capabilities()

    assert trade.provider == BTG_DATASERVICES_PROVIDER
    assert trade.capture_scope == "lab-a"
    assert trade.ticks is CapabilitySupport.SUPPORTED
    assert trade.candles is CapabilitySupport.UNSUPPORTED
    assert candle.ticks is CapabilitySupport.UNSUPPORTED
    assert candle.candles is CapabilitySupport.SUPPORTED
    assert trade.source_sequence is CapabilitySupport.UNKNOWN
    assert trade.timestamp_resolution is MissingReason.UNKNOWN
    assert trade.fidelity is FidelityMode.OBSERVATION_FAITHFUL


def test_settings_fail_closed_outside_authorized_b3_derivatives_surface() -> None:
    for overrides in (
        {"stream_type": "other"},
        {"exchange": "bmv"},
        {"data_type": "books"},
        {"data_subtype": "stocks"},
        {"feed": "C"},
        {"reconnect": True},
        {"reconnect": 1},
    ):
        with pytest.raises(ValueError):
            _settings(**overrides)


def test_callback_rejects_non_text_payload_without_optimistic_serialization() -> None:
    client = FakeVendorClient()
    subscription = BtgDataServicesSubscription(
        _settings(),
        lambda: "test-only-placeholder",
        lambda _frame: None,
        client_factory=FakeFactory(client),
    )
    subscription.start()
    with pytest.raises(TypeError, match="text WebSocket payload"):
        client.emit(b"already-bytes")


def test_error_sink_receives_only_exception_type_not_message() -> None:
    client = FakeVendorClient()
    errors: list[str] = []
    subscription = BtgDataServicesSubscription(
        _settings(),
        lambda: "test-only-placeholder",
        lambda _frame: None,
        error_sink=errors.append,
        client_factory=FakeFactory(client),
    )
    subscription.start()
    client.fail(RuntimeError("sensitive-provider-detail"))
    assert errors == ["RuntimeError"]


def test_double_start_and_close_before_start_fail_closed() -> None:
    subscription = BtgDataServicesSubscription(
        _settings(),
        lambda: "test-only-placeholder",
        lambda _frame: None,
        client_factory=FakeFactory(FakeVendorClient()),
    )
    with pytest.raises(RuntimeError, match="not started"):
        subscription.close()
    subscription.start()
    with pytest.raises(RuntimeError, match="already started"):
        subscription.start()


def test_settings_keep_no_latency_or_timestamp_claim_until_measured() -> None:
    capabilities = BtgDataServicesSubscription(
        _settings(),
        lambda: "test-only-placeholder",
        lambda _frame: None,
        client_factory=FakeFactory(FakeVendorClient()),
    ).describe_capabilities()
    assert capabilities.timestamp_resolution is MissingReason.UNKNOWN
    assert capabilities.timestamp_resolution != timedelta(microseconds=1)
