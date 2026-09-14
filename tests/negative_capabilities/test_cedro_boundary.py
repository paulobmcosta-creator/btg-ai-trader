"""Structural negative-capability tests for the Cedro Sprint 1 adapter."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "src/btg_ai_trader/observer/cedro_market_data.py"


def test_cedro_adapter_contains_no_trading_negotiation_or_account_surface() -> None:
    source = SOURCE.read_text(encoding="utf-8").lower()
    forbidden = (
        "services/" + "negotiation",
        "broker" + "servicelogin",
        "user_" + "identifier",
        "send_" + "new_order",
        "edit_" + "order",
        "cancel_" + "order",
        "account_" + "info",
        "financial_" + "account",
        "allocate_" + "guarantee",
    )
    for token in forbidden:
        assert token not in source


def test_cedro_adapter_has_no_network_library_binding_before_trial_protocol_review() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    forbidden_imports = (
        "import requests",
        "import httpx",
        "import aiohttp",
        "import websocket",
        "import websockets",
        "from requests",
        "from httpx",
        "from aiohttp",
        "from websocket",
        "from websockets",
    )
    for token in forbidden_imports:
        assert token not in source
