from __future__ import annotations

import runpy
from collections.abc import Callable
from pathlib import Path
from typing import cast

import pytest


def _scan_file(path: Path) -> list[object]:
    namespace = runpy.run_path("scripts/check_s8_strategy_boundary.py")
    scanner = cast(Callable[[Path], list[object]], namespace["scan_file"])
    return scanner(path)


@pytest.mark.parametrize(
    "source",
    [
        "class PaperTrader:\n    pass\n",
        "def order_send():\n    pass\n",
        "async def positions_get():\n    pass\n",
    ],
)
def test_scanner_rejects_forbidden_declaration_names(tmp_path: Path, source: str) -> None:
    target = tmp_path / "probe.py"
    target.write_text(source, encoding="utf-8")

    findings = _scan_file(target)

    assert any("forbidden operational declaration" in str(finding) for finding in findings)


def test_scanner_allows_unrelated_declaration_names(tmp_path: Path) -> None:
    target = tmp_path / "probe.py"
    target.write_text("class StrategyHelper:\n    pass\n", encoding="utf-8")

    assert _scan_file(target) == []


@pytest.mark.parametrize(
    "source",
    [
        "from btg_ai_trader.risk_engine import evaluate_risk\n",
        "from btg_ai_trader.risk_engine import RiskAuthorization\n",
        "import btg_ai_trader.risk_engine\n",
        "from btg_ai_trader import risk_engine\n",
    ],
)
def test_risk_adapter_rejects_broader_risk_engine_authority(
    tmp_path: Path,
    source: str,
) -> None:
    strategy_dir = tmp_path / "strategy"
    strategy_dir.mkdir()
    target = strategy_dir / "risk_adapter.py"
    target.write_text(source, encoding="utf-8")

    findings = _scan_file(target)

    assert findings
    assert any(
        "Risk Engine" in str(finding) or "risk_adapter" in str(finding)
        for finding in findings
    )


def test_risk_adapter_allows_only_required_risk_proposal_symbols(tmp_path: Path) -> None:
    strategy_dir = tmp_path / "strategy"
    strategy_dir.mkdir()
    target = strategy_dir / "risk_adapter.py"
    target.write_text(
        "from btg_ai_trader.risk_engine import EconomicDirection as RiskEconomicDirection\n"
        "from btg_ai_trader.risk_engine import RiskProposal\n",
        encoding="utf-8",
    )

    assert _scan_file(target) == []


@pytest.mark.parametrize(
    "source",
    [
        "from urllib import request\nrequest.urlopen('https://example.invalid')\n",
        "from urllib import request as req\nreq.urlopen('https://example.invalid')\n",
    ],
)
def test_scanner_rejects_split_forbidden_imports(tmp_path: Path, source: str) -> None:
    target = tmp_path / "probe.py"
    target.write_text(source, encoding="utf-8")

    findings = _scan_file(target)

    assert any("forbidden import: urllib.request" in str(finding) for finding in findings)


@pytest.mark.parametrize(
    "source",
    [
        "import http.client\nhttp.client.HTTPSConnection('example.invalid')\n",
        "from http import client\nclient.HTTPSConnection('example.invalid')\n",
        "from http.client import HTTPSConnection\nHTTPSConnection('example.invalid')\n",
        "import ftplib\nftplib.FTP('example.invalid')\n",
    ],
)
def test_scanner_rejects_network_clients_outside_import_allowlist(
    tmp_path: Path,
    source: str,
) -> None:
    target = tmp_path / "probe.py"
    target.write_text(source, encoding="utf-8")

    findings = _scan_file(target)

    assert any("outside Strategy allowlist" in str(finding) for finding in findings)


