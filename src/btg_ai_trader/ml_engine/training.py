"""Causal training coordinator binding actual inputs to verified provenance."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime

import numpy as np

from btg_ai_trader.ml_engine.domain import MLCandidateSpec, PredictiveCandidate
from btg_ai_trader.ml_engine.features import FeaturePipelineSpec, FittedFeaturePipeline
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
    """Verified output of a successful research-model fit."""

    candidate: PredictiveCandidate
    fitted_pipeline: FittedFeaturePipeline
    input_boundary: ModelTrainingInputBoundary
    manifest: ModelTrainingManifest

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
        """No wall-clock timing participates in Sprint 5 scientific identity."""

        return 0.0


class ModelTrainer:
    """Fit feature pipeline and estimator under one verified causal identity."""

    def fit(
        self,
        *,
        candidate_spec: MLCandidateSpec,
        pipeline_spec: FeaturePipelineSpec,
        samples: Sequence[StatisticalSample],
        knowledge_cutoff: datetime,
        code_revision: str,
        audit_metadata: Mapping[str, str] | None = None,
    ) -> TrainingResult:
        if not samples:
            raise ValueError("Cannot train model on empty samples")
        if candidate_spec.feature_pipeline_spec_digest != pipeline_spec.spec_digest:
            raise ValueError(
                "candidate feature_pipeline_spec_digest does not match pipeline_spec"
            )
        if candidate_spec.code_revision != code_revision:
            raise ValueError(
                "candidate code_revision does not match training code_revision"
            )

        semantics = candidate_spec.target_contract.target_semantics
        for sample in samples:
            if sample.target_knowledge_time > knowledge_cutoff:
                raise CausalLeakageError(
                    f"Sample '{sample.sample_id}' target knowledge time "
                    f"{sample.target_knowledge_time} is after training knowledge cutoff "
                    f"{knowledge_cutoff}. Future label leakage detected."
                )
            if sample.target_semantics is not semantics:
                raise ValueError(
                    f"Sample '{sample.sample_id}' target semantics do not match TargetContract"
                )

        fitted_pipeline = FittedFeaturePipeline.fit(pipeline_spec, samples)
        X_train = fitted_pipeline.transform(
            [sample.to_prediction_input() for sample in samples]
        )
        if semantics is TargetSemantics.BINARY_PROBABILITY:
            y_train = np.asarray(
                [int(sample.target_value) for sample in samples], dtype=np.int64
            )
        else:
            y_train = np.asarray(
                [float(sample.target_value) for sample in samples], dtype=np.float64
            )

        environment = EnvironmentFingerprint.current()
        boundary = ModelTrainingInputBoundary.create_and_verify(
            samples=samples,
            target_contract=candidate_spec.target_contract,
            feature_pipeline_spec_digest=pipeline_spec.spec_digest,
            candidate_spec=candidate_spec,
            knowledge_cutoff=knowledge_cutoff,
            environment=environment,
            code_revision=code_revision,
        )

        candidate = create_candidate(candidate_spec)
        candidate.fit(X_train, y_train)

        manifest = ModelTrainingManifest.create(
            boundary=boundary,
            candidate_spec=candidate_spec,
            fitted_feature_pipeline_digest=fitted_pipeline.pipeline_digest,
            model_state_digest=candidate.model_state_digest,
            environment_fingerprint=environment,
            code_revision=code_revision,
            audit_metadata=audit_metadata,
        )

        return TrainingResult(
            candidate=candidate,
            fitted_pipeline=fitted_pipeline,
            input_boundary=boundary,
            manifest=manifest,
        )
