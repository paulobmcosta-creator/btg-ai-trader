"""Strict determinism verification: 100 repetitions must produce bit-exact identical results."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from btg_ai_trader.statistical_baselines.baselines import (
    HistoricalMeanBaseline,
    PersistenceBaseline,
)
from btg_ai_trader.statistical_baselines.boundaries import WalkForwardPlan
from btg_ai_trader.statistical_baselines.comparison import Comparator
from btg_ai_trader.statistical_baselines.domain import (
    EvaluationRole,
    StatisticalSample,
    TargetSemantics,
)
from btg_ai_trader.statistical_baselines.evaluation import StatisticalEvaluationEngine
from btg_ai_trader.statistical_baselines.provenance import StatisticalEvaluationManifest
from btg_ai_trader.statistical_baselines.splits import (
    EmbargoPolicy,
    PurgePolicy,
    SplitPlanConfig,
    WalkForwardPlanner,
    WindowPolicy,
)


def _build_dataset() -> list[StatisticalSample]:
    t0 = datetime(2026, 9, 1, 9, 0, tzinfo=UTC)
    samples = []
    # 20 samples with diverse values
    for i in range(20):
        f_t = t0 + timedelta(minutes=i * 10)
        t_t = f_t + timedelta(minutes=5)
        val = Decimal(f"{100 + (i * 3) % 17}.{i % 10}")
        samples.append(
            StatisticalSample(
                sample_id=f"sample_{i:03d}",
                feature_knowledge_time=f_t,
                target_knowledge_time=t_t,
                target_value=val,
                target_semantics=TargetSemantics.CONTINUOUS,
            )
        )
    return samples


def _build_plan() -> WalkForwardPlan:
    t0 = datetime(2026, 9, 1, 9, 0, tzinfo=UTC)
    t_end = datetime(2026, 9, 1, 13, 0, tzinfo=UTC)
    cfg = SplitPlanConfig(
        window_policy=WindowPolicy.EXPANDING,
        train_duration=timedelta(hours=1),
        validation_duration=timedelta(minutes=30),
        test_duration=timedelta(minutes=30),
        step_duration=timedelta(minutes=30),
    )
    return WalkForwardPlanner.generate_plan(t0, t_end, cfg, plan_id="plan_det_100")


def test_100_repetition_determinism() -> None:
    samples = _build_dataset()
    plan = _build_plan()
    purge_pol = PurgePolicy()
    embargo_pol = EmbargoPolicy()
    ref_timestamp = datetime(2026, 9, 1, 15, 0, tzinfo=UTC)

    first_manifest_digest: str | None = None
    first_mean_mae: Decimal | None = None
    first_persistence_mae: Decimal | None = None

    for _iteration in range(100):
        # Evaluate Mean baseline
        agg_mean = StatisticalEvaluationEngine.evaluate_candidate_on_plan(
            baseline_factory=HistoricalMeanBaseline,
            plan=plan,
            samples=samples,
            role=EvaluationRole.VALIDATION_SELECTION,
            purge_policy=purge_pol,
            embargo_policy=embargo_pol,
        )

        # Evaluate Persistence baseline
        agg_pers = StatisticalEvaluationEngine.evaluate_candidate_on_plan(
            baseline_factory=PersistenceBaseline,
            plan=plan,
            samples=samples,
            role=EvaluationRole.VALIDATION_SELECTION,
            purge_policy=purge_pol,
            embargo_policy=embargo_pol,
        )

        # Compare candidates
        comp = Comparator.compare_candidates(
            [agg_mean, agg_pers], metric_name="mean_mae", higher_is_better=False
        )

        mean_inst = HistoricalMeanBaseline()
        pers_inst = PersistenceBaseline()

        manifest = StatisticalEvaluationManifest.create(
            plan=plan,
            samples=samples,
            candidate_identities=[mean_inst.identity, pers_inst.identity],
            aggregate_results=[agg_mean, agg_pers],
            comparison_results=[comp],
            code_revision="git:s4_det_test",
            execution_timestamp=ref_timestamp,
        )

        assert manifest.verify_manifest_integrity() is True

        if first_manifest_digest is None:
            first_manifest_digest = manifest.provenance.manifest_digest
            first_mean_mae = agg_mean.aggregate_metrics["mean_mae"]
            first_persistence_mae = agg_pers.aggregate_metrics["mean_mae"]
        else:
            # Must match bit-for-bit with run 1
            assert manifest.provenance.manifest_digest == first_manifest_digest
            assert agg_mean.aggregate_metrics["mean_mae"] == first_mean_mae
            assert agg_pers.aggregate_metrics["mean_mae"] == first_persistence_mae
