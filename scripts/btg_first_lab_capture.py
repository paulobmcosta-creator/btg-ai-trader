"""Controlled read-only first-lab capture harness for BTG Solutions Data Services.

This script is intentionally outside the importable runtime package. It requires the
optional ``btg-data`` extra and a read-only API key supplied only through the process
environment. It never prints, persists, hashes or forwards the credential to evidence.
"""

import argparse
import hashlib
import json
import os
import re
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from btg_ai_trader.observer.btg_dataservices import (
    BTG_DATASERVICES_PROVIDER,
    BtgDataServicesSettings,
    BtgDataServicesSubscription,
)
from btg_ai_trader.observer.identity import EventId
from btg_ai_trader.observer.provenance import (
    CaptureContext,
    CodeRevision,
    ConfigHash,
    InputIdentity,
    ProvenanceLabel,
    start_run,
)
from btg_ai_trader.observer.raw_source import RawFrame
from btg_ai_trader.observer.storage import TechnicalEvidenceStore
from btg_ai_trader.observer.storage_records import (
    EvidenceRecord,
    PersistenceRecordId,
    TechnicalEventKind,
    TechnicalJournalRecord,
    content_hash,
)

API_KEY_ENV = "BTG_DATASERVICES_API_KEY"
FIRST_LAB_FAMILY = "WIN"
FIRST_LAB_STREAM = "realtime"
FIRST_LAB_DATA_TYPE = "trades"
FIRST_LAB_SUBTYPE = "derivatives"
PROVIDER_LABEL = ProvenanceLabel(BTG_DATASERVICES_PROVIDER)
WIN_CONTRACT = re.compile(r"^WIN[A-Z][0-9]{2}$")
DISCOVERY_EVENT = "available_to_subscribe"
DISCOVERY_SYMBOL_KEYS = ("tickers", "symbols")


def _canonical_json(value: object) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=True,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")


def _string_symbols(value: object) -> tuple[str, ...] | None:
    if not isinstance(value, list) or not value:
        return None
    if not all(isinstance(item, str) for item in value):
        return None
    return tuple(value)


def _symbols_from_mapping(value: dict[object, object]) -> tuple[str, ...] | None:
    if "error" in value:
        return None
    for key in DISCOVERY_SYMBOL_KEYS:
        symbols = _string_symbols(value.get(key))
        if symbols is not None:
            return symbols
    return None


def _recognized_discovery_symbols(value: object) -> tuple[str, ...] | None:
    """Return symbols only from bounded, explicitly recognized discovery responses.

    The provider does not publish a stable discovery-response schema. The harness
    therefore recognizes only an explicit top-level discovery event or a single
    ``response`` envelope containing a dedicated symbol-list field. Unknown, echoed,
    mixed or error-shaped payloads remain evidence only and never authorize subscription.
    """
    if not isinstance(value, dict):
        return None
    if value.get("event") == DISCOVERY_EVENT:
        return _symbols_from_mapping(value)
    if set(value) == {"response"}:
        response = value.get("response")
        if isinstance(response, dict):
            return _symbols_from_mapping(response)
    return None


