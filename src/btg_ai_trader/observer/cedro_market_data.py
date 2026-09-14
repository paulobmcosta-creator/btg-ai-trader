"""Read-only Cedro Market Data boundary for the zero-cost Sprint 1 qualification."""

import re
from dataclasses import dataclass
from typing import Protocol

from btg_ai_trader.observer.identity import ProviderInstrumentRef
from btg_ai_trader.observer.provider import (
    CapabilitySupport,
    FidelityMode,
    ProviderCapabilities,
)
from btg_ai_trader.observer.raw_source import RawChannel, RawFrame
from btg_ai_trader.observer.values import MissingReason, require_text

CEDRO_MARKET_DATA_PROVIDER = "cedro-market-data"
_WIN_CONTRACT = re.compile(r"WIN[A-Z][0-9]{2}")


class _MessageCallback(Protocol):
    def __call__(self, data: object, /) -> None: ...


class _ErrorCallback(Protocol):
    def __call__(self, error: object, /) -> None: ...


class _CloseCallback(Protocol):
    def __call__(self, status: object, message: object, /) -> None: ...


class _CredentialSource(Protocol):
    def __call__(self) -> tuple[str, str]: ...


class _FrameSink(Protocol):
    def __call__(self, frame: RawFrame, /) -> None: ...


class _ControlSink(Protocol):
    def __call__(self, payload: bytes, /) -> None: ...


class _ErrorSink(Protocol):
    def __call__(self, error_type: str, /) -> None: ...


class _MarketDataClient(Protocol):
    """Only the passive Cedro Market Data operations admitted by Sprint 1.

    A concrete wire binding MUST classify vendor payloads before invoking these
    callbacks: control/discovery messages go to ``on_control`` and executed-trade
    payloads go to ``on_trade``. The local boundary never infers one from the other.
    """

    def connect(
        self,
        on_control: _MessageCallback,
        on_trade: _MessageCallback,
        on_error: _ErrorCallback | None = None,
        on_close: _CloseCallback | None = None,
        *,
        reconnect: bool = False,
    ) -> None: ...

    def request_instrument_confirmation(self, instrument: str) -> None: ...

    def subscribe_trades(self, instrument: str) -> None: ...

    def unsubscribe(self, instrument: str) -> None: ...

    def close(self) -> None: ...


@dataclass(frozen=True, slots=True)
class CedroMarketDataSettings:
    """Bounded first-lab settings; the concrete instrument is resolved at runtime."""

    capture_scope: str
    stream_type: str = "realtime"
    market: str = "bmf"
    data_type: str = "trades"
    reconnect: bool = False

    def __post_init__(self) -> None:
        for value, name in (
            (self.capture_scope, "capture_scope"),
            (self.stream_type, "stream_type"),
            (self.market, "market"),
            (self.data_type, "data_type"),
        ):
            require_text(value, name)
        if self.stream_type != "realtime":
            raise ValueError("Sprint 1 Cedro qualification requires realtime data")
        if self.market != "bmf":
            raise ValueError("Sprint 1 Cedro qualification is restricted to BM&F futures")
        if self.data_type != "trades":
            raise ValueError("Sprint 1 Cedro qualification requires executed trades")
        if self.reconnect is not False:
            raise ValueError("automatic reconnect is disabled for the first Cedro lab")


class _ClientFactory(Protocol):
    def __call__(
        self,
        username: str,
        password: str,
        settings: CedroMarketDataSettings,
    ) -> _MarketDataClient: ...