def test_scanner_allows_only_current_strategy_dependency_surface(tmp_path: Path) -> None:
    target = tmp_path / "probe.py"
    target.write_text(
        "from __future__ import annotations\n"
        "import hashlib\n"
        "import json\n"
        "import types\n"
        "import weakref\n"
        "from collections.abc import Callable, Mapping\n"
        "from dataclasses import dataclass, field\n"
        "from datetime import UTC, datetime, timedelta\n"
        "from decimal import Decimal\n"
        "from enum import Enum\n"
        "from btg_ai_trader.observer.identity import TradableInstrumentId\n"
        "from btg_ai_trader.strategy.domain import CandidateStrategy\n",
        encoding="utf-8",
    )

    assert _scan_file(target) == []


@pytest.mark.parametrize(
    "source",
    [
        "file_open = open\nfile_open('state', 'w')\n",
        "runner = eval\nrunner('1 + 1')\n",
        "from datetime import datetime\nclock = datetime.now\nclock()\n",
        "from datetime import datetime as dt\nclock = dt.utcnow\nclock()\n",
    ],
)
def test_scanner_rejects_references_to_forbidden_callables(
    tmp_path: Path,
    source: str,
) -> None:
    target = tmp_path / "probe.py"
    target.write_text(source, encoding="utf-8")

    findings = _scan_file(target)

    assert any("forbidden callable reference" in str(finding) for finding in findings)


def test_scanner_allows_reference_to_safe_callable(tmp_path: Path) -> None:
    target = tmp_path / "probe.py"
    target.write_text(
        "import hashlib\n"
        "digest = hashlib.sha256\n"
        "value = digest(b'payload').hexdigest()\n",
        encoding="utf-8",
    )

    assert _scan_file(target) == []


@pytest.mark.parametrize(
    "source",
    [
        (
            "from btg_ai_trader.strategy.domain import datetime as clock\n"
            "clock.now()\n"
        ),
        "from btg_ai_trader.strategy.domain import json\n",
        "from btg_ai_trader.strategy.engine import StrategyDecision\n",
        "from datetime import timezone\n",
    ],
)
def test_scanner_rejects_reexports_and_unapproved_symbols(
    tmp_path: Path,
    source: str,
) -> None:
    target = tmp_path / "probe.py"
    target.write_text(source, encoding="utf-8")

    findings = _scan_file(target)

    assert any("symbol outside Strategy import allowlist" in str(finding) for finding in findings)


def test_scanner_rejects_namespace_import_of_allowlisted_internal_module(
    tmp_path: Path,
) -> None:
    target = tmp_path / "probe.py"
    target.write_text(
        "import btg_ai_trader.strategy.domain as domain\n"
        "clock = domain.datetime\n",
        encoding="utf-8",
    )

    findings = _scan_file(target)

    assert any("outside Strategy allowlist" in str(finding) for finding in findings)


@pytest.mark.parametrize(
    "source",
    [
        (
            "import json\n"
            "json.__builtins__['open']('state', 'w').write('x')\n"
        ),
        "__builtins__['open']('state', 'w')\n",
        (
            "import json\n"
            "json.__dict__['__builtins__']['open']('state', 'w')\n"
        ),
        (
            "import json\n"
            "getattr(json, '__builtins__')['open']('state', 'w')\n"
        ),
        "globals()['__builtins__']['open']('state', 'w')\n",
    ],
)
def test_scanner_rejects_reflection_paths_to_forbidden_builtins(
    tmp_path: Path,
    source: str,
) -> None:
    target = tmp_path / "probe.py"
    target.write_text(source, encoding="utf-8")

    findings = _scan_file(target)

    assert any(
        "forbidden reflection namespace" in str(finding)
        or "forbidden callable reference" in str(finding)
        for finding in findings
    )


def test_scanner_keeps_required_object_setattr_internal_pattern_allowed(
    tmp_path: Path,
) -> None:
    target = tmp_path / "probe.py"
    target.write_text(
        "class Holder:\n"
        "    pass\n"
        "holder = Holder()\n"
        "object.__setattr__(holder, 'value', 1)\n",
        encoding="utf-8",
    )

    assert _scan_file(target) == []


