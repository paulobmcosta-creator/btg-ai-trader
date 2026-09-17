"""Deterministic statistical baseline and temporal validation kernel."""

from btg_ai_trader.statistical_baselines.baselines import (
    BaseStatisticalBaseline,
    ConstantBaseline,
    HistoricalMeanBaseline,
    HistoricalMedianBaseline,
    HistoricalPriorProbabilityBaseline,
    LastKnownClassBaseline,
    MajorityClassBaseline,
    PersistenceBaseline,
    StatisticalBaseline,
)
from btg_ai_trader.statistical_baselines.boundaries import (
    EvaluationBoundary,
    TemporalFold,
    WalkForwardPlan,
)
from btg_ai_trader.statistical_baselines.calibration import (
    CalibrationBin,
    CalibrationReport,
    compute_calibration,
)
from btg_ai_trader.statistical_baselines.domain import (
    CandidateIdentity,
    EvaluationRole,
    PredictionResult,
    StatisticalSample,
    TargetSemantics,
)
from btg_ai_trader.statistical_baselines.evaluation import (
    AggregateEvaluationResult,
    FoldEvaluationResult,
    StatisticalEvaluationEngine,
)
from btg_ai_trader.statistical_baselines.metrics import (
    accuracy_score,
    base_rate,
    brier_score,
    class_prevalence,
    confusion_matrix_counts,
    mean_absolute_error,
    mean_bias,
    mean_squared_error,
    root_mean_squared_error,
)
from btg_ai_trader.statistical_baselines.splits import (
    EmbargoPolicy,
    PurgePolicy,
    SplitPlanConfig,
    WalkForwardPlanner,
    WindowPolicy,
)

__all__ = [
    "AggregateEvaluationResult",
    "BaseStatisticalBaseline",
    "CalibrationBin",
    "CalibrationReport",
    "CandidateIdentity",
    "ConstantBaseline",
    "EmbargoPolicy",
    "EvaluationBoundary",
    "EvaluationRole",
    "FoldEvaluationResult",
    "HistoricalMeanBaseline",
    "HistoricalMedianBaseline",
    "HistoricalPriorProbabilityBaseline",
    "LastKnownClassBaseline",
    "MajorityClassBaseline",
    "PersistenceBaseline",
    "PredictionResult",
    "PurgePolicy",
    "SplitPlanConfig",
    "StatisticalBaseline",
    "StatisticalEvaluationEngine",
    "StatisticalSample",
    "TargetSemantics",
    "TemporalFold",
    "WalkForwardPlan",
    "WalkForwardPlanner",
    "WindowPolicy",
    "accuracy_score",
    "base_rate",
    "brier_score",
    "class_prevalence",
    "compute_calibration",
    "confusion_matrix_counts",
    "mean_absolute_error",
    "mean_bias",
    "mean_squared_error",
    "root_mean_squared_error",
]
