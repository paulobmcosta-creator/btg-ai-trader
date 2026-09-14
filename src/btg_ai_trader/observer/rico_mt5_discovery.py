"""Passive parsing of Rico/MT5 symbol-discovery snapshots; no terminal control API."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO

from btg_ai_trader.observer.values import require_text


class DiscoveryContinuityError(RuntimeError):
    """The discovery transport no longer preserves the consumed append-only prefix."""


class DiscoveryProtocolError(RuntimeError):
    """A complete discovery snapshot violates the bridge protocol."""


@dataclass(frozen=True, slots=True)
class RicoMt5DiscoveredSymbol:
    """A provider symbol name observed without creating a canonical instrument mapping."""

    symbol: str

    def __post_init__(self) -> None:
        require_text(self.symbol, "symbol")


@dataclass(frozen=True, slots=True)
class RicoMt5DiscoverySnapshot:
    """One immutable server-symbol enumeration preserving ambiguity and uncertainty."""

    snapshot_id: str
    prefix: str
    server_symbol_total: int
    prefix_matches: int
    excluded_custom: int
    prefix_errors: int
    enumeration_errors: int
    symbols: tuple[RicoMt5DiscoveredSymbol, ...]

    def __post_init__(self) -> None:
        require_text(self.snapshot_id, "snapshot_id")
        if not isinstance(self.prefix, str):
            raise TypeError("prefix must be str")
        for name in (
            "server_symbol_total",
            "prefix_matches",
            "excluded_custom",
            "prefix_errors",
            "enumeration_errors",
        ):
            value = getattr(self, name)
            if type(value) is not int or value < 0:
                raise ValueError(f"{name} must be an explicit non-negative integer")
        if type(self.symbols) is not tuple or any(
            not isinstance(item, RicoMt5DiscoveredSymbol) for item in self.symbols
        ):
            raise ValueError("symbols must be an immutable tuple of discovered symbols")
        accounted = len(self.symbols) + self.excluded_custom + self.prefix_errors
        if self.prefix_matches != accounted:
            raise ValueError("prefix match accounting does not reconcile")
        if self.prefix_matches + self.enumeration_errors > self.server_symbol_total:
            raise ValueError("server symbol accounting does not reconcile")
        names = tuple(item.symbol for item in self.symbols)
        if len(names) != len(set(names)):
            raise ValueError("discovery snapshot contains duplicate provider symbols")
        if self.prefix and any(not name.startswith(self.prefix) for name in names):
            raise ValueError("discovered symbol falls outside configured prefix")

    @property
    def enumeration_complete(self) -> bool:
        return self.enumeration_errors == 0 and self.prefix_errors == 0


@dataclass(frozen=True, slots=True)
class RicoMt5DiscoverySettings:
    path: Path
    max_record_bytes: int = 16_384

    def __post_init__(self) -> None:
        if not isinstance(self.path, Path):
            raise TypeError("path must be pathlib.Path")
        if type(self.max_record_bytes) is not int or self.max_record_bytes <= 0:
            raise ValueError("max_record_bytes must be an explicit positive integer")


class RicoMt5DiscoveryReader:
    """Read one complete append-only discovery snapshot at a time."""

    __slots__ = ("_offset", "_settings")

    def __init__(self, settings: RicoMt5DiscoverySettings) -> None:
        if not isinstance(settings, RicoMt5DiscoverySettings):
            raise TypeError("settings must be RicoMt5DiscoverySettings")
        self._settings = settings
        self._offset = 0

    @property
    def offset(self) -> int:
        return self._offset

    def poll_snapshot(self) -> RicoMt5DiscoverySnapshot | None:
        try:
            with self._settings.path.open("rb") as source:
                source.seek(0, 2)
                size = source.tell()
                if size < self._offset:
                    raise DiscoveryContinuityError("discovery file shrank below consumed offset")
                if size == self._offset:
                    return None
                source.seek(self._offset)
                parsed = self._read_snapshot(source)
                if parsed is None:
                    return None
                snapshot, next_offset = parsed
        except FileNotFoundError:
            if self._offset:
                raise DiscoveryContinuityError(
                    "discovery file disappeared after a snapshot was consumed"
                ) from None
            return None
        self._offset = next_offset
        return snapshot

    def _read_snapshot(
        self, source: BinaryIO
    ) -> tuple[RicoMt5DiscoverySnapshot, int] | None:
        begin = self._read_record(source)
        if begin is None:
            return None
        _require_keys(
            begin,
            {"schema", "record_type", "snapshot_id", "prefix", "server_symbol_total"},
        )
        _require_schema_and_type(begin, "snapshot_begin")
        snapshot_id = _text(begin, "snapshot_id")
        prefix = _string(begin, "prefix")
        server_symbol_total = _nonnegative_int(begin, "server_symbol_total")
        symbols: list[RicoMt5DiscoveredSymbol] = []

        while True:
            record = self._read_record(source)
            if record is None:
                return None
            if record.get("snapshot_id") != snapshot_id:
                raise DiscoveryProtocolError("snapshot id changed before snapshot end")
            record_type = record.get("record_type")
            if record_type == "symbol":
                symbols.append(_parse_symbol(record))
                continue
            if record_type != "snapshot_end":
                raise DiscoveryProtocolError("unexpected discovery record type")
            _require_keys(
                record,
                {
                    "schema",
                    "record_type",
                    "snapshot_id",
                    "prefix_matches",
                    "emitted_symbols",
                    "excluded_custom",
                    "prefix_errors",
                    "enumeration_errors",
                },
            )
            _require_schema_and_type(record, "snapshot_end")
            emitted = _nonnegative_int(record, "emitted_symbols")
            if emitted != len(symbols):
                raise DiscoveryProtocolError(
                    "declared emitted symbol count does not match records"
                )
            try:
                snapshot = RicoMt5DiscoverySnapshot(
                    snapshot_id=snapshot_id,
                    prefix=prefix,
                    server_symbol_total=server_symbol_total,
                    prefix_matches=_nonnegative_int(record, "prefix_matches"),
                    excluded_custom=_nonnegative_int(record, "excluded_custom"),
                    prefix_errors=_nonnegative_int(record, "prefix_errors"),
                    enumeration_errors=_nonnegative_int(record, "enumeration_errors"),
                    symbols=tuple(symbols),
                )
            except (TypeError, ValueError) as exc:
                raise DiscoveryProtocolError(str(exc)) from exc
            return snapshot, source.tell()

    def _read_record(self, source: BinaryIO) -> dict[str, object] | None:
        line = source.readline(self._settings.max_record_bytes + 2)
        if not line or not line.endswith(b"\n"):
            if len(line) > self._settings.max_record_bytes:
                raise DiscoveryProtocolError("discovery record exceeded max_record_bytes")
            return None
        if len(line) - 1 > self._settings.max_record_bytes:
            raise DiscoveryProtocolError("discovery record exceeded max_record_bytes")
        try:
            value = json.loads(line.decode("ascii"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise DiscoveryProtocolError("discovery record is not canonical ASCII JSON") from exc
        if not isinstance(value, dict):
            raise DiscoveryProtocolError("discovery record must be a JSON object")
        return value


def _parse_symbol(record: dict[str, object]) -> RicoMt5DiscoveredSymbol:
    _require_keys(
        record,
        {"schema", "record_type", "snapshot_id", "symbol", "custom"},
    )
    _require_schema_and_type(record, "symbol")
    if record.get("custom") is not False:
        raise DiscoveryProtocolError("custom symbols must not enter broker discovery evidence")
    try:
        return RicoMt5DiscoveredSymbol(symbol=_text(record, "symbol"))
    except (TypeError, ValueError) as exc:
        raise DiscoveryProtocolError(str(exc)) from exc


def _require_keys(record: dict[str, object], keys: set[str]) -> None:
    if set(record) != keys:
        raise DiscoveryProtocolError("discovery record fields differ from schema")


def _require_schema_and_type(record: dict[str, object], record_type: str) -> None:
    if record.get("schema") != 1 or record.get("record_type") != record_type:
        raise DiscoveryProtocolError("discovery record schema/type mismatch")


def _text(record: dict[str, object], key: str) -> str:
    value = record.get(key)
    if not isinstance(value, str) or not value.strip():
        raise DiscoveryProtocolError(f"{key} must be non-empty text")
    return value


def _string(record: dict[str, object], key: str) -> str:
    value = record.get(key)
    if not isinstance(value, str):
        raise DiscoveryProtocolError(f"{key} must be text")
    return value


def _nonnegative_int(record: dict[str, object], key: str) -> int:
    value = record.get(key)
    if type(value) is not int or value < 0:
        raise DiscoveryProtocolError(f"{key} must be a non-negative integer")
    return value
