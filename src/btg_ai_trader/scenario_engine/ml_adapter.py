"""Optional Sprint 5 -> Sprint 6 evidence adapter.

Importing this module requires the optional ML dependency group. The Scenario Engine
core and package initializer do not import it.
"""

from __future__ import annotations

from collections.abc import Sequence

import btg_ai_trader.scenario_engine.core as scenario_core
from btg_ai_trader.ml_engine.evaluation import ModelEvaluationReport
from btg_ai_trader.ml_engine.provenance import ModelTrainingManifest
from btg_ai_trader.statistical_baselines.domain import EvaluationRole


def snapshot_from_s5(
    report: ModelEvaluationReport,
    training_manifests: Sequence[ModelTrainingManifest],
) -> scenario_core.ModelEvidenceSnapshot:
    """Issue a neutral verified snapshot from real Sprint 5 evidence objects."""
    if not isinstance(report, ModelEvaluationReport):
        raise TypeError("report must be ModelEvaluationReport")
    if report.evaluation_scope.value != "MODEL":
        raise ValueError("model evidence snapshot requires MODEL evaluation scope")
    if report.role not in {
        EvaluationRole.VALIDATION_SELECTION,
        EvaluationRole.PROTECTED_TEST,
    }:
        raise ValueError("S6 model evidence accepts validation or protected evaluation only")
    if any(fold.role is not report.role for fold in report.fold_evaluations):
        raise ValueError("model fold evaluation roles must match report role")

    protected_boundary_id = report.protected_boundary_id.strip() or None
    if report.role is EvaluationRole.PROTECTED_TEST:
        if protected_boundary_id is None:
            raise ValueError("PROTECTED_TEST model evidence requires protected_boundary_id")
    elif protected_boundary_id is not None:
        raise ValueError("non-protected model evidence cannot carry protected_boundary_id")

    manifests = tuple(training_manifests)
    if not manifests:
        raise ValueError("at least one verified ModelTrainingManifest is required")
    if any(
        not isinstance(manifest, ModelTrainingManifest) or not manifest.is_verified
        for manifest in manifests
    ):
        raise ValueError("all model training manifests must be verified ModelTrainingManifest")
    if any(manifest.candidate_id != report.candidate_id for manifest in manifests):
        raise ValueError("model report and training manifest candidate identities differ")
    if any(
        manifest.target_contract_digest != report.target_contract_digest
        for manifest in manifests
    ):
        raise ValueError("model report and training manifest target contracts differ")
    if any(manifest.numeric_policy != report.numeric_policy for manifest in manifests):
        raise ValueError("model report and training manifest numeric policies differ")

    revisions = {manifest.code_revision for manifest in manifests}
    if len(revisions) != 1:
        raise ValueError("model training manifests must share one code revision")
    source_code_revision = next(iter(revisions))
    source_manifest_ids = tuple(
        sorted(manifest.scientific_root_digest for manifest in manifests)
    )

    return scenario_core._issue_model_evidence_snapshot(
        candidate_id=report.candidate_id,
        evaluation_scope=report.evaluation_scope.value,
        evaluation_role=report.role,
        protected_boundary_id=protected_boundary_id,
        dataset_digest=report.dataset_digest,
        plan_digest=report.plan_digest,
        target_contract_digest=report.target_contract_digest,
        experimental_context_fingerprint=report.experimental_context_fingerprint,
        metrics=report.mean_metrics,
        disposition=report.disposition.value,
        source_manifest_ids=source_manifest_ids,
        source_code_revision=source_code_revision,
        numeric_policy=report.numeric_policy,
        issuer_token=scenario_core._MODEL_SNAPSHOT_ISSUER_TOKEN,
    )