@pytest.mark.parametrize(
    "source",
    [
        "from datetime import datetime\ndatetime.today()\n",
        "from datetime import datetime as dt\ndt.today()\n",
        "from datetime import datetime\nclock = datetime.today\nclock()\n",
    ],
)
def test_scanner_rejects_datetime_today_wall_clock(
    tmp_path: Path,
    source: str,
) -> None:
    target = tmp_path / "probe.py"
    target.write_text(source, encoding="utf-8")

    findings = _scan_file(target)

    assert any(
        "datetime.today" in str(finding)
        and (
            "forbidden call" in str(finding)
            or "forbidden callable reference" in str(finding)
        )
        for finding in findings
    )


@pytest.mark.parametrize(
    "source",
    [
        (
            "import json\n"
            "json.__loader__.set_data('/tmp/state', b'changed')\n"
        ),
        (
            "import json\n"
            "json.__spec__.loader.set_data('/tmp/state', b'changed')\n"
        ),
        (
            "import json\n"
            "json.__loader__.get_data('/tmp/state')\n"
        ),
    ],
)
def test_scanner_rejects_loader_and_spec_reflection(
    tmp_path: Path,
    source: str,
) -> None:
    target = tmp_path / "probe.py"
    target.write_text(source, encoding="utf-8")

    findings = _scan_file(target)

    assert any(
        "forbidden reflection namespace" in str(finding)
        or "forbidden I/O method" in str(finding)
        for finding in findings
    )


@pytest.mark.parametrize(
    "source",
    [
        "import json\njson.dump({'x': 1}, handle)\n",
        "import json\njson.load(handle)\n",
        "import json as codec\ncodec.dump({'x': 1}, handle)\n",
        "import json as codec\ncodec.load(handle)\n",
    ],
)
def test_scanner_rejects_json_file_helpers(
    tmp_path: Path,
    source: str,
) -> None:
    target = tmp_path / "probe.py"
    target.write_text(source, encoding="utf-8")

    findings = _scan_file(target)

    assert any(
        "module attribute outside Strategy allowlist" in str(finding)
        for finding in findings
    )


def test_scanner_allows_only_required_namespace_module_apis(tmp_path: Path) -> None:
    target = tmp_path / "probe.py"
    target.write_text(
        "import hashlib\n"
        "import json\n"
        "import types\n"
        "import weakref\n"
        "digest = hashlib.sha256(b'x').hexdigest()\n"
        "encoded = json.dumps({'digest': digest})\n"
        "proxy = types.MappingProxyType({'encoded': encoded})\n"
        "reference_type = weakref.ReferenceType\n"
        "reference_factory = weakref.ref\n",
        encoding="utf-8",
    )

    assert _scan_file(target) == []


@pytest.mark.parametrize(
    "source",
    [
        (
            "try:\n"
            "    raise RuntimeError('probe')\n"
            "except RuntimeError as error:\n"
            "    error.__traceback__.tb_frame.f_globals['__builtins__']['open']('file', 'w')\n"
        ),
        "frame = error.__traceback__.tb_frame\n",
        "access = frame.f_globals\n",
        "access = frame.f_locals\n",
        "access = frame.f_builtins\n",
        "access = generator.gi_frame\n",
        "access = coroutine.cr_frame\n",
    ],
)
def test_scanner_rejects_traceback_and_frame_reflection(
    tmp_path: Path,
    source: str,
) -> None:
    target = tmp_path / "probe.py"
    target.write_text(source, encoding="utf-8")

    findings = _scan_file(target)

    assert any("forbidden reflection namespace" in str(finding) for finding in findings)


@pytest.mark.parametrize(
    "source",
    [
        "handle.write(b'data')\n",
        "handle.read()\n",
        "handle.readlines()\n",
        "handle.writelines(['x'])\n",
        "handle.readinto(buffer)\n",
    ],
)
def test_scanner_rejects_generic_stream_io(tmp_path: Path, source: str) -> None:
    target = tmp_path / "probe.py"
    target.write_text(source, encoding="utf-8")
    assert any("forbidden I/O method" in str(f) for f in _scan_file(target))