def discovery_confirms_instrument(payloads: list[bytes], instrument: str) -> bool:
    """Require the exact WIN contract in a recognized provider discovery response."""
    if WIN_CONTRACT.fullmatch(instrument) is None:
        raise ValueError("first-lab instrument must be a concrete WIN contract, e.g. WINV26")
    for payload in payloads:
        try:
            parsed: object = json.loads(payload.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
        symbols = _recognized_discovery_symbols(parsed)
        if symbols is not None and instrument in symbols:
            return True
    return False


def is_confirmed_trade(payload: bytes, instrument: str) -> bool:
    """Recognize only the approved first-lab event for the confirmed concrete symbol."""
    try:
        parsed: object = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return False
    if not isinstance(parsed, dict):
        return False
    return parsed.get("event") == "trade" and parsed.get("symbol") == instrument


def _credential_source() -> str:
    credential = os.environ.get(API_KEY_ENV)
    if credential is None or not credential.strip():
        raise RuntimeError(f"{API_KEY_ENV} must be supplied by the authorized runtime environment")
    return credential


def _vendor_factory(credential: str, settings: BtgDataServicesSettings) -> Any:
    try:
        from btgsolutions_dataservices import (  # type: ignore[import-not-found]
            MarketDataWebSocketClient,
        )
    except ImportError as error:
        raise RuntimeError("install the project with the btg-data optional dependency") from error
    return MarketDataWebSocketClient(
        api_key=credential,
        stream_type=settings.stream_type,
        exchange=settings.exchange,
        data_type=settings.data_type,
        data_subtype=settings.data_subtype,
        instruments=[],
        ssl=True,
        feed=settings.feed,
    )


class SessionEvidence:
    """Append-only evidence/journal writer for the controlled first-lab run."""

    def __init__(
        self,
        store: TechnicalEvidenceStore,
        *,
        code_revision: CodeRevision,
        config: dict[str, object],
    ) -> None:
        config_bytes = _canonical_json(config)
        config_hash = ConfigHash(hashlib.sha256(config_bytes).hexdigest())
        started_at = datetime.now(UTC)
        manifest = start_run(
            started_at=started_at,
            code_revision=code_revision,
            config_hash=config_hash,
            inputs=(),
        )
        self._store = store
        self._context = CaptureContext.from_manifest(manifest, PROVIDER_LABEL)
        self._run_id = manifest.run_id
        plan = _canonical_json(
            {
                "schema": 1,
                "run_id": manifest.run_id.value,
                "started_at": started_at.isoformat(timespec="microseconds"),
                "code_revision": code_revision.value,
                "config_hash": config_hash.value,
                "config": config,
            }
        )
        self.record(plan, "btg-session-plan", TechnicalEventKind.STARTED)

    @property
    def run_id(self) -> str:
        return self._run_id.value

    def record(
        self,
        raw: bytes,
        detail: str,
        kind: TechnicalEventKind = TechnicalEventKind.OBSERVATION_RECORDED,
    ) -> None:
        observed_at = datetime.now(UTC)
        evidence_id = PersistenceRecordId(str(uuid4()))
        identity = InputIdentity(EventId(str(uuid4())), content_hash(raw))
        self._store.append_evidence(
            EvidenceRecord(
                evidence_id,
                identity,
                observed_at,
                raw,
                self._context,
            )
        )
        self._store.append_journal(
            TechnicalJournalRecord(
                PersistenceRecordId(str(uuid4())),
                self._context.run_id,
                observed_at,
                kind,
                ProvenanceLabel(detail),
                evidence_id,
            )
        )

    def stop(self) -> None:
        self._store.append_journal(
            TechnicalJournalRecord(
                PersistenceRecordId(str(uuid4())),
                self._context.run_id,
                datetime.now(UTC),
                TechnicalEventKind.STOPPED,
                ProvenanceLabel("btg-first-lab-stopped"),
            )
        )


def _config(capture_scope: str, instrument_candidate: str) -> dict[str, object]:
    return {
        "provider": BTG_DATASERVICES_PROVIDER,
        "capture_scope": capture_scope,
        "instrument_family": FIRST_LAB_FAMILY,
        "instrument_candidate": instrument_candidate,
        "stream_type": FIRST_LAB_STREAM,
        "exchange": "b3",
        "data_type": FIRST_LAB_DATA_TYPE,
        "data_subtype": FIRST_LAB_SUBTYPE,
        "feed": "A",
        "auto_reconnect": False,
        "auto_rollover": False,
        "auto_fallback": False,
        "economic_authority": "none",
    }


def _new_store(output_root: Path) -> tuple[TechnicalEvidenceStore, Path]:
    absolute = output_root.absolute()
    if any(part.is_symlink() for part in (absolute, *absolute.parents)):
        raise ValueError("output root and ancestors must not be symlinks")
    root = absolute.resolve(strict=True)
    if not root.is_dir():
        raise ValueError("output root must be an existing directory")
    session_root = root / ("btg-s1-first-lab-" + str(uuid4()))
    session_root.mkdir()
    archive = session_root / "archive"
    journal = session_root / "journal"
    archive.mkdir()
    journal.mkdir()
    return (
        TechnicalEvidenceStore(
            archive_root=archive,
            journal_root=journal,
            max_record_bytes=2_000_000,
        ),
        session_root,
    )


def _settings(capture_scope: str) -> BtgDataServicesSettings:
    return BtgDataServicesSettings(
        capture_scope=capture_scope,
        stream_type=FIRST_LAB_STREAM,
        exchange="b3",
        data_type=FIRST_LAB_DATA_TYPE,
        data_subtype=FIRST_LAB_SUBTYPE,
        feed="A",
        reconnect=False,
    )


def run_first_lab(
    *,
    instrument: str,
    capture_scope: str,
    code_revision: str,
    output_root: Path,
    discovery_seconds: float,
    capture_seconds: float,
) -> Path:
    """Run one causal session: connect, discover, confirm, subscribe, observe, close."""
    if WIN_CONTRACT.fullmatch(instrument) is None:
        raise ValueError("instrument must be an explicit concrete WIN contract")
    if discovery_seconds <= 0 or discovery_seconds > 30:
        raise ValueError("discovery_seconds must be in (0, 30]")
    if capture_seconds <= 0 or capture_seconds > 300:
        raise ValueError("capture_seconds must be in (0, 300]")

    revision = CodeRevision(code_revision)
    store, session_root = _new_store(output_root)
    settings = _settings(capture_scope)
    evidence = SessionEvidence(
        store,
        code_revision=revision,
        config=_config(capture_scope, instrument),
    )

    discovery_payloads: list[bytes] = []
    provider_errors: list[str] = []
    confirmed_trade_frames = 0
    other_post_subscription_frames = 0
    instrument_confirmed = False

    def record_control(payload: bytes) -> None:
        discovery_payloads.append(payload)
        detail = "btg-discovery-control" if not instrument_confirmed else "btg-capture-control"
        evidence.record(payload, detail)

    def record_frame(frame: RawFrame) -> None:
        nonlocal confirmed_trade_frames, other_post_subscription_frames
        if is_confirmed_trade(frame.payload, instrument):
            confirmed_trade_frames += 1
            detail = "btg-market-frame"
        else:
            other_post_subscription_frames += 1
            detail = "btg-postsubscribe-message"
        evidence.record(frame.payload, detail)

    subscription = BtgDataServicesSubscription(
        settings,
        _credential_source,
        record_frame,
        client_factory=_vendor_factory,
        control_sink=record_control,
        error_sink=provider_errors.append,
    )

    started = False
    body_succeeded = False
    close_succeeded = False
    try:
        subscription.start()
        started = True
        subscription.request_available_instruments()
        time.sleep(discovery_seconds)

        if provider_errors:
            raise RuntimeError("provider reported an error during discovery")
        if not discovery_confirms_instrument(discovery_payloads, instrument):
            raise RuntimeError("provider discovery did not confirm the requested WIN contract")

        confirmation = _canonical_json(
            {
                "schema": 1,
                "instrument_family": FIRST_LAB_FAMILY,
                "confirmed_instrument": instrument,
                "confirmation": "provider-discovery-listed-exact-match",
            }
        )
        evidence.record(confirmation, "btg-instrument-confirmed")
        instrument_confirmed = True

        subscription.subscribe_confirmed(instrument)
        time.sleep(capture_seconds)

        if provider_errors:
            raise RuntimeError("provider reported an error during capture")
        if confirmed_trade_frames == 0:
            raise RuntimeError("capture completed without a confirmed trade frame")
        body_succeeded = True
    finally:
        try:
            if started:
                subscription.close()
            close_succeeded = True
        finally:
            if not (body_succeeded and close_succeeded):
                evidence.stop()

    summary = _canonical_json(
        {
            "schema": 1,
            "provider": BTG_DATASERVICES_PROVIDER,
            "instrument_family": FIRST_LAB_FAMILY,
            "instrument": instrument,
            "stream_type": FIRST_LAB_STREAM,
            "data_type": FIRST_LAB_DATA_TYPE,
            "run_id": evidence.run_id,
            "confirmed_trade_frames": confirmed_trade_frames,
            "other_post_subscription_frames": other_post_subscription_frames,
            "real_money": False,
            "trading_capability": False,
        }
    )
    evidence.record(summary, "btg-capture-summary")
    evidence.stop()
    return session_root


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="BTG Data Services Sprint 1 first-lab capture")
    parser.add_argument("--instrument", required=True, help="candidate confirmed by discovery")
    parser.add_argument("--capture-scope", required=True)
    parser.add_argument("--code-revision", required=True, help="exact 40-char reviewed Git SHA")
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--discovery-seconds", required=True, type=float)
    parser.add_argument("--capture-seconds", required=True, type=float)
    return parser


def main() -> int:
    args = _parser().parse_args()
    session_root = run_first_lab(
        instrument=args.instrument,
        capture_scope=args.capture_scope,
        code_revision=args.code_revision,
        output_root=args.output_root,
        discovery_seconds=args.discovery_seconds,
        capture_seconds=args.capture_seconds,
    )
    print(f"controlled read-only capture evidence: {session_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
