# Runtime-validation tests intentionally pass malformed values through typed constructors.
# mypy: disable-error-code="arg-type,assignment,unused-ignore"

from __future__ import annotations

import dataclasses
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from types import MappingProxyType
from zoneinfo import ZoneInfo

import pytest

from btg_ai_trader.observer.identity import TradableInstrumentId
from btg_ai_trader.risk_engine import EconomicDirection as RiskEconomicDirection
from btg_ai_trader.strategy import (
    CandidateStrategy,
    ComparisonOperator,
    DecisionOpportunity,
    DecisionReason,
    EconomicDirection,
    EconomicObjective,
    StrategyDecision,
    StrategyDisposition,
    StrategyEvaluationResult,
    StrategyEvidenceQuality,
    StrategyRule,
    TradeIntent,
    evaluate_strategy,
    to_risk_proposal,
    verify_deterministic_equivalence,
)

INSTRUMENT = TradableInstrumentId("11111111-1111-1111-1111-111111111111")
OTHER_INSTRUMENT = TradableInstrumentId("22222222-2222-2222-2222-222222222222")


def dt(seconds: int = 0) -> datetime:
    return datetime(2026, 10, 4, 12, 0, tzinfo=UTC) + timedelta(seconds=seconds)


def objective(direction: EconomicDirection = EconomicDirection.INCREASE_LONG) -> EconomicObjective:
    return EconomicObjective(direction, Decimal("10"), "shares", Decimal("200"), "BRL")


def rule(
    rule_id: str = "long",
    *,
    priority: int = 10,
    signal_name: str = "score",
    operator: ComparisonOperator = ComparisonOperator.GE,
    threshold: Decimal = Decimal("0.7"),
    direction: EconomicDirection = EconomicDirection.INCREASE_LONG,
) -> StrategyRule:
    return StrategyRule(rule_id, priority, signal_name, operator, threshold, objective(direction))


def candidate(
    *,
    rules: tuple[StrategyRule, ...] | None = None,
    max_age: int = 5,
) -> CandidateStrategy:
    return CandidateStrategy(
        name="threshold-alpha",
        version="1",
        code_revision="abc123",
        instrument_id=INSTRUMENT,
        portfolio_id="paper-candidate-portfolio",
        input_spec_digest="input-spec-1",
        max_evidence_age_seconds=max_age,
        rules=rules or (rule(),),
    )


def opportunity(
    *,
    instrument_id: TradableInstrumentId = INSTRUMENT,
    portfolio_id: str = "paper-candidate-portfolio",
    input_spec_digest: str = "input-spec-1",
    quality: StrategyEvidenceQuality = StrategyEvidenceQuality.VALID,
    signals: dict[str, Decimal] | None = None,
    event_time: datetime | None = None,
    knowledge_time: datetime | None = None,
    decision_time: datetime | None = None,
) -> DecisionOpportunity:
    return DecisionOpportunity(
        opportunity_id="opp-1",
        instrument_id=instrument_id,
        portfolio_id=portfolio_id,
        event_time=event_time or dt(0),
        knowledge_time=knowledge_time or dt(1),
        decision_time=decision_time or dt(2),
        input_spec_digest=input_spec_digest,
        signals={"score": Decimal("0.8")} if signals is None else signals,
        evidence_quality=quality,
        source_digest="market-evidence-1",
    )


def test_objective_is_immutable_deterministic_and_validated() -> None:
    first = objective()
    second = objective()
    assert first.objective_digest == second.objective_digest
    with pytest.raises(dataclasses.FrozenInstanceError):
        first.quantity_unit = "contracts"  # type: ignore[misc]

    with pytest.raises(ValueError, match="direction"):
        EconomicObjective(
            "LONG", Decimal("1"), "shares", Decimal("1"), "BRL"  # type: ignore[arg-type]
        )
    for bad in (1, Decimal("NaN"), Decimal("0"), Decimal("-1")):
        with pytest.raises(ValueError, match="requested_quantity"):
            EconomicObjective(
                EconomicDirection.INCREASE_LONG,
                bad,  # type: ignore[arg-type]
                "shares",
                Decimal("1"),
                "BRL",
            )
    for bad in ("", " shares "):
        with pytest.raises(ValueError, match="quantity_unit"):
            EconomicObjective(
                EconomicDirection.INCREASE_LONG,
                Decimal("1"),
                bad,
                Decimal("1"),
                "BRL",
            )
    for bad in (1, Decimal("NaN"), Decimal("0"), Decimal("-1")):
        with pytest.raises(ValueError, match="requested_exposure"):
            EconomicObjective(
                EconomicDirection.INCREASE_LONG,
                Decimal("1"),
                "shares",
                bad,  # type: ignore[arg-type]
                "BRL",
            )
    with pytest.raises(ValueError, match="exposure_unit"):
        EconomicObjective(
            EconomicDirection.INCREASE_LONG,
            Decimal("1"),
            "shares",
            Decimal("1"),
            " BRL",
        )