@pytest.mark.parametrize(
    "source",
    [
        "import json\ncodec = json\ncodec.dump({'a': 1}, handle)\n",
        "import json\ncodec = json\ncodec.load(handle)\n",
        "import json\nfirst = json\nsecond = first\nsecond.dump({}, handle)\n",
        "import json\n(codec := json).dump({}, handle)\n",
    ],
)
def test_scanner_rejects_assignment_aliased_module_io(
    tmp_path: Path, source: str
) -> None:
    target = tmp_path / "probe.py"
    target.write_text(source, encoding="utf-8")
    assert any(
        "module attribute outside Strategy allowlist" in str(f)
        for f in _scan_file(target)
    )


def test_scanner_allows_assignment_aliased_json_dumps(tmp_path: Path) -> None:
    target = tmp_path / "probe.py"
    target.write_text(
        "import json\ncodec = json\nencoded = codec.dumps({'value': 1})\n",
        encoding="utf-8",
    )
    assert _scan_file(target) == []


@pytest.mark.parametrize(
    "source",
    [
        "import json\n(codec,) = (json,)\ncodec.dump({}, handle)\n",
        "import json\n[codec] = [json]\ncodec.dump({}, handle)\n",
        "import json\n((codec,),) = ((json,),)\ncodec.dump({}, handle)\n",
        "import json\nfor codec in [json]:\n    codec.dump({}, handle)\n",
        "import json\nvalues = [codec.dump({}, handle) for codec in [json]]\n",
        "import json\ncodec = [json][0]\ncodec.dump({}, handle)\n",
        "import json\ncodec: object = json\ncodec.dump({}, handle)\n",
        "import json\n(codec := [json][0]).dump({}, handle)\n",
        "import json\n[codec for codec in [json]]\n",
    ],
)
def test_scanner_fails_closed_on_opaque_module_alias_transfers(
    tmp_path: Path, source: str
) -> None:
    target = tmp_path / "probe.py"
    target.write_text(source, encoding="utf-8")
    findings = _scan_file(target)
    assert any("unverifiable module alias binding" in str(finding) for finding in findings)


def test_scanner_still_allows_simple_module_alias_and_value_calls(
    tmp_path: Path,
) -> None:
    target = tmp_path / "probe.py"
    target.write_text(
        "import json\n"
        "codec = json\n"
        "encoded = codec.dumps({'ok': 1})\n"
        "encoded_values = [codec.dumps({'ok': n}) for n in (1, 2)]\n",
        encoding="utf-8",
    )
    assert _scan_file(target) == []


@pytest.mark.parametrize(
    "source",
    [
        "import json\ndef codec():\n    return json\ncodec().dump({}, handle)\n",
        "import json\ndef codec():\n    return (json,)\ncodec()[0].dump({}, handle)\n",
        "import json\ncodec = lambda: json\ncodec().dump({}, handle)\n",
        "import json\ndef codec():\n    yield json\nnext(codec()).dump({}, handle)\n",
        "import json\ndef codec():\n    yield from [json]\nnext(codec()).dump({}, handle)\n",
        "import json\ndef codec():\n    return [json][0]\ncodec().dump({}, handle)\n",
    ],
)
def test_scanner_rejects_helper_returned_module_io(
    tmp_path: Path, source: str
) -> None:
    target = tmp_path / "probe.py"
    target.write_text(source, encoding="utf-8")
    assert any(
        "unverifiable module alias binding" in str(finding)
        for finding in _scan_file(target)
    )


def test_scanner_allows_helper_returning_pure_json_value(tmp_path: Path) -> None:
    target = tmp_path / "probe.py"
    target.write_text(
        "import json\ndef codec():\n    return json.dumps({'ok': 1})\n"
        "value = codec()\n",
        encoding="utf-8",
    )
    assert _scan_file(target) == []


