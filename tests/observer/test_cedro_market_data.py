"""Offline contract tests for the narrow Cedro Market Data Sprint 1 boundary."""

from collections.abc import Callable
from typing import Any

import pytest

from btg_ai_trader.observer.cedro_market_data import (
    CEDRO_MARKET_DATA_PROVIDER,
    CedroMarketDataSettings,
    CedroMarketDataSubscription,
)
from btg_ai_trader.observer.identity import ProviderInstrumentRef
from btg_ai_trader.observer.provider import CapabilitySupport, FidelityMode
from btg_ai_trader.observer.raw_source import RawChannel, RawFrame
from btg_ai_trader.observer.values import MissingReason

CANDIDATE = "WINV26"


class FakeMarketDataClient:
    def __init__(self) -> None:
        self.on_message: Callable[..., None] | None = None
        self.on_error: Callable[..., None] | None = None
        self.on_close: Callable[..., None] | None = None
        self.reconnect: bool | None = None
        self.confirmation_requests: list[str] = []
        self.subscriptions: list[str] = []
        self.unsubscriptions: list[str] = []
        self.closed = False

    def connect(
        self,
        on_message: Callable[..., None],
        on_error: Callable[..., None] | None = None,
        on_close: Callable[..., None] | None = None,
        *,
        reconnect: bool = False,
    ) -> None:
        self.on_message = on_message
        self.on_error = on_error
        self.on_close = on_close
        self.reconnect = reconnect

    def request_instrument_confirmation(self, instrument: str) -> None:
        self.confirmation_requests.append(instrument)

    def subscribe_trades(self, instrument: str) -> None:
        self.subscriptions.append(instrument)

    def unsubscribe(self, instrument: str) -> None:
        self.unsubscriptions.append(instrument)

    def close(self) -> None:
        self.closed = True
        if self.on_close is not None:
            self.on_close(1000, "normal-close")

    def emit(self, data: object) -> None:
        assert self.on_message is not None
        self.on_message(data)

    def fail(self, error: object) -> None:
        assert self.on_error is not None
        self.on_error(error)

    def disconnect(self) -> None:
        assert self.on_close is not None
        self.on_close(1006, "unexpected-disconnect")


class FailingConnectClient(FakeMarketDataClient):
    def connect(
        self,
        on_message: Callable[..., None],
        on_error: Callable[..., None] | None = None,
        on_close: Callable[..., None] | None = None,
        *,
        reconnect: bool = False,
    ) -> None:
        super().connect(on_message, on_error, on_close, reconnect=reconnect)
        raise RuntimeError("synthetic connect failure")


class FakeFactory:
    def __init__(self, client: FakeMarketDataClient) -> None:
        self.client = client
        self.credentials: list[tuple[str, str]] = []
        self.settings: list[CedroMarketDataSettings] = []

    def __call__(
        self,
        username: str,
        password: str,
        settings: CedroMarketDataSettings,
    ) -> Any:
        self.credentials.append((username, password))
        self.settings.append(settings)
        return self.client


def _settings(**overrides: Any) -> CedroMarketDataSettings:
    values: dict[str, object] = {"capture_scope": "cedro-lab"}
    values.update(overrides)
    return CedroMarketDataSettings(**values)  # type: ignore[arg-type]


def _subscription(
    client: FakeMarketDataClient,
    *,
    control_sink: Callable[[bytes], None] | None = None,
    error_sink: Callable[[str], None] | None = None,
) -> CedroMarketDataSubscription:
    return CedroMarketDataSubscription(
        _settings(),
        lambda: ("fixture-user", "fixture-secret"),
        lambda _frame: None,
        client_factory=FakeFactory(client),
        control_sink=control_sink,
        error_sink=error_sink,
    )


def test_first_lab_settings_are_fixed_to_realtime_bmf_trades() -> None:
    settings = _settings()
    assert settings.stream_type == "realtime"
    assert settings.market == "bmf"
    assert settings.data_type == "trades"
    assert settings.reconnect is False
    assert not hasattr(settings, "instrument")