def test_rule_validation_and_digest() -> None:
    assert rule().rule_digest == rule().rule_digest
    with pytest.raises(ValueError, match="rule_id"):
        rule(" bad ")
    for bad in (True, "1", -1):
        with pytest.raises(ValueError, match="priority"):
            StrategyRule(
                "r",
                bad,  # type: ignore[arg-type]
                "score",
                ComparisonOperator.GE,
                Decimal("1"),
                objective(),
            )
    with pytest.raises(ValueError, match="signal_name"):
        StrategyRule("r", 1, "", ComparisonOperator.GE, Decimal("1"), objective())
    with pytest.raises(ValueError, match="operator"):
        StrategyRule("r", 1, "score", "GE", Decimal("1"), objective())  # type: ignore[arg-type]
    for bad in (1, Decimal("NaN")):
        with pytest.raises(ValueError, match="threshold"):
            StrategyRule(
                "r",
                1,
                "score",
                ComparisonOperator.GE,
                bad,  # type: ignore[arg-type]
                objective(),
            )
    with pytest.raises(ValueError, match="objective"):
        StrategyRule(
            "r",
            1,
            "score",
            ComparisonOperator.GE,
            Decimal("1"),
            object(),  # type: ignore[arg-type]
        )


def test_candidate_canonicalizes_rules_and_validates_identity() -> None:
    first_rule = rule("first", priority=1, signal_name="a")
    second_rule = rule("second", priority=2, signal_name="b")
    left = candidate(rules=(second_rule, first_rule))
    right = candidate(rules=(first_rule, second_rule))
    assert left.rules == (first_rule, second_rule)
    assert left.required_signals == ("a", "b")
    assert left.candidate_digest == right.candidate_digest
    assert left.candidate_id.startswith("strategy:threshold-alpha:")

    base = dict(
        name="s",
        version="1",
        code_revision="rev",
        instrument_id=INSTRUMENT,
        portfolio_id="p",
        input_spec_digest="spec",
        max_evidence_age_seconds=1,
        rules=(rule(),),
    )
    for key in ("name", "version", "code_revision", "portfolio_id", "input_spec_digest"):
        bad = dict(base)
        bad[key] = " bad "
        with pytest.raises(ValueError, match=key):
            CandidateStrategy(**bad)  # type: ignore[arg-type]
    bad = dict(base, instrument_id="instrument")
    with pytest.raises(ValueError, match="instrument_id"):
        CandidateStrategy(**bad)  # type: ignore[arg-type]
    for value in (True, "1", -1):
        bad = dict(base, max_evidence_age_seconds=value)
        with pytest.raises(ValueError, match="max_evidence_age_seconds"):
            CandidateStrategy(**bad)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="at least one"):
        CandidateStrategy(**dict(base, rules=()))
    with pytest.raises(ValueError, match="only StrategyRule"):
        CandidateStrategy(**dict(base, rules=(object(),)))  # type: ignore[arg-type]
    same_id_a = rule("dup", priority=1)
    same_id_b = rule("dup", priority=2)
    with pytest.raises(ValueError, match="rule_id"):
        CandidateStrategy(**dict(base, rules=(same_id_a, same_id_b)))
    same_priority_a = rule("a", priority=1)
    same_priority_b = rule("b", priority=1)
    with pytest.raises(ValueError, match="priorities"):
        CandidateStrategy(**dict(base, rules=(same_priority_a, same_priority_b)))


