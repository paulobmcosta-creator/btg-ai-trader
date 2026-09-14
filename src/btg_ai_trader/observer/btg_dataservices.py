"""Read-only BTG Solutions Data Services subscription boundary for Sprint 1."""

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

BTG_DATASERVICES_PROVIDER = "btg-solutions-data-services"


class _MessageCallback(Protocol):
    def __call__(self, data: object, /) -> None: ...


class _ErrorCallback(Protocol):
    def __call__(self, error: object, /) -> None: ...


class _CloseCallback(Protocol):
    def __call__(self, status: object, message: object, /) -> None: ...


class _CredentialSource(Protocol):
    def __call__(self) -> str: ...


class _FrameSink(Protocol):
    def __call__(self, frame: RawFrame, /) -> None: ...


class _ControlSink(Protocol):
    def __call__(self, payload: bytes, /) -> None: ...


class _ErrorSink(Protocol):
    def __call__(self, error_type: str, /) -> None: ...


class _VendorClient(Protocol):
    """Only the read-only subset admitted from the official vendor client."""

    def run(
        self,
        on_open: object | None = None,
        on_message: _MessageCallback | None = None,
        on_error: _ErrorCallback | None = None,
        on_close: _CloseCallback | None = None,
        reconnect: bool = True,
        spawn_thread: bool = True,
        default_logs: bool = True,
    ) -> None: ...

    def subscribe(
        self,
        list_instruments: list[str],
        n: int | None = None,
        initial_snapshot: bool = False,
    ) -> None: ...

    def unsubscribe(self, list_instruments: list[str]) -> None: ...

    def available_to_subscribe(self) -> None: ...

    def close(self) -> None: ...


@dataclass(frozen=True, slots=True)
class BtgDataServicesSettings:
    """Connection settings independent from the point-in-time instrument decision."""

    capture_scope: str
    stream_type: str = "realtime"
    exchange: str = "b3"
    data_type: str = "trades"
    data_subtype: str = "derivatives"
    feed: str = "A"
    reconnect: bool = False

    def __post_init__(self) -> None:
        for value, name in (
            (self.capture_scope, "capture_scope"),
            (self.stream_type, "stream_type"),
            (self.exchange, "exchange"),
            (self.data_type, "data_type"),
            (self.data_subtype, "data_subtype"),
            (self.feed, "feed"),
        ):
            require_text(value, name)
        if self.stream_type not in {"realtime", "delayed"}:
            raise ValueError("stream_type must be realtime or delayed")
        if self.exchange != "b3":
            raise ValueError("Sprint 1 BTG Data Services adapter is restricted to B3")
        if self.data_type not in {"trades", "candles-1S", "candles-1M"}:
            raise ValueError("unsupported Sprint 1 market-data type")
        if self.data_subtype != "derivatives":
            raise ValueError("Sprint 1 initial BTG adapter is restricted to derivatives")
        if self.feed not in {"A", "B"}:
            raise ValueError("feed must be A or B")
        if self.reconnect is not False:
            raise ValueError("automatic vendor reconnect is disabled in Sprint 1")

    @property
    def raw_channel(self) -> RawChannel:
        if self.data_type == "trades":
            return RawChannel.TICK
        return RawChannel.CANDLE


class _ClientFactory(Protocol):
    def __call__(
        self, credential: str, settings: BtgDataServicesSettings
    ) -> _VendorClient: ...


