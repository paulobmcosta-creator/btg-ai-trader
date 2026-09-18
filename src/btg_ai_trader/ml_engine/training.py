"""Deterministic training orchestrator binding causal inputs, pipelines, and manifests."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime

import numpy as np

from btg_ai_trader.ml_engine.domain import (
    MLCandidateSpec,
    PredictiveCandidate,
)
from btg_ai_trader.ml_engine.features import (
    FeaturePipelineSpec,
    FittedFeaturePipeline,
)
from btg_ai_trader.ml_engine.models import create_candidate
from btg_ai_trader.ml_engine.provenance import (
    EnvironmentFingerprint,
    ModelTrainingInputBoundary,
    ModelTrainingManifest,
)
from btg_ai_trader.statistical_baselines.domain import (
    CausalLeakageError,
    StatisticalSample,
    TargetSemantics,
)


@dataclass(frozen=True, slots=True)
class TrainingResult:
    """Outcome of a successful model training run."""

    candidate: PredictiveCandidate
    fitted_pipeline: FittedFeaturePipeline
    input_boundary: ModelTrainingInputBoundary
    manifest: ModelTrainingManifest
    training_duration_seconds: float = 0.0

    @property
    def candidate_id(self) -> str:
        return self.candidate.spec.candidate_id

    @property
    def fitted_candidate(self) -> PredictiveCandidate:
        return self.candidate

    @property
    def boundary(self) -> ModelTrainingInputBoundary:
        return self.input_boundary

    @property
    def training_duration(self) -> float:
        return self.training_duration_seconds


class ModelTrainer:
    """Orchestrator for fitting feature pipelines and candidates under strict causality."""

    def __init__(self) -> None:
        pass

    def fit(
        self,
        candidate_spec: MLCandidateSpec,
        pipeline_spec: FeaturePipelineSpec,
        samples: Sequence[StatisticalSample],
        knowledge_cutoff: datetime,
        code_revision: str,
        audit_metadata: dict[str, str] | None = None,
    ) -> TrainingResult:
        """Fit candidate and pipeline, enforcing causal boundary and generating provenance."""
        if not samples:
            raise ValueError("Cannot train model on empty samples")

        # 1. Causal validation: target_knowledge_time <= knowledge_cutoff
        for s in samples:
            if s.target_knowledge_time > knowledge_cutoff:
                raise CausalLeakageError(
                    f"Sample '{s.sample_id}' target knowledge time {s.target_knowledge_time} "
                    f"is after training knowledge cutoff {knowledge_cutoff}. "
                    f"Future label leakage detected."
                )

        # 2. Target semantics validation
        expected_semantics = candidate_spec.target_contract.target_semantics
        for s in samples:
            if s.target_semantics != expected_semantics:
                raise ValueError(
                    f"Sample '{s.sample_id}' semantics {s.target_semantics} differs from "
                    f"target contract semantics {expected_semantics}"
                )

        # 3. Fit feature pipeline strictly on training samples
        fitted_pipeline = FittedFeaturePipeline.fit(pipeline_spec, samples)

        # 4. Transform training samples
        pred_inputs = [s.to_prediction_input() for s in samples]
        X_train = fitted_pipeline.transform(pred_inputs)

        if expected_semantics is TargetSemantics.BINARY_PROBABILITY:
            y_train = np.array([int(s.target_value) for s in samples], dtype=np.int64)
        else:
            y_train = np.array([float(s.target_value) for s in samples], dtype=np.float64)

        # 5. Capture environment and verified input boundary
        env = EnvironmentFingerprint.current()
        boundary = ModelTrainingInputBoundary.create_and_verify(
            samples=samples,
            target_contract=candidate_spec.target_contract,
            feature_schema_digest=pipeline_spec.schema.schema_digest,
            candidate_spec=candidate_spec,
            knowledge_cutoff=knowledge_cutoff,
            environment=env,
            code_revision=code_revision,
        )

        # 6. Fit candidate model
        candidate = create_candidate(candidate_spec)
        candidate.fit(X_train, y_train)

        # 7. Generate ModelTrainingManifest
        manifest = ModelTrainingManifest(
            boundary_digest=boundary.boundary_digest,
            candidate_id=candidate_spec.candidate_id,
            fitted_feature_pipeline_digest=fitted_pipeline.pipeline_digest,
            model_state_digest=candidate.model_state_digest,
            target_contract_digest=candidate_spec.target_contract.contract_digest,
            rng_context=candidate_spec.rng_context,
            numeric_policy=candidate_spec.numeric_policy,
            environment_fingerprint=env,
            code_revision=code_revision,
            audit_metadata=audit_metadata or {},
        )

        return TrainingResult(
            candidate=candidate,
            fitted_pipeline=fitted_pipeline,
            input_boundary=boundary,
            manifest=manifest,
        )