def test_opportunity_causal_boundary_freezes_signals_and_validates() -> None:
    first = opportunity(signals={"z": Decimal("2"), "a": Decimal("1")})
    second = opportunity(signals={"a": Decimal("1"), "z": Decimal("2")})
    assert isinstance(first.signals, MappingProxyType)
    assert first.opportunity_digest == second.opportunity_digest
    with pytest.raises(TypeError):
        first.signals["a"] = Decimal("3")  # type: ignore[index]

    args = dict(
        opportunity_id="opp",
        instrument_id=INSTRUMENT,
        portfolio_id="p",
        event_time=dt(0),
        knowledge_time=dt(1),
        decision_time=dt(2),
        input_spec_digest="spec",
        signals={"score": Decimal("1")},
        evidence_quality=StrategyEvidenceQuality.VALID,
        source_digest="src",
    )
    for key in ("opportunity_id", "portfolio_id", "input_spec_digest", "source_digest"):
        bad = dict(args)
        bad[key] = " bad "
        with pytest.raises(ValueError, match=key):
            DecisionOpportunity(**bad)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="instrument_id"):
        DecisionOpportunity(**dict(args, instrument_id="bad"))  # type: ignore[arg-type]
    for key in ("event_time", "knowledge_time", "decision_time"):
        bad = dict(args)
        bad[key] = datetime(2026, 10, 4, 12, 0)
        with pytest.raises(ValueError, match=key):
            DecisionOpportunity(**bad)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="event_time"):
        DecisionOpportunity(**dict(args, event_time=dt(2), knowledge_time=dt(1)))
    with pytest.raises(ValueError, match="knowledge_time"):
        DecisionOpportunity(**dict(args, knowledge_time=dt(3), decision_time=dt(2)))
    with pytest.raises(ValueError, match="signal_name"):
        DecisionOpportunity(**dict(args, signals={" bad ": Decimal("1")}))
    for value in (1, Decimal("NaN")):
        with pytest.raises(ValueError, match="signal"):
            DecisionOpportunity(**dict(args, signals={"score": value}))  # type: ignore[dict-item]
    with pytest.raises(ValueError, match="evidence_quality"):
        DecisionOpportunity(**dict(args, evidence_quality="VALID"))  # type: ignore[arg-type]


def test_engine_fail_closed_reasons() -> None:
    c = candidate()
    cases = (
        (opportunity(instrument_id=OTHER_INSTRUMENT), DecisionReason.CANDIDATE_INSTRUMENT_MISMATCH),
        (opportunity(portfolio_id="other"), DecisionReason.CANDIDATE_PORTFOLIO_MISMATCH),
        (opportunity(input_spec_digest="other"), DecisionReason.INPUT_SPEC_MISMATCH),
        (opportunity(quality=StrategyEvidenceQuality.UNKNOWN), DecisionReason.EVIDENCE_NOT_VALID),
        (
            opportunity(knowledge_time=dt(1), decision_time=dt(7)),
            DecisionReason.EVIDENCE_TOO_OLD,
        ),
        (opportunity(signals={}), DecisionReason.MISSING_REQUIRED_SIGNAL),
        (opportunity(signals={"score": Decimal("0.1")}), DecisionReason.NO_RULE_MATCHED),
    )
    for item, reason in cases:
        result = evaluate_strategy(c, item)
        assert result.decision.disposition is StrategyDisposition.NO_TRADE
        assert result.decision.reason_codes == (reason,)
        assert result.decision.matched_rule_id is None
        assert result.trade_intent is None
        assert result.decision.is_engine_issued


@pytest.mark.parametrize(
    ("operator", "value", "threshold", "matches"),
    [
        (ComparisonOperator.LT, "0.4", "0.5", True),
        (ComparisonOperator.LT, "0.5", "0.5", False),
        (ComparisonOperator.LE, "0.5", "0.5", True),
        (ComparisonOperator.LE, "0.6", "0.5", False),
        (ComparisonOperator.GE, "0.5", "0.5", True),
        (ComparisonOperator.GE, "0.4", "0.5", False),
        (ComparisonOperator.GT, "0.6", "0.5", True),
        (ComparisonOperator.GT, "0.5", "0.5", False),
    ],
)
def test_all_comparison_operators(
    operator: ComparisonOperator,
    value: str,
    threshold: str,
    matches: bool,
) -> None:
    c = candidate(rules=(rule(operator=operator, threshold=Decimal(threshold)),))
    result = evaluate_strategy(c, opportunity(signals={"score": Decimal(value)}))
    assert (result.decision.disposition is StrategyDisposition.PROPOSE_TRADE) is matches