def test_settings_fail_closed_outside_zero_cost_first_lab_profile() -> None:
    for overrides in (
        {"stream_type": "delayed"},
        {"market": "bovespa"},
        {"data_type": "quotes"},
        {"reconnect": True},
        {"reconnect": 1},
    ):
        with pytest.raises(ValueError):
            _settings(**overrides)


def test_start_reads_credentials_once_and_does_not_store_them_on_adapter() -> None:
    client = FakeMarketDataClient()
    factory = FakeFactory(client)
    reads = 0

    def credential_source() -> tuple[str, str]:
        nonlocal reads
        reads += 1
        return ("fixture-user", "fixture-secret")

    subscription = CedroMarketDataSubscription(
        _settings(),
        credential_source,
        lambda _frame: None,
        client_factory=factory,
        control_sink=lambda _payload: None,
    )
    subscription.start()

    assert reads == 1
    assert factory.credentials == [("fixture-user", "fixture-secret")]
    assert factory.settings == [_settings()]
    assert client.reconnect is False
    assert not hasattr(subscription, "username")
    assert not hasattr(subscription, "password")
    assert not hasattr(subscription, "session_cookie")


def test_candidate_confirmation_precedes_same_symbol_trade_subscription() -> None:
    client = FakeMarketDataClient()
    factory = FakeFactory(client)
    controls: list[bytes] = []
    frames: list[RawFrame] = []
    subscription = CedroMarketDataSubscription(
        _settings(),
        lambda: ("fixture-user", "fixture-secret"),
        frames.append,
        client_factory=factory,
        control_sink=controls.append,
    )

    subscription.start()
    assert client.subscriptions == []

    subscription.request_instrument_confirmation(CANDIDATE)
    confirmation = '{"symbol":"WINV26","market":"BMF","status":"available"}'
    client.emit(confirmation)

    assert client.confirmation_requests == [CANDIDATE]
    assert controls == [confirmation.encode("utf-8")]
    assert frames == []

    subscription.subscribe_confirmed(CANDIDATE)
    trade = '{"event":"trade","symbol":"WINV26","price":123456.0}'
    client.emit(trade)

    assert client.subscriptions == [CANDIDATE]
    assert frames == [
        RawFrame(
            trade.encode("utf-8"),
            ProviderInstrumentRef(
                CEDRO_MARKET_DATA_PROVIDER,
                "cedro-lab",
                CANDIDATE,
            ),
            RawChannel.TICK,
        )
    ]


def test_subscription_is_impossible_before_confirmation_request() -> None:
    client = FakeMarketDataClient()
    subscription = _subscription(client, control_sink=lambda _payload: None)
    subscription.start()

    with pytest.raises(RuntimeError, match="confirmation must be requested"):
        subscription.subscribe_confirmed(CANDIDATE)

    assert client.subscriptions == []


def test_subscription_rejects_symbol_different_from_confirmed_candidate() -> None:
    client = FakeMarketDataClient()
    subscription = _subscription(client, control_sink=lambda _payload: None)
    subscription.start()
    subscription.request_instrument_confirmation(CANDIDATE)

    with pytest.raises(ValueError, match="exactly match"):
        subscription.subscribe_confirmed("WINZ26")

    assert client.subscriptions == []


def test_confirmation_is_single_shot_and_requires_control_sink() -> None:
    without_sink_client = FakeMarketDataClient()
    without_sink = _subscription(without_sink_client)
    without_sink.start()
    with pytest.raises(RuntimeError, match="requires a control_sink"):
        without_sink.request_instrument_confirmation(CANDIDATE)
    assert without_sink_client.confirmation_requests == []

    client = FakeMarketDataClient()
    subscription = _subscription(client, control_sink=lambda _payload: None)
    subscription.start()
    subscription.request_instrument_confirmation(CANDIDATE)
    with pytest.raises(RuntimeError, match="already requested"):
        subscription.request_instrument_confirmation(CANDIDATE)
    assert client.confirmation_requests == [CANDIDATE]


