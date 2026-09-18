"""Sprint 5 ML Engine — Research Machine Learning and Predictive Candidate Evaluation."""

from __future__ import annotations

from btg_ai_trader.ml_engine.domain import (
    EvaluationScope,
    FeatureType,
    InvalidCandidateError,
    MetricDirection,
    MissingnessPolicy,
    MLCandidateSpec,
    ModelEvaluationDisposition,
    PredictiveCandidate,
    RNGContext,
    TargetContract,
    TrainingFailureError,
)
from btg_ai_trader.ml_engine.evaluation import (
    AblationResult,
    BaselineComparisonResult,
    FeatureAblationSpec,
    FoldModelEvaluation,
    ModelEvaluationEngine,
    ModelEvaluationReport,
)
from btg_ai_trader.ml_engine.features import (
    FeaturePipelineSpec,
    FeatureSchema,
    FeatureSpec,
    FittedFeaturePipeline,
)
from btg_ai_trader.ml_engine.metrics import (
    BinaryMetricsReport,
    CalibrationBinResult,
    CalibrationDiagnostics,
    ContinuousMetricsReport,
    compute_brier_score,
    compute_calibration_diagnostics,
    compute_continuous_metrics,
    compute_log_loss,
    compute_roc_auc,
)
from btg_ai_trader.ml_engine.model_card import ModelCard
from btg_ai_trader.ml_engine.models import (
    GradientBoostingClassifierCandidate,
    GradientBoostingRegressorCandidate,
    LogisticRegressionCandidate,
    RandomForestClassifierCandidate,
    RandomForestRegressorCandidate,
    RidgeRegressionCandidate,
    create_candidate,
    extract_model_state_digest,
)
from btg_ai_trader.ml_engine.provenance import (
    EnvironmentFingerprint,
    ModelTrainingInputBoundary,
    ModelTrainingManifest,
)
from btg_ai_trader.ml_engine.registry import (
    ModelRecord,
    ResearchModelRegistry,
)
from btg_ai_trader.ml_engine.selection import (
    ModelComplexityDescriptor,
    ModelSearchHistory,
    ModelSearchSpace,
    ModelSelectionPolicy,
    SearchAttemptRecord,
)
from btg_ai_trader.ml_engine.training import (
    ModelTrainer,
    TrainingResult,
)

__all__ = [
    "AblationResult",
    "BaselineComparisonResult",
    "BinaryMetricsReport",
    "CalibrationBinResult",
    "CalibrationDiagnostics",
    "ContinuousMetricsReport",
    "EnvironmentFingerprint",
    "EvaluationScope",
    "FeatureAblationSpec",
    "FeaturePipelineSpec",
    "FeatureSchema",
    "FeatureSpec",
    "FeatureType",
    "FittedFeaturePipeline",
    "FoldModelEvaluation",
    "GradientBoostingClassifierCandidate",
    "GradientBoostingRegressorCandidate",
    "InvalidCandidateError",
    "LogisticRegressionCandidate",
    "MLCandidateSpec",
    "MetricDirection",
    "MissingnessPolicy",
    "ModelCard",
    "ModelComplexityDescriptor",
    "ModelEvaluationDisposition",
    "ModelEvaluationEngine",
    "ModelEvaluationReport",
    "ModelRecord",
    "ModelSearchHistory",
    "ModelSearchSpace",
    "ModelSelectionPolicy",
    "ModelTrainer",
    "ModelTrainingInputBoundary",
    "ModelTrainingManifest",
    "PredictiveCandidate",
    "RNGContext",
    "RandomForestClassifierCandidate",
    "RandomForestRegressorCandidate",
    "ResearchModelRegistry",
    "RidgeRegressionCandidate",
    "SearchAttemptRecord",
    "TargetContract",
    "TrainingFailureError",
    "TrainingResult",
    "UnknownCategoryPolicy",
    "compute_brier_score",
    "compute_calibration_diagnostics",
    "compute_continuous_metrics",
    "compute_log_loss",
    "compute_roc_auc",
    "create_candidate",
    "extract_model_state_digest",
]
