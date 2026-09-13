# MT5 isolated installation and import spike

## Boundary and decision status

This experiment contributes narrowly to DD-61 (Python 3.12 compatibility investigation). DD-60 remains UNDECIDED: MT5 is not selected as the Observer's provider. No application runtime dependency or adapter is introduced. The experiment is confined to a disposable Python environment on a GitHub-hosted Windows runner, on branch `spike/mt5-import-surface`, based on `183203307169f41ce40e035fe19f1d0a570e3e16`.

```text
INSTALL_IMPORT_SURFACE = SEE_EXACT_HEAD_RUN_EVIDENCE
DD_60_PROVIDER_SELECTION = UNDECIDED
DD_61_END_TO_END_COMPATIBILITY = NOT_PROVEN
DUAL_USE_11_CONDITIONS = NOT_PROVEN
TERMINAL_CONNECTION = NOT_EXECUTED
SYMBOL_DISCOVERY = NOT_EXECUTED
TICK_RETRIEVAL = NOT_EXECUTED
CANDLE_RETRIEVAL = NOT_EXECUTED
HEARTBEAT = NOT_EXECUTED
RECONNECT = NOT_EXECUTED
TRADING = NOT_EXECUTED
```

The controlling contract is [0F-E section 9](../../foundation/0F-E_sprint1_entry_contract.md#9-provider--sdk-dual-use-admissibility-contract), containing eleven cumulative conditions. [DD-60 and DD-61](../../foundation/0F-B_deferred_decision_register.md) remain subject to the before-first-material-dependency decision deadline. This installation experiment is not an architecture selection, compatibility approval, provider admission or proof of the eleven conditions.

## Reproducible package boundary

[MetaTrader5 5.0.6180 on PyPI](https://pypi.org/project/metatrader5/5.0.6180/) publishes a CPython 3.12 Windows x86-64 wheel, uploaded 2026-09-05, with 47,969 bytes. Its SHA256 is `7870e1497026d3f0d9b296904e3bcef48292d5b665b1fff1fb44efd41631b998`. [Release metadata](https://pypi.org/pypi/metatrader5/5.0.6180/json) declares `numpy>=1.7`.

The experiment fixes [NumPy 1.26.4](https://pypi.org/project/numpy/1.26.4/) as a controlled dependency variable, not as an application dependency or preferred production version. Its CPython 3.12 Windows x86-64 wheel SHA256 is `08beddf13648eb95f8d867350f6a018a4be2e5ad54c8d8caed89ebca558b2818`. Both requirements are fully pinned and pip enforces hashes and binary-only installation. No terminal installer is downloaded.

The workflow `.github/workflows/mt5-import-spike.yml` creates a disposable venv under the GitHub runner's temporary directory. It does not install the BTG AI Trader package, change `pyproject.toml`, use self-hosted runners, access user-machine state or receive trading secrets. GitHub permissions are `contents: read`; checkout credentials are not persisted.

## Probe semantics

The source `spikes/mt5-import/import_surface.py` imports the package, reads distribution/module version metadata and reports callable presence of explicitly enumerated observation, connection and financial API names. The probe invokes none of those SDK functions. Presence does not establish usability, permissions, absence of effects within vendor import code, or actual market-data compatibility.

In particular, it does not call `initialize`, `login`, `account_info`, `terminal_info`, `shutdown`, data functions, order functions or calculation functions. No connection/retrieval/trading example from vendor documentation is executed. SDK presence stays confined to the spike and does not expose a service to the Observer.

## Automatic terminal/account behavior and follow-up boundary

[Official initialize documentation](https://www.mql5.com/en/docs/python_metatrader5/mt5initialize_py) states that initialization can find and launch a terminal and can default to the last account and stored password/server. Therefore, omitting credentials from a call is not evidence of read-only or account-free behavior. This experiment does not call initialization.

Before any future terminal-connected experiment, provision a separately authorized disposable remote Windows terminal environment with explicit read-only authority, no saved trading identity and no user-computer dependency. Validate the full eleven-condition contract and structural isolation before connecting; broker permission toggles or a disabled trading flag alone are insufficient. If the environment or authority is unavailable, stop at the import evidence and record that blocker. No such environment is provisioned by this spike.

## Evidence policy

The draft PR must link the exact head, GitHub Actions run, installation/import results and actual surface report. A successful import is only partial evidence for the tested Windows/Python/NumPy/package combination. It cannot prove market discovery, subscription, timestamps, ticks, candles, heartbeat, reconnect, execution impossibility or dual-use admission. Keep this PR draft and unmerged; preserve all eleven conditions as NOT_PROVEN.

## Recorded evidence — 2026-09-13

[Run 34780123929](https://github.com/paulobmcosta-creator/btg-ai-trader/actions/runs/34780123929), [job 103785485461](https://github.com/paulobmcosta-creator/btg-ai-trader/actions/runs/34780123929/job/103785485461), tested exact head `7e725a5aaa5e68ccb165157221f8883c2fc8e823` successfully. The runner reported Windows-2022Server-10.0.20348-SP0 and Python 3.12.10. Both hash-locked wheels installed, `pip check` reported no broken requirements, and the import probe reported MetaTrader5 module/distribution 5.0.6180 with NumPy 1.26.4 inside the disposable venv.

All 24 enumerated symbols were callable-present: eleven observation symbols, five connection/account symbols and eight financial symbols, including `order_send`. No SDK function is invoked by the probe source; its empty invocation field is a source-declared boundary, not independent syscall instrumentation. Native vendor import behavior was not traced. No terminal connection or data retrieval is established by these observations.

The initial [run 34780050837](https://github.com/paulobmcosta-creator/btg-ai-trader/actions/runs/34780050837) failed before jobs started because the binary-only pip argument needed a YAML block scalar. Commit `7e725a5` corrected the workflow representation; no check or hash enforcement was removed. Current-head evidence is maintained on the draft [PR #11](https://github.com/paulobmcosta-creator/btg-ai-trader/pull/11). Later commits are not covered by the historical run cited above.

The spike stops here. All eleven admissibility conditions remain NOT_PROVEN, DD-60 remains UNDECIDED, and no remote terminal/read-only credential environment has been provisioned for the next experiment. Connection, discovery, ticks, candles, heartbeat and real reconnect remain NOT_EXECUTED.