def test_only_concrete_win_contracts_can_enter_confirmation_boundary() -> None:
    client = FakeMarketDataClient()
    subscription = _subscription(client, control_sink=lambda _payload: None)
    subscription.start()

    for invalid in ("WIN", "WINV2026", "WDOU26", "PETR4", " winv26 "):
        with pytest.raises(ValueError):
            subscription.request_instrument_confirmation(invalid)
    assert client.confirmation_requests == []


def test_adapter_public_surface_contains_no_trading_or_account_operations() -> None:
    subscription = _subscription(FakeMarketDataClient())
    names = {name.lower() for name in dir(subscription)}
    forbidden = {
        "send_new_order",
        "edit_order",
        "cancel_order",
        "brokerservicelogin",
        "user_identifier",
        "account_info",
        "positions_get",
        "allocate_guarantee",
    }
    assert names.isdisjoint(forbidden)


def test_capabilities_do_not_invent_candles_sequence_or_timestamp_resolution() -> None:
    capabilities = _subscription(FakeMarketDataClient()).describe_capabilities()
    assert capabilities.provider == CEDRO_MARKET_DATA_PROVIDER
    assert capabilities.capture_scope == "cedro-lab"
    assert capabilities.ticks is CapabilitySupport.SUPPORTED
    assert capabilities.candles is CapabilitySupport.UNSUPPORTED
    assert capabilities.source_sequence is CapabilitySupport.UNKNOWN
    assert capabilities.timestamp_resolution is MissingReason.UNKNOWN
    assert capabilities.fidelity is FidelityMode.OBSERVATION_FAITHFUL


def test_callback_rejects_non_text_payload_without_optimistic_serialization() -> None:
    client = FakeMarketDataClient()
    subscription = _subscription(client, control_sink=lambda _payload: None)
    subscription.start()
    with pytest.raises(TypeError, match="text payload"):
        client.emit(b"already-bytes")


def test_unsolicited_control_message_without_sink_fails_closed() -> None:
    client = FakeMarketDataClient()
    subscription = _subscription(client)
    subscription.start()
    with pytest.raises(RuntimeError, match="control message received"):
        client.emit('{"event":"control"}')


def test_error_sink_receives_type_only_and_close_semantics_are_explicit() -> None:
    client = FakeMarketDataClient()
    errors: list[str] = []
    subscription = _subscription(client, error_sink=errors.append)
    subscription.start()
    client.fail(RuntimeError("sensitive-provider-detail"))
    client.disconnect()
    assert errors == ["RuntimeError", "connection-closed"]

    subscription.close()
    assert errors == ["RuntimeError", "connection-closed"]


def test_close_unsubscribes_only_after_confirmed_subscription() -> None:
    client = FakeMarketDataClient()
    subscription = _subscription(client, control_sink=lambda _payload: None)
    subscription.start()
    subscription.request_instrument_confirmation(CANDIDATE)
    subscription.subscribe_confirmed(CANDIDATE)
    subscription.close()

    assert client.unsubscriptions == [CANDIDATE]
    assert client.closed is True


def test_failed_start_closes_client_and_clears_session_state() -> None:
    client = FailingConnectClient()
    subscription = _subscription(client)

    with pytest.raises(RuntimeError, match="synthetic connect failure"):
        subscription.start()

    assert client.closed is True
    with pytest.raises(RuntimeError, match="not started"):
        subscription.request_instrument_confirmation(CANDIDATE)


def test_invalid_credential_shape_fails_before_client_creation() -> None:
    client = FakeMarketDataClient()
    factory = FakeFactory(client)
    subscription = CedroMarketDataSubscription(
        _settings(),
        lambda: ("only-one",),  # type: ignore[arg-type]
        lambda _frame: None,
        client_factory=factory,
    )

    with pytest.raises(TypeError, match="exactly username and password"):
        subscription.start()
    assert factory.credentials == []


def test_close_before_start_and_double_start_fail_closed() -> None:
    subscription = _subscription(FakeMarketDataClient())
    with pytest.raises(RuntimeError, match="not started"):
        subscription.close()
    subscription.start()
    with pytest.raises(RuntimeError, match="already started"):
        subscription.start()