class BtgDataServicesSubscription:
    """Narrow read-only wrapper with explicit discovery-before-subscription lifecycle."""

    __slots__ = (
        "_client",
        "_client_factory",
        "_confirmed_instrument",
        "_control_sink",
        "_credential_source",
        "_error_sink",
        "_frame_sink",
        "_settings",
        "_subscribed",
    )

    def __init__(
        self,
        settings: BtgDataServicesSettings,
        credential_source: _CredentialSource,
        frame_sink: _FrameSink,
        *,
        client_factory: _ClientFactory,
        control_sink: _ControlSink | None = None,
        error_sink: _ErrorSink | None = None,
    ) -> None:
        if not isinstance(settings, BtgDataServicesSettings):
            raise TypeError("settings must be BtgDataServicesSettings")
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
        self._client: _VendorClient | None = None
        self._confirmed_instrument: str | None = None
        self._subscribed = False

    def describe_capabilities(self) -> ProviderCapabilities:
        ticks = (
            CapabilitySupport.SUPPORTED
            if self._settings.raw_channel is RawChannel.TICK
            else CapabilitySupport.UNSUPPORTED
        )
        candles = (
            CapabilitySupport.SUPPORTED
            if self._settings.raw_channel is RawChannel.CANDLE
            else CapabilitySupport.UNSUPPORTED
        )
        return ProviderCapabilities(
            provider=BTG_DATASERVICES_PROVIDER,
            capture_scope=self._settings.capture_scope,
            ticks=ticks,
            candles=candles,
            source_sequence=CapabilitySupport.UNKNOWN,
            timestamp_resolution=MissingReason.UNKNOWN,
            fidelity=FidelityMode.OBSERVATION_FAITHFUL,
        )

    def _on_message(self, data: object) -> None:
        if type(data) is not str:
            raise TypeError("BTG Data Services callback must provide a text WebSocket payload")
        payload = data.encode("utf-8")
        if not self._subscribed:
            if self._control_sink is None:
                raise RuntimeError("control message received without configured control_sink")
            self._control_sink(payload)
            return
        instrument = self._confirmed_instrument
        if instrument is None:
            raise RuntimeError("subscribed state requires a confirmed instrument")
        self._frame_sink(
            RawFrame(
                payload=payload,
                reference=ProviderInstrumentRef(
                    BTG_DATASERVICES_PROVIDER,
                    self._settings.capture_scope,
                    instrument,
                ),
                channel=self._settings.raw_channel,
            )
        )

    def _on_error(self, error: object) -> None:
        if self._error_sink is not None:
            self._error_sink(type(error).__name__)

    def _on_close(self, _status: object, _message: object) -> None:
        if self._error_sink is not None:
            self._error_sink("connection-closed")

    def start(self) -> None:
        """Connect without selecting or subscribing an instrument."""
        if self._client is not None:
            raise RuntimeError("subscription session is already started")
        credential = self._credential_source()
        require_text(credential, "credential")
        client = self._client_factory(credential, self._settings)
        self._client = client
        client.run(
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close,
            reconnect=False,
            spawn_thread=False,
            default_logs=False,
        )

    def request_available_instruments(self) -> None:
        if self._subscribed:
            raise RuntimeError("instrument discovery is only allowed before subscription")
        if self._control_sink is None:
            raise RuntimeError("instrument discovery requires a control_sink")
        self._require_client().available_to_subscribe()

    def subscribe_confirmed(self, instrument: str) -> None:
        """Subscribe only after point-in-time confirmation of ``instrument`` by the caller."""
        client = self._require_client()
        if self._subscribed or self._confirmed_instrument is not None:
            raise RuntimeError("instrument is already subscribed")
        require_text(instrument, "instrument")
        self._confirmed_instrument = instrument
        self._subscribed = True
        try:
            client.subscribe([instrument], initial_snapshot=False)
        except Exception:
            self._subscribed = False
            self._confirmed_instrument = None
            raise

    def close(self) -> None:
        client = self._require_client()
        instrument = self._confirmed_instrument
        try:
            if self._subscribed and instrument is not None:
                client.unsubscribe([instrument])
        finally:
            client.close()
            self._client = None
            self._confirmed_instrument = None
            self._subscribed = False

    def _require_client(self) -> _VendorClient:
        if self._client is None:
            raise RuntimeError("subscription session is not started")
        return self._client
