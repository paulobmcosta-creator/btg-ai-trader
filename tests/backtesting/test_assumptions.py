"""Tests for backtesting assumptions module."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from btg_ai_trader.backtesting.assumptions import (
    EconomicAssumptions,
    ExecutionPolicy,
    FeeSchedule,
    FixedBpsSlippageModel,
    FixedPointsSlippageModel,
    LatencyModel,
    SpreadModel,
    ZeroSlippageModel,
)
from btg_ai_trader.backtesting.domain import Side


def test_spread_model_valid() -> None:
    model = SpreadModel(require_positive_spread=True, max_spread=Decimal("2.0"))

    # BUY consumes Ask
    price, reason = model.resolve_executable_price(Side.BUY, Decimal("100.0"), Decimal("100.5"))
    assert price == Decimal("100.5")
    assert reason == "ASK_CONSUMED"

    # SELL consumes Bid
    price, reason = model.resolve_executable_price(Side.SELL, Decimal("100.0"), Decimal("100.5"))
    assert price == Decimal("100.0")
    assert reason == "BID_CONSUMED"


def test_spread_model_edge_cases() -> None:
    model = SpreadModel(require_positive_spread=True, max_spread=Decimal("1.0"))

    # Missing quote
    price, reason = model.resolve_executable_price(Side.BUY, None, Decimal("100.5"))
    assert price is None and reason == "MISSING_QUOTE"

    price, reason = model.resolve_executable_price(Side.BUY, Decimal("100.0"), None)
    assert price is None and reason == "MISSING_QUOTE"

    # Non-positive prices
    price, reason = model.resolve_executable_price(Side.BUY, Decimal("0"), Decimal("100.5"))
    assert price is None and reason == "NON_POSITIVE_PRICE"

    # Non-positive spread (ask <= bid)
    price, reason = model.resolve_executable_price(Side.BUY, Decimal("100.5"), Decimal("100.0"))
    assert price is None and reason == "NON_POSITIVE_SPREAD"

    # Spread exceeds max
    price, reason = model.resolve_executable_price(Side.BUY, Decimal("100.0"), Decimal("102.0"))
    assert price is None and reason == "SPREAD_EXCEEDS_MAX"

    # require_positive_spread=False is strictly rejected
    with pytest.raises(ValueError, match="require_positive_spread=False is forbidden"):
        SpreadModel(require_positive_spread=False, max_spread=None)

    # Invalid max_spread
    with pytest.raises(ValueError, match="max_spread must be Decimal or None"):
        SpreadModel(max_spread="bad")  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="max_spread must be positive"):
        SpreadModel(max_spread=Decimal("0"))

    # Invalid price types
    with pytest.raises(ValueError, match="bid and ask must be Decimal"):
        model.resolve_executable_price(Side.BUY, 100.0, Decimal("101.0"))  # type: ignore[arg-type]

    # Unrecognized side
    with pytest.raises(ValueError, match="unrecognized side"):
        model.resolve_executable_price("UNKNOWN", Decimal("100.0"), Decimal("101.0"))  # type: ignore[arg-type]


def test_zero_slippage_model() -> None:
    model = ZeroSlippageModel()
    price, slip = model.apply_slippage(Side.BUY, Decimal("100.0"))
    assert price == Decimal("100.0")
    assert slip == Decimal("0")

    with pytest.raises(ValueError, match="positive Decimal"):
        model.apply_slippage(Side.BUY, Decimal("-10.0"))


def test_fixed_points_slippage_model() -> None:
    model = FixedPointsSlippageModel(adverse_points=Decimal("0.5"))

    # BUY slips higher
    price, slip = model.apply_slippage(Side.BUY, Decimal("100.0"))
    assert price == Decimal("100.5")
    assert slip == Decimal("0.5")

    # SELL slips lower
    price, slip = model.apply_slippage(Side.SELL, Decimal("100.0"))
    assert price == Decimal("99.5")
    assert slip == Decimal("0.5")

    # Extreme SELL floor: silent clamp removed, non-positive price raises ValueError
    with pytest.raises(ValueError, match="implies non-positive fill price"):
        model.apply_slippage(Side.SELL, Decimal("0.2"))

    with pytest.raises(ValueError, match="adverse_points must be Decimal"):
        FixedPointsSlippageModel(adverse_points=0.5)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="adverse_points cannot be negative"):
        FixedPointsSlippageModel(adverse_points=Decimal("-0.1"))

    with pytest.raises(ValueError, match="positive Decimal"):
        model.apply_slippage(Side.BUY, Decimal("0"))

    with pytest.raises(ValueError, match="unrecognized side"):
        model.apply_slippage("BAD", Decimal("100"))  # type: ignore[arg-type]


def test_fixed_bps_slippage_model() -> None:
    model = FixedBpsSlippageModel(bps=Decimal("10"))  # 10 bps = 0.1%

    # BUY: 100 + 0.1 = 100.1
    p_buy, s_buy = model.apply_slippage(Side.BUY, Decimal("100.0"))
    assert p_buy == Decimal("100.100")
    assert s_buy == Decimal("0.100")

    # SELL: 100 - 0.1 = 99.9
    p_sell, s_sell = model.apply_slippage(Side.SELL, Decimal("100.0"))
    assert p_sell == Decimal("99.900")
    assert s_sell == Decimal("0.100")

    with pytest.raises(ValueError, match="bps must be Decimal"):
        FixedBpsSlippageModel(bps=10)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="bps cannot be negative"):
        FixedBpsSlippageModel(bps=Decimal("-1"))

    with pytest.raises(ValueError, match="positive Decimal"):
        model.apply_slippage(Side.BUY, Decimal("-5"))

    with pytest.raises(ValueError, match="unrecognized side"):
        model.apply_slippage("BAD", Decimal("100"))  # type: ignore[arg-type]


def test_fee_schedule() -> None:
    schedule = FeeSchedule(
        schedule_id="test_b3",
        fixed_per_order=Decimal("2.50"),
        per_unit=Decimal("0.25"),
        bps_rate=Decimal("2.5"),  # 2.5 bps = 0.025%
        currency="BRL",
    )
    # qty=10, price=100, multiplier=1 => notional = 1000
    # fixed = 2.50
    # unit = 0.25 * 10 = 2.50
    # bps = 1000 * 2.5 / 10000 = 0.25
    # total = 5.25
    fee = schedule.compute_fee(
        quantity=Decimal("10"),
        fill_price=Decimal("100.0"),
        money_per_price_unit=Decimal("1.0"),
    )
    assert fee == Decimal("5.250")


def test_fee_schedule_validation() -> None:
    with pytest.raises(ValueError, match="schedule_id"):
        FeeSchedule(schedule_id="")

    with pytest.raises(ValueError, match="currency"):
        FeeSchedule(schedule_id="valid", currency="")

    with pytest.raises(ValueError, match="fixed_per_order must be nonnegative Decimal"):
        FeeSchedule(schedule_id="valid", fixed_per_order=Decimal("-1"))

    with pytest.raises(ValueError, match="per_unit must be nonnegative Decimal"):
        FeeSchedule(schedule_id="valid", per_unit=Decimal("-1"))

    with pytest.raises(ValueError, match="bps_rate must be nonnegative Decimal"):
        FeeSchedule(schedule_id="valid", bps_rate=Decimal("-1"))

    sched = FeeSchedule(schedule_id="valid")
    with pytest.raises(ValueError, match="must be positive"):
        sched.compute_fee(Decimal("0"), Decimal("100"), Decimal("1"))


def test_latency_model() -> None:
    model = LatencyModel(decision_latency_us=5000, transit_latency_us=2500)
    t_dec = datetime(2026, 9, 16, 10, 0, 0, 0, tzinfo=UTC)
    t_ready = datetime(2026, 9, 16, 10, 0, 0, 1000, tzinfo=UTC)

    sim_ready, sim_arrival = model.apply_latency(t_dec, t_ready)
    # max(1000, 5000) = 5000us
    assert sim_ready == datetime(2026, 9, 16, 10, 0, 0, 5000, tzinfo=UTC)
    # 5000 + 2500 = 7500us
    assert sim_arrival == datetime(2026, 9, 16, 10, 0, 0, 7500, tzinfo=UTC)


def test_latency_model_validation() -> None:
    with pytest.raises(ValueError, match="decision_latency_us must be nonnegative integer"):
        LatencyModel(decision_latency_us=-1)

    with pytest.raises(ValueError, match="transit_latency_us must be nonnegative integer"):
        LatencyModel(transit_latency_us=-1)

    model = LatencyModel()
    t_dec = datetime(2026, 9, 16, 10, 0, 1, tzinfo=UTC)
    t_ready = datetime(2026, 9, 16, 10, 0, 0, tzinfo=UTC)
    with pytest.raises(ValueError, match="order_ready_time cannot precede decision_time"):
        model.apply_latency(t_dec, t_ready)


def test_execution_policy_and_economic_assumptions() -> None:
    default_policy = ExecutionPolicy()
    assert default_policy.max_quote_age_us is None

    policy = ExecutionPolicy(
        small_lot_max_quantity=Decimal("50"),
        allow_candle_fills=False,
        max_quote_age_us=1_000_000,
    )
    assert policy.small_lot_max_quantity == Decimal("50")

    with pytest.raises(ValueError, match="small_lot_max_quantity must be Decimal"):
        ExecutionPolicy(small_lot_max_quantity=50)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="small_lot_max_quantity must be positive"):
        ExecutionPolicy(small_lot_max_quantity=Decimal("0"))

    with pytest.raises(ValueError, match="must be positive integer"):
        ExecutionPolicy(max_quote_age_us=0)

    assumptions = EconomicAssumptions(
        assumptions_id="assumptions_v1",
        spread_model=SpreadModel(),
        slippage_model=ZeroSlippageModel(),
        fee_schedule=FeeSchedule("default"),
        latency_model=LatencyModel(),
        execution_policy=policy,
    )
    assert assumptions.assumptions_id == "assumptions_v1"

    with pytest.raises(ValueError, match="assumptions_id"):
        EconomicAssumptions(
            assumptions_id="",
            spread_model=SpreadModel(),
            slippage_model=ZeroSlippageModel(),
            fee_schedule=FeeSchedule("default"),
            latency_model=LatencyModel(),
            execution_policy=policy,
        )

    with pytest.raises(ValueError, match="spread_model"):
        EconomicAssumptions(
            assumptions_id="valid",
            spread_model="bad",  # type: ignore[arg-type]
            slippage_model=ZeroSlippageModel(),
            fee_schedule=FeeSchedule("default"),
            latency_model=LatencyModel(),
            execution_policy=policy,
        )

    with pytest.raises(ValueError, match="slippage_model"):
        EconomicAssumptions(
            assumptions_id="valid",
            spread_model=SpreadModel(),
            slippage_model="bad",  # type: ignore[arg-type]
            fee_schedule=FeeSchedule("default"),
            latency_model=LatencyModel(),
            execution_policy=policy,
        )

    class CustomSlippageModel:
        def apply_slippage(self, side: Side, price: Decimal) -> tuple[Decimal, Decimal]:
            return price, Decimal("0")

    with pytest.raises(ValueError, match="slippage_model must be ZeroSlippageModel"):
        EconomicAssumptions(
            assumptions_id="valid",
            spread_model=SpreadModel(),
            slippage_model=CustomSlippageModel(),
            fee_schedule=FeeSchedule("default"),
            latency_model=LatencyModel(),
            execution_policy=policy,
        )

    with pytest.raises(ValueError, match="fee_schedule"):
        EconomicAssumptions(
            assumptions_id="valid",
            spread_model=SpreadModel(),
            slippage_model=ZeroSlippageModel(),
            fee_schedule="bad",  # type: ignore[arg-type]
            latency_model=LatencyModel(),
            execution_policy=policy,
        )

    with pytest.raises(ValueError, match="latency_model"):
        EconomicAssumptions(
            assumptions_id="valid",
            spread_model=SpreadModel(),
            slippage_model=ZeroSlippageModel(),
            fee_schedule=FeeSchedule("default"),
            latency_model="bad",  # type: ignore[arg-type]
            execution_policy=policy,
        )

    with pytest.raises(ValueError, match="execution_policy"):
        EconomicAssumptions(
            assumptions_id="valid",
            spread_model=SpreadModel(),
            slippage_model=ZeroSlippageModel(),
            fee_schedule=FeeSchedule("default"),
            latency_model=LatencyModel(),
            execution_policy="bad",  # type: ignore[arg-type]
        )