def test_priority_is_deterministic_and_trade_intent_preserves_lineage() -> None:
    higher = rule("higher", priority=1, operator=ComparisonOperator.GE, threshold=Decimal("0.5"))
    lower = rule(
        "lower",
        priority=2,
        operator=ComparisonOperator.GE,
        threshold=Decimal("0.5"),
        direction=EconomicDirection.INCREASE_SHORT,
    )
    c = candidate(rules=(lower, higher))
    opp = opportunity(signals={"score": Decimal("0.9")})
    result = evaluate_strategy(c, opp)
    assert result.decision.disposition is StrategyDisposition.PROPOSE_TRADE
    assert result.decision.reason_codes == (DecisionReason.RULE_MATCHED,)
    assert result.decision.matched_rule_id == "higher"
    assert result.trade_intent is not None
    assert result.trade_intent.is_engine_issued
    assert result.trade_intent.decision_digest == result.decision.decision_digest
    assert result.trade_intent.candidate_digest == c.candidate_digest
    assert result.trade_intent.opportunity_digest == opp.opportunity_digest
    assert result.trade_intent.source_digest == result.decision.decision_digest
    assert verify_deterministic_equivalence(c, opp)
    assert evaluate_strategy(c, opp).result_digest == result.result_digest


def test_boundary_age_equal_to_limit_is_admissible() -> None:
    c = candidate(max_age=5)
    result = evaluate_strategy(c, opportunity(knowledge_time=dt(1), decision_time=dt(6)))
    assert result.decision.disposition is StrategyDisposition.PROPOSE_TRADE


def test_causal_order_uses_utc_instants_across_dst_fold() -> None:
    eastern = ZoneInfo("America/New_York")
    event_time = datetime(2026, 11, 1, 1, 30, tzinfo=eastern, fold=1)
    knowledge_time = datetime(2026, 11, 1, 1, 45, tzinfo=eastern, fold=0)
    decision_time = datetime(2026, 11, 1, 2, 0, tzinfo=eastern)

    with pytest.raises(ValueError, match="event_time"):
        opportunity(
            event_time=event_time,
            knowledge_time=knowledge_time,
            decision_time=decision_time,
        )


def test_evidence_age_uses_utc_instants_across_dst_fold() -> None:
    eastern = ZoneInfo("America/New_York")
    event_time = datetime(2026, 11, 1, 1, 40, tzinfo=eastern, fold=0)
    knowledge_time = datetime(2026, 11, 1, 1, 50, tzinfo=eastern, fold=0)
    decision_time = datetime(2026, 11, 1, 1, 55, tzinfo=eastern, fold=1)

    result = evaluate_strategy(
        candidate(max_age=300),
        opportunity(
            event_time=event_time,
            knowledge_time=knowledge_time,
            decision_time=decision_time,
        ),
    )

    assert result.decision.disposition is StrategyDisposition.NO_TRADE
    assert result.decision.reason_codes == (DecisionReason.EVIDENCE_TOO_OLD,)
    assert result.trade_intent is None


@pytest.mark.parametrize("direction", list(EconomicDirection))
def test_risk_adapter_maps_all_directions_without_losing_economic_objective(
    direction: EconomicDirection,
) -> None:
    c = candidate(rules=(rule(direction=direction),))
    result = evaluate_strategy(c, opportunity())
    assert result.trade_intent is not None
    proposal = to_risk_proposal(result.trade_intent)
    assert proposal.proposal_id == f"risk-proposal:{result.trade_intent.intent_digest[:24]}"
    assert proposal.instrument_id == result.trade_intent.instrument_id
    assert proposal.portfolio_id == result.trade_intent.portfolio_id
    assert proposal.direction is RiskEconomicDirection(direction.value)
    assert proposal.requested_quantity == result.trade_intent.objective.requested_quantity
    assert proposal.quantity_unit == result.trade_intent.objective.quantity_unit
    assert proposal.requested_exposure == result.trade_intent.objective.requested_exposure
    assert proposal.exposure_unit == result.trade_intent.objective.exposure_unit
    assert proposal.created_at == result.trade_intent.created_at
    assert proposal.source_digest == result.trade_intent.intent_digest


