"""One-command orchestration for the passive XP/MT5 Sprint 1 capture.

This launcher coordinates only local files and the existing read-only evidence harness.
It never imports MetaTrader5 and exposes no account, position, or order surface.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import time
import uuid
from pathlib import Path

BRANCH = "sprint/1-market-observer"
PROVIDER = "xp-mt5"
STATUS_NAME = "capture-bridge-status.tsv"
CONTROL_NAME = "capture-control.tsv"
CAPTURE_RE = re.compile(r"^s1-xp-capture-a([0-9]+)$")
INSTRUMENT_RE = re.compile(r"^WIN[A-Z][0-9]{2}$")
EVIDENCE_GLOB = "rico-mt5-s1-first-lab-*"


def _git(repo: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _parse_tsv(line: str) -> dict[str, str] | None:
    line = line.rstrip("\r\n")
    if not line:
        return None
    result: dict[str, str] = {}
    for field in line.split("\t"):
        if "=" not in field:
            return None
        key, value = field.split("=", 1)
        if not key or key in result:
            return None
        result[key] = value
    return result


def _read_status(path: Path) -> dict[str, str] | None:
    try:
        return _parse_tsv(path.read_text(encoding="ascii"))
    except (FileNotFoundError, UnicodeDecodeError, OSError):
        return None


def _status_ready(path: Path, instrument: str, freshness_seconds: float = 4.0) -> bool:
    status = _read_status(path)
    if status is None:
        return False
    try:
        age = time.time() - path.stat().st_mtime
    except OSError:
        return False
    return (
        age <= freshness_seconds
        and status.get("schema") == "1"
        and status.get("state") == "IDLE"
        and status.get("provider") == PROVIDER
        and status.get("instrument") == instrument
        and status.get("timeframe") == "PERIOD_M1"
    )


def _wait_bridge_ready(path: Path, instrument: str, timeout_seconds: float) -> None:
    deadline = time.monotonic() + timeout_seconds
    notice = False
    while time.monotonic() < deadline:
        if _status_ready(path, instrument):
            return
        if not notice:
            print("Aguardando a ponte passiva do MT5...")
            print(f"Deixe XPMarketDataBridge anexado ao grafico {instrument} em M1.")
            print("Nao e necessario preencher parametros de captura.")
            notice = True
        time.sleep(0.5)
    raise RuntimeError("a ponte passiva do MT5 nao ficou pronta no tempo limite")


def _next_scope(root: Path) -> str:
    maximum = 0
    for path in root.iterdir():
        if not path.is_dir():
            continue
        match = CAPTURE_RE.fullmatch(path.name)
        if match is not None:
            maximum = max(maximum, int(match.group(1)))
    return f"s1-xp-capture-a{maximum + 1}"


def _control_line(scope: str, instrument: str, expires_epoch: int) -> str:
    return (
        "schema=1\tstate=ACTIVE"
        f"\tcapture_scope={scope}"
        f"\tinstrument={instrument}"
        f"\tprovider={PROVIDER}"
        f"\texpires_epoch={expires_epoch}\n"
    )


def _publish_control(path: Path, line: str) -> None:
    temporary = path.with_name(f"{path.name}.tmp-{uuid.uuid4().hex}")
    temporary.write_text(line, encoding="ascii", newline="")
    os.replace(temporary, path)


def _active_status(path: Path, scope: str, instrument: str) -> bool:
    status = _read_status(path)
    return bool(
        status
        and status.get("state") == "ACTIVE"
        and status.get("provider") == PROVIDER
        and status.get("capture_scope") == scope
        and status.get("instrument") == instrument
    )


def _build_harness_command(
    repo: Path,
    instrument: str,
    scope: str,
    revision: str,
    capture_root: Path,
    evidence_root: Path,
    capture_seconds: int,
) -> list[str]:
    return [
        sys.executable,
        str(repo / "scripts" / "rico_mt5_first_lab_capture.py"),
        "--instrument",
        instrument,
        "--capture-scope",
        scope,
        "--code-revision",
        revision,
        "--discovery-file",
        str(capture_root / "discovery.ndjson"),
        "--tick-file",
        str(capture_root / "ticks.ndjson"),
        "--candle-file",
        str(capture_root / "candles.ndjson"),
        "--output-root",
        str(evidence_root),
        "--clock-scope",
        "windows-local-monotonic",
        "--discovery-timeout-seconds",
        "30",
        "--capture-seconds",
        str(capture_seconds),
        "--poll-interval-ms",
        "100",
        "--heartbeat-timeout-ms",
        "2000",
        "--market-staleness-ms",
        "5000",
    ]


def run_capture(instrument: str, capture_seconds: int, evidence_root: Path) -> int:
    if INSTRUMENT_RE.fullmatch(instrument) is None:
        raise ValueError("instrumento deve ser um contrato WIN explicito")
    if capture_seconds < 60 or capture_seconds > 300:
        raise ValueError("capture_seconds deve estar entre 60 e 300")

    repo = Path(__file__).resolve().parents[1]
    branch = _git(repo, "branch", "--show-current")
    revision = _git(repo, "rev-parse", "HEAD")
    dirty = _git(repo, "status", "--porcelain")
    if branch != BRANCH:
        raise RuntimeError(f"checkout deve estar em {BRANCH}; atual: {branch}")
    if re.fullmatch(r"[0-9a-f]{40}", revision) is None:
        raise RuntimeError("SHA Git invalido")
    if dirty:
        raise RuntimeError("working tree deve estar limpa antes da captura")

    appdata = os.environ.get("APPDATA")
    if not appdata:
        raise RuntimeError("APPDATA nao esta disponivel")
    common_files = Path(appdata) / "MetaQuotes" / "Terminal" / "Common" / "Files"
    if not common_files.is_dir():
        raise RuntimeError("diretorio FILE_COMMON do MetaTrader nao foi encontrado")

    bridge_root = common_files / "btg_ai_trader"
    bridge_root.mkdir(parents=True, exist_ok=True)
    evidence_root.mkdir(parents=True, exist_ok=True)
    status_path = bridge_root / STATUS_NAME
    control_path = bridge_root / CONTROL_NAME

    _wait_bridge_ready(status_path, instrument, 60.0)
    if control_path.exists():
        control_path.unlink()
        time.sleep(1.0)
        _wait_bridge_ready(status_path, instrument, 10.0)

    scope = _next_scope(bridge_root)
    capture_root = bridge_root / scope
    capture_root.mkdir()

    before_evidence = {path.resolve() for path in evidence_root.glob(EVIDENCE_GLOB)}
    command = _build_harness_command(
        repo,
        instrument,
        scope,
        revision,
        capture_root,
        evidence_root,
        capture_seconds,
    )
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(repo / "src")

    print(f"Preparando captura passiva {scope} em {instrument}...")
    process = subprocess.Popen(
        command,
        cwd=repo,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    control_published = False
    session_root: Path | None = None
    try:
        preflight_deadline = time.monotonic() + 15.0
        while time.monotonic() < preflight_deadline and process.poll() is None:
            current = {path.resolve() for path in evidence_root.glob(EVIDENCE_GLOB)}
            created = sorted(current - before_evidence)
            if created:
                session_root = created[0]
                break
            time.sleep(0.2)

        if session_root is None:
            output, _ = process.communicate(timeout=35)
            if output:
                print(output, end="" if output.endswith("\n") else "\n")
            raise RuntimeError(f"harness nao passou pelo preflight; preserve {scope}")

        if any(capture_root.iterdir()):
            raise RuntimeError(f"arquivos apareceram antes da ativacao; preserve {scope}")

        expires_epoch = int(time.time()) + capture_seconds + 90
        _publish_control(control_path, _control_line(scope, instrument, expires_epoch))
        control_published = True

        activation_deadline = time.monotonic() + 8.0
        while time.monotonic() < activation_deadline:
            if _active_status(status_path, scope, instrument):
                print(f"CAPTURE_ACTIVE: {scope}")
                print("Nenhuma acao adicional no MT5 e necessaria.")
                break
            if process.poll() is not None:
                break
            time.sleep(0.2)
        else:
            print("AVISO: a ponte ainda nao confirmou ACTIVE; aguardando encerramento seguro.")

        output, _ = process.communicate(timeout=capture_seconds + 60)
    finally:
        if control_published:
            try:
                control_path.unlink()
            except FileNotFoundError:
                pass
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
        time.sleep(0.75)

    if output:
        print(output, end="" if output.endswith("\n") else "\n")
    if process.returncode != 0:
        raise RuntimeError(
            f"captura nao qualificou; preserve {scope} e a evidencia; nao reutilize o namespace"
        )

    print(f"CAPTURE_COMPLETED: {scope}")
    print(f"CODE_REVISION: {revision}")
    print(f"EVIDENCE_SESSION: {session_root}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--instrument", default="WINV26")
    parser.add_argument("--capture-seconds", type=int, default=120)
    parser.add_argument(
        "--evidence-root",
        type=Path,
        default=Path(r"C:\BTG_AI_TRADER_EVIDENCE"),
    )
    args = parser.parse_args()
    try:
        return run_capture(args.instrument, args.capture_seconds, args.evidence_root)
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as exc:
        print(f"CAPTURE_ABORTED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
