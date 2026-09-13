"""Isolated package-import experiment. Never invoke any MetaTrader5 API function."""

import importlib.metadata
import json
import platform
import sys

import MetaTrader5 as mt5

EXPECTED_VERSION = "5.0.6180"
installed_version = importlib.metadata.version("metatrader5")
if installed_version != EXPECTED_VERSION or mt5.__version__ != EXPECTED_VERSION:
    raise RuntimeError("Unexpected package version")
if sys.version_info[:2] != (3, 12) or platform.system() != "Windows":
    raise RuntimeError("This experiment is restricted to Windows Python 3.12")

symbols = {
    "observation_surface": (
        "symbols_get", "symbol_info", "symbol_info_tick",
        "copy_rates_from", "copy_rates_from_pos", "copy_rates_range",
        "copy_ticks_from", "copy_ticks_range",
        "market_book_add", "market_book_get", "market_book_release",
    ),
    "connection_surface_not_invoked": (
        "initialize", "login", "shutdown", "terminal_info", "account_info",
    ),
    "financial_surface_not_invoked": (
        "order_send", "order_check", "order_calc_margin", "order_calc_profit",
        "orders_get", "positions_get", "history_orders_get", "history_deals_get",
    ),
}
report = {
    "python": platform.python_version(),
    "platform": platform.platform(),
    "package_version": installed_version,
    "module_version": mt5.__version__,
    "module_name": mt5.__name__,
    "module_path": mt5.__file__,
    "numpy_version": importlib.metadata.version("numpy"),
    "sdk_functions_invoked_by_probe": [],
    "surface_presence": {
        group: {name: callable(getattr(mt5, name, None)) for name in names}
        for group, names in symbols.items()
    },
}
print(json.dumps(report, indent=2, sort_keys=True))