def test_risk_adapter_rejects_forged_intent() -> None:
    with pytest.raises(ValueError, match="engine-issued"):
        to_risk_proposal(object())  # type: ignore[arg-type]


def test_dataclass_replace_cannot_preserve_trade_intent_engine_trust() -> None:
    result = evaluate_strategy(candidate(), opportunity())
    assert result.trade_intent is not None
    intent = result.trade_intent

    clones = (
        dataclasses.replace(intent, objective=objective(EconomicDirection.INCREASE_SHORT)),
        dataclasses.replace(intent, instrument_id=OTHER_INSTRUMENT),
        dataclasses.replace(intent, portfolio_id="other"),
    )
    for clone in clones:
        assert not clone.is_engine_issued
        with pytest.raises(ValueError, match="engine-issued"):
            to_risk_proposal(clone)


def test_digest_validation_rejects_in_place_tampering_even_with_engine_token() -> None:
    result = evaluate_strategy(candidate(), opportunity())
    assert result.trade_intent is not None
    assert result.decision.is_engine_issued
    assert result.trade_intent.is_engine_issued

    object.__setattr__(result.decision, "candidate_digest", "tampered")
    object.__setattr__(result.trade_intent, "portfolio_id", "tampered")

    assert not result.decision.is_engine_issued
    assert not result.trade_intent.is_engine_issued
    with pytest.raises(ValueError, match="engine-issued"):
        to_risk_proposal(result.trade_intent)


def test_objective_content_tampering_invalidates_intent_and_risk_adapter() -> None:
    c = candidate()
    result = evaluate_strategy(c, opportunity())
    assert result.trade_intent is not None
    intent = result.trade_intent
    original_candidate_digest = c.candidate_digest
    original_objective_digest = intent.objective.objective_digest

    object.__setattr__(intent.objective, "requested_exposure", Decimal("999"))

    assert c.candidate_digest != original_candidate_digest
    assert intent.objective.objective_digest != original_objective_digest
    assert not intent.is_engine_issued
    with pytest.raises(ValueError, match="engine-issued"):
        to_risk_proposal(intent)


def test_strategy_decision_direct_construction_is_untrusted_and_validated() -> None:
    valid = dict(
        decision_id="d",
        candidate_id="c",
        candidate_digest="cd",
        opportunity_id="o",
        opportunity_digest="od",
        disposition=StrategyDisposition.NO_TRADE,
        reason_codes=(DecisionReason.NO_RULE_MATCHED,),
        matched_rule_id=None,
        decided_at=dt(2),
        decision_digest="dd",
    )
    forged = StrategyDecision(**valid)
    assert not forged.is_engine_issued
    for key in (
        "decision_id",
        "candidate_id",
        "candidate_digest",
        "opportunity_id",
        "opportunity_digest",
        "decision_digest",
    ):
        with pytest.raises(ValueError, match=key):
            StrategyDecision(**dict(valid, **{key: " bad "}))
    with pytest.raises(ValueError, match="disposition"):
        StrategyDecision(**dict(valid, disposition="NO_TRADE"))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="reason_codes"):
        StrategyDecision(**dict(valid, reason_codes=()))
    with pytest.raises(ValueError, match="reason_codes"):
        StrategyDecision(**dict(valid, reason_codes=("bad",)))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="NO_TRADE"):
        StrategyDecision(**dict(valid, matched_rule_id="rule"))
    with pytest.raises(ValueError, match="matched_rule_id"):
        StrategyDecision(**dict(valid, disposition=StrategyDisposition.PROPOSE_TRADE))
    with pytest.raises(ValueError, match="decided_at"):
        StrategyDecision(**dict(valid, decided_at=datetime(2026, 10, 4)))