@pytest.mark.parametrize(
    "source",
    [
        "import json\n"
        "def encode(value, handle, codec=json):\n    codec.dump(value, handle)\n",
        "import json\n"
        "def encode(value, handle, *, codec=json):\n    codec.dump(value, handle)\n",
        "import json\n"
        "def encode(value, handle, codec=(json,)):\n    codec[0].dump(value, handle)\n",
        "import json\n"
        "module = json\ndef encode(value, handle, codec=module):\n    codec.dump(value, handle)\n",
        "import json\n"
        "encode = lambda value, handle, codec=json: codec.dump(value, handle)\n",
        "import json\n"
        "encode = lambda value, *, codec=json: codec.dump(value, handle)\n",
        "import json\n"
        "async def encode(value, handle, *, codec=json):\n    codec.dump(value, handle)\n",
    ],
)
def test_scanner_rejects_module_capabilities_captured_in_function_defaults(
    tmp_path: Path, source: str
) -> None:
    target = tmp_path / "probe.py"
    target.write_text(source, encoding="utf-8")
    assert any(
        "unverifiable module alias binding:" in str(finding)
        and "argument default" in str(finding)
        for finding in _scan_file(target)
    )


def test_scanner_allows_non_module_function_defaults(tmp_path: Path) -> None:
    target = tmp_path / "probe.py"
    target.write_text(
        "import json\n"
        "def encode(value='default', *, active=True):\n"
        "    return json.dumps({'value': value, 'active': active})\n"
        "encode_value = lambda value='default': json.dumps({'value': value})\n",
        encoding="utf-8",
    )
    assert _scan_file(target) == []


@pytest.mark.parametrize(
    "source",
    [
        (
            "import json\n"
            "def passthrough(value):\n    return value\n"
            "passthrough(json).dump({}, handle)\n"
        ),
        (
            "import json\n"
            "def passthrough(*, value):\n    return value\n"
            "passthrough(value=json).dump({}, handle)\n"
        ),
        (
            "import json\n"
            "def passthrough(*values):\n    return values[0]\n"
            "passthrough(*(json,)).dump({}, handle)\n"
        ),
        (
            "import json\n"
            "def passthrough(**values):\n    return values['codec']\n"
            "passthrough(**{'codec': json}).dump({}, handle)\n"
        ),
        (
            "import json\n"
            "def passthrough(value):\n    return value[0]\n"
            "passthrough([json]).dump({}, handle)\n"
        ),
        (
            "import json\n"
            "codec = json\n"
            "def passthrough(value):\n    return value\n"
            "passthrough(codec).dump({}, handle)\n"
        ),
        (
            "import json\n"
            "def passthrough(value):\n    return value\n"
            "passthrough({'codec': (json,)})['codec'][0].dump({}, handle)\n"
        ),
    ],
)
def test_scanner_fails_closed_on_module_capability_call_arguments(
    tmp_path: Path, source: str
) -> None:
    target = tmp_path / "probe.py"
    target.write_text(source, encoding="utf-8")
    assert any(
        "unverifiable module alias binding: module-valued call argument" in str(finding)
        for finding in _scan_file(target)
    )


def test_scanner_allows_pure_values_as_function_arguments(tmp_path: Path) -> None:
    target = tmp_path / "probe.py"
    target.write_text(
        "import json\n"
        "def encode(value):\n    return json.dumps(value)\n"
        "value = encode({'ok': True})\n"
        "other = json.dumps({'nested': [json.dumps({'a': 1})]})\n",
        encoding="utf-8",
    )
    assert _scan_file(target) == []