class CedroMarketDataSubscription:
    """Fail-closed read-only wrapper with adjudicated confirmation before subscription."""

    __slots__ = (
        "_candidate_instrument",
        "_client",
        "_client_factory",
        "_confirmation_recorded",
        "_confirmation_requested",
        "_confirmed_instrument",
        "_control_sink",
        "_credential_source",
        "_error_sink",
        "_expected_close",
        "_frame_sink",
        "_settings",
        "_subscribed",
    )

    def __init__(
        self,
        settings: CedroMarketDataSettings,
        credential_source: _CredentialSource,
        frame_sink: _FrameSink,
        *,
        client_factory: _ClientFactory,
        control_sink: _ControlSink | None = None,
        error_sink: _ErrorSink | None = None,
    ) -> None:
        if not isinstance(settings, CedroMarketDataSettings):
            raise TypeError("settings must be CedroMarketDataSettings")
        if not callable(credential_source) or not callable(frame_sink):
            raise TypeError("credential_source and frame_sink must be callable")
        if control_sink is not None and not callable(control_sink):
            raise TypeError("control_sink must be callable")
        if error_sink is not None and not callable(error_sink):
            raise TypeError("error_sink must be callable")
        if not callable(client_factory):
            raise TypeError("client_factory must be callable")
        self._settings = settings
        self._credential_source = credential_source
        self._frame_sink = frame_sink
        self._control_sink = control_sink
        self._error_sink = error_sink
        self._client_factory = client_factory
        self._client: _MarketDataClient | None = None
        self._candidate_instrument: str | None = None
        self._confirmed_instrument: str | None = None
        self._confirmation_requested = False
        self._confirmation_recorded = False
        self._subscribed = False
        self._expected_close = False

    def describe_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            provider=CEDRO_MARKET_DATA_PROVIDER,
            capture_scope=self._settings.capture_scope,
            ticks=CapabilitySupport.SUPPORTED,
            candles=CapabilitySupport.UNSUPPORTED,
            source_sequence=CapabilitySupport.UNKNOWN,
            timestamp_resolution=MissingReason.UNKNOWN,
            fidelity=FidelityMode.OBSERVATION_FAITHFUL,
        )

    def _on_control(self, data: object) -> None:
        if type(data) is not str:
            raise TypeError("Cedro Market Data control callback must provide a text payload")
        if self._control_sink is None:
            raise RuntimeError("control message received without configured control_sink")
        self._control_sink(data.encode("utf-8"))

    def _on_trade(self, data: object) -> None:
        if type(data) is not str:
            raise TypeError("Cedro Market Data trade callback must provide a text payload")
        if not self._subscribed:
            raise RuntimeError("trade message received before confirmed subscription")
        instrument = self._confirmed_instrument
        if instrument is None:
            raise RuntimeError("subscribed state requires a confirmed instrument")
        self._frame_sink(
            RawFrame(
                payload=data.encode("utf-8"),
                reference=ProviderInstrumentRef(
                    CEDRO_MARKET_DATA_PROVIDER,
                    self._settings.capture_scope,
                    instrument,
                ),
                channel=RawChannel.TICK,
            )
        )

    def _on_error(self, error: object) -> None:
        if self._error_sink is not None:
            self._error_sink(type(error).__name__)

    def _on_close(self, _status: object, _message: object) -> None:
        if not self._expected_close and self._error_sink is not None:
            self._error_sink("connection-closed")

    def start(self) -> None:
        """Authenticate/connect without selecting or subscribing a concrete contract."""
        if self._client is not None:
            raise RuntimeError("subscription session is already started")
        credentials = self._credential_source()
        if type(credentials) is not tuple or len(credentials) != 2:
            raise TypeError("credential_source must return exactly username and password")
        username, password = credentials
        require_text(username, "username")
        require_text(password, "password")
        client = self._client_factory(username, password, self._settings)
        self._expected_close = False
        self._candidate_instrument = None
        self._confirmed_instrument = None
        self._confirmation_requested = False
        self._confirmation_recorded = False
        self._subscribed = False
        self._client = client
        try:
            client.connect(
                self._on_control,
                self._on_trade,
                self._on_error,
                self._on_close,
                reconnect=False,
            )
        except Exception:
            self._expected_close = True
            try:
                client.close()
            finally:
                self._client = None
            raise

    def request_instrument_confirmation(self, instrument: str) -> None:
        """Ask the provider to confirm one explicit WIN candidate before subscription."""
        client = self._require_client()
        if self._subscribed:
            raise RuntimeError("instrument confirmation is only allowed before subscription")
        if self._confirmation_requested:
            raise RuntimeError("instrument confirmation was already requested")
        if self._control_sink is None:
            raise RuntimeError("instrument confirmation requires a control_sink")
        self._require_win_contract(instrument)
        client.request_instrument_confirmation(instrument)
        self._candidate_instrument = instrument
        self._confirmation_requested = True

    def record_provider_confirmation(self, instrument: str) -> None:
        """Record caller adjudication of preserved provider confirmation evidence.

        The caller is responsible for parsing the raw control evidence using the
        concrete, reviewed Cedro wire protocol. This method only binds that
        adjudication to the exact candidate previously requested.
        """
        self._require_client()
        if not self._confirmation_requested or self._candidate_instrument is None:
            raise RuntimeError("confirmation must be requested before it can be recorded")
        if self._confirmation_recorded:
            raise RuntimeError("provider confirmation was already recorded")
        self._require_win_contract(instrument)
        if instrument != self._candidate_instrument:
            raise ValueError("provider confirmation must match the requested candidate")
        self._confirmation_recorded = True

    def subscribe_confirmed(self, instrument: str) -> None:
        """Subscribe only after exact provider confirmation evidence was adjudicated."""
        client = self._require_client()
        if not self._confirmation_recorded or self._candidate_instrument is None:
            raise RuntimeError("provider confirmation must be recorded before subscription")
        if self._subscribed or self._confirmed_instrument is not None:
            raise RuntimeError("instrument is already subscribed")
        self._require_win_contract(instrument)
        if instrument != self._candidate_instrument:
            raise ValueError("confirmed instrument must exactly match the requested candidate")
        self._confirmed_instrument = instrument
        self._subscribed = True
        try:
            client.subscribe_trades(instrument)
        except Exception:
            self._confirmed_instrument = None
            self._subscribed = False
            raise

    def close(self) -> None:
        client = self._require_client()
        instrument = self._confirmed_instrument
        self._expected_close = True
        try:
            try:
                if self._subscribed and instrument is not None:
                    client.unsubscribe(instrument)
            finally:
                client.close()
        finally:
            self._client = None
            self._candidate_instrument = None
            self._confirmed_instrument = None
            self._confirmation_requested = False
            self._confirmation_recorded = False
            self._subscribed = False

    @staticmethod
    def _require_win_contract(instrument: str) -> None:
        require_text(instrument, "instrument")
        if _WIN_CONTRACT.fullmatch(instrument) is None:
            raise ValueError("instrument must be one explicit concrete WIN contract")

    def _require_client(self) -> _MarketDataClient:
        if self._client is None:
            raise RuntimeError("subscription session is not started")
        return self._client
