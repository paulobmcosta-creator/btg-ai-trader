"""Unit tests for evaluation provenance, input boundary, and manifests."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from btg_ai_trader.statistical_baselines.boundaries import (
    EvaluationBoundary,
    TemporalFold,
    WalkForwardPlan,
)
from btg_ai_trader.statistical_baselines.comparison import ModelComparisonResult
from btg_ai_trader.statistical_baselines.domain import (
    CandidateIdentity,
    EvaluationRole,
    StatisticalSample,
    TargetSemantics,
)
from btg_ai_trader.statistical_baselines.evaluation import (
    AggregateEvaluationResult,
    FoldEvaluationResult,
)
from btg_ai_trader.statistical_baselines.provenance import (
    EvaluationProvenanceRecord,
    StatisticalEvaluationInputBoundary,
    StatisticalEvaluationManifest,
)


def _make_sample(
    sample_id: str,
    feature_time: datetime,
    target_time: datetime,
    target_val: Decimal | str,
    info_interval: tuple[datetime, datetime] | None = None,
) -> StatisticalSample:
    return StatisticalSample(
        sample_id=sample_id,
        feature_knowledge_time=feature_time,
        target_knowledge_time=target_time,
        target_value=target_val,
        target_semantics=TargetSemantics.CONTINUOUS,
        information_interval=info_interval,
    )


def test_input_boundary_validation() -> None:
    t0 = datetime(2026, 9, 1, 9, 0, tzinfo=UTC)
    t1 = datetime(2026, 9, 1, 10, 0, tzinfo=UTC)

    # Empty dataset
    with pytest.raises(ValueError, match="cannot be empty"):
        StatisticalEvaluationInputBoundary.validate_dataset([])

    s1 = _make_sample("s1", t0, t1, Decimal("10"))
    # Duplicate ID
    with pytest.raises(ValueError, match="Duplicate sample_id"):
        StatisticalEvaluationInputBoundary.validate_dataset([s1, s1])

    # Defensive check in validate_dataset for feature after target
    s_bypass = _make_sample("s_byp", t0, t1, Decimal("10"))
    object.__setattr__(s_bypass, "feature_knowledge_time", t1 + timedelta(hours=1))
    with pytest.raises(ValueError, match="feature_knowledge_time cannot be after"):
        StatisticalEvaluationInputBoundary.validate_dataset([s_bypass])


def test_input_boundary_sorting_and_digest() -> None:
    t0 = datetime(2026, 9, 1, 9, 0, tzinfo=UTC)
    t1 = datetime(2026, 9, 1, 10, 0, tzinfo=UTC)
    t2 = datetime(2026, 9, 1, 11, 0, tzinfo=UTC)

    s1 = _make_sample("s1", t0, t1, Decimal("10"), info_interval=(t0, t1))
    s2 = _make_sample("s2", t1, t2, Decimal("20"))

    # Passing out-of-order samples fails closed
    with pytest.raises(ValueError, match="out of chronological order"):
        StatisticalEvaluationInputBoundary.validate_dataset([s2, s1])

    valid_samples = StatisticalEvaluationInputBoundary.validate_dataset([s1, s2])
    assert valid_samples[0].sample_id == "s1"
    assert valid_samples[1].sample_id == "s2"

    digest1 = StatisticalEvaluationInputBoundary.compute_dataset_digest(valid_samples)
    assert len(digest1) == 64


def test_provenance_record_validation() -> None:
    t0 = datetime(2026, 9, 1, 9, 0, tzinfo=UTC)
    cid = CandidateIdentity("Mean", {}, TargetSemantics.CONTINUOUS, "v1.0.0")

    with pytest.raises(ValueError, match="plan_id cannot be empty"):
        EvaluationProvenanceRecord(
            plan_id="",
            plan_digest="d1",
            dataset_digest="d2",
            candidate_identities=(cid,),
            code_revision="v1.0.0",
            execution_timestamp=t0,
            manifest_digest="m1",
        )

    with pytest.raises(ValueError, match="plan_digest cannot be empty"):
        EvaluationProvenanceRecord(
            plan_id="p1",
            plan_digest="",
            dataset_digest="d2",
            candidate_identities=(cid,),
            code_revision="v1.0.0",
            execution_timestamp=t0,
            manifest_digest="m1",
        )

    with pytest.raises(ValueError, match="dataset_digest cannot be empty"):
        EvaluationProvenanceRecord(
            plan_id="p1",
            plan_digest="d1",
            dataset_digest="",
            candidate_identities=(cid,),
            code_revision="v1.0.0",
            execution_timestamp=t0,
            manifest_digest="m1",
        )

    with pytest.raises(ValueError, match="code_revision cannot be empty"):
        EvaluationProvenanceRecord(
            plan_id="p1",
            plan_digest="d1",
            dataset_digest="d2",
            candidate_identities=(cid,),
            code_revision="",
            execution_timestamp=t0,
            manifest_digest="m1",
        )

    with pytest.raises(ValueError, match="manifest_digest cannot be empty"):
        EvaluationProvenanceRecord(
            plan_id="p1",
            plan_digest="d1",
            dataset_digest="d2",
            candidate_identities=(cid,),
            code_revision="v1.0.0",
            execution_timestamp=t0,
            manifest_digest="",
        )

    with pytest.raises(ValueError, match="timezone-aware"):
        EvaluationProvenanceRecord(
            plan_id="p1",
            plan_digest="d1",
            dataset_digest="d2",
            candidate_identities=(cid,),
            code_revision="v1.0.0",
            execution_timestamp=datetime(2026, 9, 1, 9, 0),
            manifest_digest="m1",
        )


def test_manifest_creation_and_integrity() -> None:
    t0 = datetime(2026, 9, 1, 9, 0, tzinfo=UTC)
    t1 = datetime(2026, 9, 1, 11, 0, tzinfo=UTC)
    t2 = datetime(2026, 9, 1, 12, 0, tzinfo=UTC)
    t3 = datetime(2026, 9, 1, 13, 0, tzinfo=UTC)

    fold = TemporalFold(
        fold_id="f1",
        development_boundary=EvaluationBoundary(t0, t3, knowledge_cutoff=t0),
        training_boundary=EvaluationBoundary(t0, t1, knowledge_cutoff=t0),
        validation_boundary=EvaluationBoundary(t1, t2, knowledge_cutoff=t1),
        protected_evaluation_boundary=EvaluationBoundary(t2, t3, knowledge_cutoff=t2),
        knowledge_cutoff=t1,
        window_policy_name="EXPANDING",
    )
    plan = WalkForwardPlan(plan_id="wf_1", window_policy_name="EXPANDING", folds=(fold,))

    s1 = _make_sample("s1", t0, t0 + timedelta(minutes=30), Decimal("10"))
    samples = [s1]

    cid = CandidateIdentity("HistoricalMeanBaseline", {}, TargetSemantics.CONTINUOUS, "v1.0.0")
    f_res = FoldEvaluationResult(
        fold_id="f1",
        candidate_id=cid.candidate_id,
        evaluation_role=EvaluationRole.VALIDATION_SELECTION,
        metrics={"mae": Decimal("1.5")},
        sample_count=1,
        cold_start_count=0,
    )
    agg_res = AggregateEvaluationResult(
        candidate_id=cid.candidate_id,
        evaluation_role=EvaluationRole.VALIDATION_SELECTION,
        fold_results=(f_res,),
        aggregate_metrics={"mean_mae": Decimal("1.5")},
        total_samples=1,
        total_cold_starts=0,
    )
    comp_res = ModelComparisonResult(
        evaluation_role=EvaluationRole.VALIDATION_SELECTION,
        metric_name="mean_mae",
        higher_is_better=False,
        rankings=((cid.candidate_id, Decimal("1.5")),),
        winner_candidate_id=cid.candidate_id,
    )

    manifest = StatisticalEvaluationManifest.create(
        plan=plan,
        samples=samples,
        candidate_identities=[cid],
        aggregate_results=[agg_res],
        comparison_results=[comp_res],
        code_revision="git:s4_commit",
        execution_timestamp=t0,
    )

    # Verifies integrity
    assert manifest.verify_manifest_integrity() is True

    # Tampering with manifest provenance breaks integrity
    tampered_prov = EvaluationProvenanceRecord(
        plan_id="tampered_plan",
        plan_digest=manifest.provenance.plan_digest,
        dataset_digest=manifest.provenance.dataset_digest,
        candidate_identities=manifest.provenance.candidate_identities,
        code_revision=manifest.provenance.code_revision,
        execution_timestamp=manifest.provenance.execution_timestamp,
        manifest_digest=manifest.provenance.manifest_digest,
    )
    tampered_manifest = StatisticalEvaluationManifest(
        provenance=tampered_prov,
        aggregate_results=manifest.aggregate_results,
        comparison_results=manifest.comparison_results,
    )
    assert tampered_manifest.verify_manifest_integrity() is False

    # Canonical dictionary export
    can_dict = manifest.to_canonical_dict()
    assert can_dict["manifest_digest"] == manifest.provenance.manifest_digest
    assert len(can_dict["candidate_identities"]) == 1