@pytest.mark.parametrize(
    "source",
    [
        "def run(client, order):\n    client.submit_order(order)\n",
        "def run(client, order):\n    client.cancel_order(order)\n",
        "def run(effect):\n    effect()\n",
        "def run(client):\n    client.get()\n",
        "def run(client):\n    client.send('order')\n",
        "def run(client):\n    getattr(client, 'submit_order')('order')\n",
        "def run(effect):\n    callback = effect\n    callback()\n",
        "def run(client):\n    client.submit_order\n",
    ],
)
def test_scanner_rejects_unapproved_injected_calls(
    tmp_path: Path, source: str
) -> None:
    target = tmp_path / "probe.py"
    target.write_text(source, encoding="utf-8")
    findings = _scan_file(target)
    assert any(
        "call outside audited Strategy allowlist" in str(finding)
        or "forbidden operational attribute" in str(finding)
        for finding in findings
    )


def test_scanner_allows_reviewed_strategy_call_sites(tmp_path: Path) -> None:
    target = tmp_path / "probe.py"
    target.write_text(
        "import hashlib\n"
        "import json\n"
        "encoded = json.dumps({'ok': True}).encode('utf-8')\n"
        "digest = hashlib.sha256(encoded).hexdigest()\n"
        "assert digest\n",
        encoding="utf-8",
    )
    assert _scan_file(target) == []


def test_scanner_rejects_shadowed_local_helper_callback(tmp_path: Path) -> None:
    target = tmp_path / "probe.py"
    target.write_text(
        "def helper(value):\n    return value\n"
        "def run(helper):\n    helper('effect')\n",
        encoding="utf-8",
    )
    assert any(
        "call outside audited Strategy allowlist" in str(finding)
        for finding in _scan_file(target)
    )


def test_scanner_rejects_broker_method_reference_without_invocation(
    tmp_path: Path,
) -> None:
    target = tmp_path / "probe.py"
    target.write_text(
        "def run(client):\n    return client.submit_order\n",
        encoding="utf-8",
    )
    assert any(
        "forbidden operational attribute" in str(finding)
        for finding in _scan_file(target)
    )


@pytest.mark.parametrize(
    "source",
    [
        "def f(evaluate_strategy, value):\n    evaluate_strategy(value)\n",
        "def f(ledger):\n    ledger.pop('position')\n",
        "def f(json):\n    json.dumps({'x': 1})\n",
        "def f(*, RiskProposal):\n    RiskProposal()\n",
        "def f(**values):\n    return values['callback']()\n",
        "def f(object):\n    object.__setattr__(state, 'orders', 1)\n",
    ],
)
def test_scanner_blocks_shadowed_approved_names(tmp_path: Path, source: str) -> None:
    target = tmp_path / "probe.py"
    target.write_text(source, encoding="utf-8")
    assert any(
        "call outside audited Strategy allowlist" in str(item)
        for item in _scan_file(target)
    )


@pytest.mark.parametrize(
    "source",
    [
        "def f(state):\n    state.balance = 0\n",
        "def f(state):\n    state['orders'] = ()\n",
        "def f(state):\n    state.balance += 1\n",
        "def f(state):\n    del state['orders']\n",
        "def f(state):\n    del state.balance\n",
        "def f(state):\n    [state['orders']] = [1]\n",
        "def f(state):\n    for state['orders'] in (1, 2):\n        pass\n",
    ],
)
def test_scanner_blocks_mutation_of_injected_objects(tmp_path: Path, source: str) -> None:
    target = tmp_path / "probe.py"
    target.write_text(source, encoding="utf-8")
    assert any(
        "external or unverified mutation target forbidden" in str(item)
        for item in _scan_file(target)
    )


def test_scanner_rejects_unapproved_setattr_even_with_builtin_name(tmp_path: Path) -> None:
    target = tmp_path / "probe.py"
    target.write_text(
        "def f(state):\n    object.__setattr__(state, 'balance', 0)\n",
        encoding="utf-8",
    )
    assert any(
        "call outside audited Strategy allowlist" in str(item)
        for item in _scan_file(target)
    )