def test_strategy_decision_issuer_recomputes_complete_outcome() -> None:
    c = candidate()
    low_score = opportunity(signals={"score": Decimal("0.1")})

    decision = StrategyDecision._issue(candidate=c, opportunity=low_score)

    assert decision.is_engine_issued
    assert decision.disposition is StrategyDisposition.NO_TRADE
    assert decision.reason_codes == (DecisionReason.NO_RULE_MATCHED,)
    assert decision.matched_rule_id is None
    with pytest.raises(ValueError, match="PROPOSE_TRADE"):
        TradeIntent._build(decision=decision, candidate=c, opportunity=low_score)

    mismatch = opportunity(instrument_id=OTHER_INSTRUMENT)
    mismatch_decision = StrategyDecision._issue(candidate=c, opportunity=mismatch)
    assert mismatch_decision.disposition is StrategyDisposition.NO_TRADE
    assert mismatch_decision.reason_codes == (DecisionReason.CANDIDATE_INSTRUMENT_MISMATCH,)


def test_trade_intent_direct_construction_is_untrusted_and_validated() -> None:
    valid = dict(
        intent_id="i",
        decision_digest="dd",
        candidate_id="c",
        candidate_digest="cd",
        opportunity_digest="od",
        instrument_id=INSTRUMENT,
        portfolio_id="p",
        objective=objective(),
        created_at=dt(2),
        source_digest="src",
        intent_digest="id",
    )
    forged = TradeIntent(**valid)
    assert not forged.is_engine_issued
    for key in (
        "intent_id",
        "decision_digest",
        "candidate_id",
        "candidate_digest",
        "opportunity_digest",
        "portfolio_id",
        "source_digest",
        "intent_digest",
    ):
        with pytest.raises(ValueError, match=key):
            TradeIntent(**dict(valid, **{key: " bad "}))
    with pytest.raises(ValueError, match="instrument_id"):
        TradeIntent(**dict(valid, instrument_id="bad"))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="objective"):
        TradeIntent(**dict(valid, objective=object()))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="created_at"):
        TradeIntent(**dict(valid, created_at=datetime(2026, 10, 4)))


def test_trade_intent_builder_binds_decision_candidate_and_opportunity() -> None:
    c = candidate()
    no_trade_opp = opportunity(signals={"score": Decimal("0.1")})
    no_trade = evaluate_strategy(c, no_trade_opp).decision
    forged = dataclasses.replace(no_trade)

    with pytest.raises(ValueError, match="engine-issued"):
        TradeIntent._build(decision=forged, candidate=c, opportunity=no_trade_opp)
    with pytest.raises(ValueError, match="PROPOSE_TRADE"):
        TradeIntent._build(decision=no_trade, candidate=c, opportunity=no_trade_opp)

    opp = opportunity()
    proposed = evaluate_strategy(c, opp).decision
    other_candidate = dataclasses.replace(c, portfolio_id="other")
    with pytest.raises(ValueError, match="candidate identity mismatch"):
        TradeIntent._build(decision=proposed, candidate=other_candidate, opportunity=opp)

    other_opp = dataclasses.replace(opp, source_digest="other-market-evidence")
    with pytest.raises(ValueError, match="opportunity identity mismatch"):
        TradeIntent._build(decision=proposed, candidate=c, opportunity=other_opp)


def test_evaluation_result_rejects_inconsistent_artifacts() -> None:
    c = candidate()
    opp = opportunity()
    valid = evaluate_strategy(c, opp)
    assert valid.trade_intent is not None

    forged_decision = dataclasses.replace(valid.decision)
    with pytest.raises(ValueError, match="decision must"):
        StrategyEvaluationResult(forged_decision, None)

    no_trade = evaluate_strategy(c, opportunity(signals={"score": Decimal("0.1")})).decision
    with pytest.raises(ValueError, match="NO_TRADE"):
        StrategyEvaluationResult(no_trade, valid.trade_intent)
    with pytest.raises(ValueError, match="requires engine-issued"):
        StrategyEvaluationResult(valid.decision, None)

    forged_intent = dataclasses.replace(valid.trade_intent)
    with pytest.raises(ValueError, match="requires engine-issued"):
        StrategyEvaluationResult(valid.decision, forged_intent)

    other_opp = dataclasses.replace(opp, source_digest="other-market-evidence")
    other_result = evaluate_strategy(c, other_opp)
    assert other_result.trade_intent is not None
    with pytest.raises(ValueError, match="decision_digest"):
        StrategyEvaluationResult(valid.decision, other_result.trade_intent)
