"""Tests for the optional verified Sprint 5 -> Sprint 6 evidence adapter."""

from __future__ import annotations

import dataclasses
from decimal import Decimal

import pytest

import btg_ai_trader.ml_engine.provenance as ml_provenance
from btg_ai_trader.ml_engine.domain import EvaluationScope, ModelEvaluationDisposition
from btg_ai_trader.ml_engine.evaluation import FoldModelEvaluation, ModelEvaluationReport
from btg_ai_trader.scenario_engine.core import ScenarioInputBoundary
from btg_ai_trader.scenario_engine.ml_adapter import snapshot_from_s5
from btg_ai_trader.statistical_baselines.domain import EvaluationRole, TargetSemantics
from btg_ai_trader.statistical_baselines.evaluation import FoldAggregationPolicy
from btg_ai_trader.statistical_baselines.metrics import DEFAULT_NUMERIC_POLICY


def training_manifest(
    *,
    candidate_id: str = "candidate-1",
    target_contract_digest: str = "target-1",
    code_revision: str = "rev-s5",
    verified: bool = True,
) -> ml_provenance.ModelTrainingManifest:
    manifest = ml_provenance.ModelTrainingManifest(
        boundary_digest="b" * 64,
        candidate_id=candidate_id,
        fitted_feature_pipeline_digest="f" * 64,
        model_state_digest="m" * 64,
        target_contract_digest=target_contract_digest,
        rng_context=None,
        environment_fingerprint=ml_provenance.EnvironmentFingerprint.current(),
        code_revision=code_revision,
        numeric_policy=DEFAULT_NUMERIC_POLICY,
    )
    if verified:
        object.__setattr__(manifest, "_verification_token", ml_provenance._MANIFEST_VERIFICATION_TOKEN)
    return manifest


def report(
    *,
    candidate_id: str = "candidate-1",
    role: EvaluationRole = EvaluationRole.VALIDATION_SELECTION,
    protected_boundary_id: str = "",
) -> ModelEvaluationReport:
    return ModelEvaluationReport(
        candidate_id=candidate_id,
        evaluation_scope=EvaluationScope.MODEL,
        role=role,
        target_semantics=TargetSemantics.CONTINUOUS,
        fold_evaluations=(
            FoldModelEvaluation(
                fold_id="f1",
                role=role,
                metrics={"mae": Decimal("1.5")},
                sample_count=1,
            ),
        ),
        mean_metrics={"mae": Decimal("1.5")},
        aggregation_policy=FoldAggregationPolicy.EQUAL_FOLD,
        numeric_policy=DEFAULT_NUMERIC_POLICY,
        dataset_digest="d" * 64,
        plan_digest="p" * 64,
        target_contract_digest="target-1",
        experimental_context_fingerprint="x" * 64,
        disposition=ModelEvaluationDisposition.INCONCLUSIVE,
        protected_boundary_id=protected_boundary_id,
    )


def test_snapshot_from_s5_verified_evidence() -> None:
    manifest = training_manifest()
    snapshot = snapshot_from_s5(report(), (manifest,))
    assert snapshot.is_verified
    boundary = ScenarioInputBoundary.from_model_snapshot(
        snapshot,
        scenario_code_revision="rev-s6",
    )
    assert boundary.source_artifact_id == "candidate-1"
    assert boundary.protected_boundary_id is None
    protected = snapshot_from_s5(
        report(role=EvaluationRole.PROTECTED_TEST, protected_boundary_id="pb-s5"),
        (manifest,),
    )
    assert protected.protected_boundary_id == "pb-s5"


def test_snapshot_from_s5_fails_closed_on_invalid_upstream_evidence() -> None:
    manifest = training_manifest()
    with pytest.raises(TypeError, match="ModelEvaluationReport"):
        snapshot_from_s5(object(), (manifest,))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="MODEL evaluation scope"):
        snapshot_from_s5(
            dataclasses.replace(report(), evaluation_scope=EvaluationScope.STRATEGY),
            (manifest,),
        )
    with pytest.raises(ValueError, match="validation or protected"):
        snapshot_from_s5(report(role=EvaluationRole.DEVELOPMENT), (manifest,))
    with pytest.raises(ValueError, match="fold evaluation roles"):
        snapshot_from_s5(
            dataclasses.replace(
                report(),
                fold_evaluations=(
                    FoldModelEvaluation(
                        fold_id="f1",
                        role=EvaluationRole.PROTECTED_TEST,
                        metrics={},
                        sample_count=0,
                    ),
                ),
            ),
            (manifest,),
        )
    with pytest.raises(ValueError, match="requires protected_boundary_id"):
        snapshot_from_s5(report(role=EvaluationRole.PROTECTED_TEST), (manifest,))
    with pytest.raises(ValueError, match="non-protected"):
        snapshot_from_s5(report(protected_boundary_id="unexpected"), (manifest,))
    with pytest.raises(ValueError, match="at least one verified"):
        snapshot_from_s5(report(), ())
    with pytest.raises(ValueError, match="verified ml_provenance.ModelTrainingManifest"):
        snapshot_from_s5(report(), (training_manifest(verified=False),))
    with pytest.raises(ValueError, match="candidate identities differ"):
        snapshot_from_s5(report(), (training_manifest(candidate_id="other"),))
    with pytest.raises(ValueError, match="target contracts differ"):
        snapshot_from_s5(report(), (training_manifest(target_contract_digest="other"),))
    with pytest.raises(ValueError, match="numeric policies differ"):
        snapshot_from_s5(
            report(),
            (
                dataclasses.replace(
                    manifest,
                    numeric_policy=dataclasses.replace(
                        DEFAULT_NUMERIC_POLICY,
                        precision=20,
                    ),
                ),
            ),
        )
    with pytest.raises(ValueError, match="share one code revision"):
        snapshot_from_s5(
            report(),
            (manifest, training_manifest(code_revision="other")),
        )
    unverified = dataclasses.replace(manifest)
    assert not unverified.is_verified
    with pytest.raises(ValueError, match="verified ml_provenance.ModelTrainingManifest"):
        snapshot_from_s5(report(), (unverified,))
