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
    """Explicit single-instrument subscription settings; DD-68 supplies the instrument later."""

    capture_scope: str
    instrument: str
    stream_type: str = "realtime"
    exchange: str = "b3"
    data_type: str = "trades"
    data_subtype: str = "derivatives"
    feed: str = "A"
    reconnect: bool = False

    def __post_init__(self) -> None:
        for value, name in (
            (self.capture_scope, "capture_scope"),
            (self.instrument, "instrument"),
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

    @property
    def reference(self) -> ProviderInstrumentRef:
        return ProviderInstrumentRef(
            BTG_DATASERVICES_PROVIDER,
            self.capture_scope,
            self.instrument,
        )


class _ClientFactory(Protocol):
    def __call__(
        self, credential: str, settings: BtgDataServicesSettings
    ) -> _VendorClient: ...


class BtgDataServicesSubscription:
    """Narrow read-only wrapper; no credential is stored by the BTG AI Trader adapter itself."""

    __slots__ = (
        "_client",
        "_client_factory",
        "_credential_source",
        "_error_sink",
        "_frame_sink",
        "_settings",
    )

    def __init__(
        self,
        settings: BtgDataServicesSettings,
        credential_source: _CredentialSource,
        frame_sink: _FrameSink,
        *,
        client_factory: _ClientFactory,
        error_sink: _ErrorSink | None = None,
    ) -> None:
        if not isinstance(settings, BtgDataServicesSettings):
            raise TypeError("settings must be BtgDataServicesSettings")
        if not callable(credential_source) or not callable(frame_sink):
            raise TypeError("credential_source and frame_sink must be callable")
        if error_sink is not None and not callable(error_sink):
            raise TypeError("error_sink must be callable")
        if not callable(client_factory):
            raise TypeError("client_factory must be callable")
        self._settings = settings
        self._credential_source = credential_source
        self._frame_sink = frame_sink
        self._error_sink = error_sink
        self._client_factory = client_factory
        self._client: _VendorClient | None = None

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
        self._frame_sink(
            RawFrame(
                payload=data.encode("utf-8"),
                reference=self._settings.reference,
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
        if self._client is not None:
            raise RuntimeError("subscription is already started")
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
        client.subscribe([self._settings.instrument], initial_snapshot=False)

    def request_available_instruments(self) -> None:
        self._require_client().available_to_subscribe()

    def close(self) -> None:
        client = self._require_client()
        try:
            client.unsubscribe([self._settings.instrument])
        finally:
            client.close()
            self._client = None

    def _require_client(self) -> _VendorClient:
        if self._client is None:
            raise RuntimeError("subscription is not started")
        return self._client
