"""Structural negative-capability tests for the Cedro Sprint 1 adapter."""

import inspect

from btg_ai_trader.observer import cedro_market_data


def test_cedro_adapter_contains_no_trading_negotiation_or_account_surface() -> None:
    source = inspect.getsource(cedro_market_data).lower()
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
    source = inspect.getsource(cedro_market_data)
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
