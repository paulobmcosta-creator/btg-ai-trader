"""Deterministic statistical baseline catalog and candidate interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections import Counter
from collections.abc import Mapping, Sequence
from datetime import datetime
from decimal import Decimal
from typing import Any, Protocol, runtime_checkable

from btg_ai_trader.statistical_baselines.domain import (
    CandidateIdentity,
    PredictionInput,
    PredictionResult,
    StatisticalSample,
    TargetSemantics,
    _validate_timezone_aware,
)


@runtime_checkable
class StatisticalBaseline(Protocol):
    """Protocol for deterministic statistical baseline models."""

    @property
    def identity(self) -> CandidateIdentity:
        """Identity of this candidate baseline."""
        ...

    @property
    def is_fitted(self) -> bool:
        """Whether the baseline has been fitted."""
        ...

    @property
    def supported_semantics(self) -> frozenset[TargetSemantics]:
        """Set of target semantics supported by this baseline."""
        ...

    def fit(self, samples: Sequence[StatisticalSample], knowledge_cutoff: datetime) -> None:
        """Fit the baseline model up to knowledge_cutoff using causally admissible samples."""
        ...

    def predict(self, sample: StatisticalSample | PredictionInput) -> PredictionResult:
        """Generate deterministic prediction for the given sample."""
        ...


class BaseStatisticalBaseline(ABC):
    """Base class for statistical baselines providing causal and semantic validation."""

    def __init__(
        self,
        baseline_type: str,
        parameters: Mapping[str, Any] | None = None,
        target_semantics: TargetSemantics = TargetSemantics.CONTINUOUS,
        code_revision: str = "v1.0.0",
    ) -> None:
        if not code_revision or not isinstance(code_revision, str):
            raise ValueError("code_revision must be a non-empty string explicitly provided")
        self._code_revision = code_revision
        self._identity = CandidateIdentity(
            baseline_type=baseline_type,
            parameters=parameters or {},
            target_semantics=target_semantics,
            code_revision=code_revision,
        )
        self._is_fitted: bool = False
        self._is_cold_start: bool = False
        self._knowledge_cutoff: datetime | None = None

    @property
    def identity(self) -> CandidateIdentity:
        return self._identity

    @property
    def is_fitted(self) -> bool:
        return self._is_fitted

    @property
    def supported_semantics(self) -> frozenset[TargetSemantics]:
        """Supported target semantics."""
        return frozenset([self._identity.target_semantics])

    def fit(
        self,
        samples: Sequence[StatisticalSample],
        knowledge_cutoff: datetime,
    ) -> None:
        """Fit baseline on causal samples available up to knowledge_cutoff."""
        _validate_timezone_aware(knowledge_cutoff, "knowledge_cutoff")
        for s in samples:
            if not s.is_causally_admissible_for_fit(knowledge_cutoff):
                raise ValueError(
                    f"Sample {s.sample_id} is not causally admissible at cutoff "
                    f"{knowledge_cutoff}: target_knowledge_time={s.target_knowledge_time}"
                )
            if s.target_semantics not in self.supported_semantics:
                raise ValueError(
                    f"Sample {s.sample_id} semantics {s.target_semantics} not supported by "
                    f"{self.identity.baseline_type}; supported: {self.supported_semantics}"
                )
        self._knowledge_cutoff = knowledge_cutoff

        if not samples:
            self._is_cold_start = True
            self._fit_empty()
        else:
            self._is_cold_start = False
            self._fit_samples(samples)

        self._is_fitted = True

    @abstractmethod
    def _fit_empty(self) -> None:
        """Initialize state for cold start when no training samples are available."""
        ...

    @abstractmethod
    def _fit_samples(self, samples: Sequence[StatisticalSample]) -> None:
        """Fit baseline parameters from admissible training samples."""
        ...

    def predict(self, sample: StatisticalSample | PredictionInput) -> PredictionResult:
        """Generate prediction for sample, checking state and semantics."""
        if not self._is_fitted:
            raise RuntimeError(
                f"Baseline {self.identity.baseline_type} must be fitted before predict"
            )
        pred_input = (
            sample if isinstance(sample, PredictionInput) else sample.to_prediction_input()
        )
        if pred_input.target_semantics not in self.supported_semantics:
            raise ValueError(
                f"Sample {pred_input.sample_id} semantics {pred_input.target_semantics} "
                f"not supported by {self.identity.baseline_type}"
            )

        assert self._knowledge_cutoff is not None
        return self._predict_sample(pred_input)

    @abstractmethod
    def _predict_sample(self, sample: PredictionInput) -> PredictionResult:
        """Generate candidate prediction from PredictionInput."""
        ...


class ConstantBaseline(BaseStatisticalBaseline):
    """Deterministic constant baseline returning a fixed value, probability, or class."""

    def __init__(
        self,
        constant_value: Decimal | None = None,
        constant_probability: Decimal | None = None,
        constant_class: str | None = None,
        semantics: TargetSemantics = TargetSemantics.CONTINUOUS,
        code_revision: str = "v1.0.0",
    ) -> None:
        if semantics is TargetSemantics.CONTINUOUS:
            if constant_value is None:
                raise ValueError("constant_value is required for CONTINUOUS semantics")
            if not isinstance(constant_value, Decimal):
                raise TypeError(
                    f"constant_value must be Decimal, got {type(constant_value).__name__}"
                )
            if constant_probability is not None or constant_class is not None:
                raise ValueError(
                    "Conflicting config: constant_probability and constant_class "
                    "must be None for CONTINUOUS"
                )
        elif semantics is TargetSemantics.BINARY_PROBABILITY:
            if constant_probability is None:
                raise ValueError(
                    "constant_probability is required for BINARY_PROBABILITY semantics"
                )
            if not isinstance(constant_probability, Decimal):
                raise TypeError(
                    f"constant_probability must be Decimal, "
                    f"got {type(constant_probability).__name__}"
                )
            if not (Decimal(0) <= constant_probability <= Decimal(1)):
                raise ValueError(
                    f"constant_probability must be in [0, 1], got {constant_probability}"
                )
            if constant_value is not None or constant_class is not None:
                raise ValueError(
                    "Conflicting config: constant_value and constant_class "
                    "must be None for BINARY_PROBABILITY"
                )
        elif semantics is TargetSemantics.CATEGORICAL:
            if constant_class is None:
                raise ValueError("constant_class is required for CATEGORICAL semantics")
            if not isinstance(constant_class, str):
                raise TypeError(f"constant_class must be str, got {type(constant_class).__name__}")
            if constant_value is not None:
                raise ValueError(
                    "Conflicting config: constant_value must be None for CATEGORICAL"
                )
            if constant_probability is not None:
                if not isinstance(constant_probability, Decimal):
                    raise TypeError(
                        f"constant_probability must be Decimal, "
                        f"got {type(constant_probability).__name__}"
                    )
                if not (Decimal(0) <= constant_probability <= Decimal(1)):
                    raise ValueError(
                        f"constant_probability must be in [0, 1], got {constant_probability}"
                    )
        else:
            raise ValueError(f"Unsupported target semantics: {semantics}")

        params: dict[str, Any] = {}
        if constant_value is not None:
            params["constant_value"] = str(constant_value)
        if constant_probability is not None:
            params["constant_probability"] = str(constant_probability)
        if constant_class is not None:
            params["constant_class"] = constant_class

        super().__init__(
            baseline_type="ConstantBaseline",
            parameters=params,
            target_semantics=semantics,
            code_revision=code_revision,
        )
        self._constant_value = constant_value
        self._constant_probability = constant_probability
        self._constant_class = constant_class

    def _fit_empty(self) -> None:
        pass

    def _fit_samples(self, samples: Sequence[StatisticalSample]) -> None:
        pass

    def _predict_sample(self, sample: PredictionInput) -> PredictionResult:
        assert self._knowledge_cutoff is not None
        return PredictionResult(
            sample_id=sample.sample_id,
            prediction_time=sample.feature_knowledge_time,
            predicted_value=self._constant_value,
            predicted_probability=self._constant_probability,
            predicted_class=self._constant_class,
            is_cold_start=self._is_cold_start,
            metadata={"cutoff": self._knowledge_cutoff.isoformat()},
        )


class PersistenceBaseline(BaseStatisticalBaseline):
    """Persistence baseline predicting the last observed continuous target value."""

    def __init__(
        self,
        code_revision: str = "v1.0.0",
    ) -> None:
        super().__init__(
            baseline_type="PersistenceBaseline",
            parameters={},
            target_semantics=TargetSemantics.CONTINUOUS,
            code_revision=code_revision,
        )
        self._last_value: Decimal | None = None

    def _fit_empty(self) -> None:
        self._last_value = None

    def _fit_samples(self, samples: Sequence[StatisticalSample]) -> None:
        last_sample = max(samples, key=lambda s: (s.target_knowledge_time, s.sample_id))
        assert isinstance(last_sample.target_value, Decimal)
        self._last_value = last_sample.target_value

    def _predict_sample(self, sample: PredictionInput) -> PredictionResult:
        assert self._knowledge_cutoff is not None
        return PredictionResult(
            sample_id=sample.sample_id,
            prediction_time=sample.feature_knowledge_time,
            predicted_value=self._last_value,
            predicted_probability=None,
            predicted_class=None,
            is_cold_start=self._is_cold_start,
            metadata={"cutoff": self._knowledge_cutoff.isoformat()},
        )


class HistoricalMeanBaseline(BaseStatisticalBaseline):
    """Historical mean baseline predicting the empirical arithmetic mean of continuous targets."""

    def __init__(
        self,
        code_revision: str = "v1.0.0",
    ) -> None:
        super().__init__(
            baseline_type="HistoricalMeanBaseline",
            parameters={},
            target_semantics=TargetSemantics.CONTINUOUS,
            code_revision=code_revision,
        )
        self._mean_value: Decimal | None = None

    def _fit_empty(self) -> None:
        self._mean_value = None

    def _fit_samples(self, samples: Sequence[StatisticalSample]) -> None:
        total = sum(
            s.target_value for s in samples if isinstance(s.target_value, Decimal)
        )
        self._mean_value = total / Decimal(len(samples))

    def _predict_sample(self, sample: PredictionInput) -> PredictionResult:
        assert self._knowledge_cutoff is not None
        return PredictionResult(
            sample_id=sample.sample_id,
            prediction_time=sample.feature_knowledge_time,
            predicted_value=self._mean_value,
            predicted_probability=None,
            predicted_class=None,
            is_cold_start=self._is_cold_start,
            metadata={"cutoff": self._knowledge_cutoff.isoformat()},
        )


class HistoricalMedianBaseline(BaseStatisticalBaseline):
    """Historical median baseline predicting empirical median of continuous targets."""

    def __init__(
        self,
        code_revision: str = "v1.0.0",
    ) -> None:
        super().__init__(
            baseline_type="HistoricalMedianBaseline",
            parameters={},
            target_semantics=TargetSemantics.CONTINUOUS,
            code_revision=code_revision,
        )
        self._median_value: Decimal | None = None

    def _fit_empty(self) -> None:
        self._median_value = None

    def _fit_samples(self, samples: Sequence[StatisticalSample]) -> None:
        sorted_vals = sorted(
            s.target_value for s in samples if isinstance(s.target_value, Decimal)
        )
        n = len(sorted_vals)
        if n % 2 == 1:
            self._median_value = sorted_vals[n // 2]
        else:
            mid = n // 2
            self._median_value = (sorted_vals[mid - 1] + sorted_vals[mid]) / Decimal(2)

    def _predict_sample(self, sample: PredictionInput) -> PredictionResult:
        assert self._knowledge_cutoff is not None
        return PredictionResult(
            sample_id=sample.sample_id,
            prediction_time=sample.feature_knowledge_time,
            predicted_value=self._median_value,
            predicted_probability=None,
            predicted_class=None,
            is_cold_start=self._is_cold_start,
            metadata={"cutoff": self._knowledge_cutoff.isoformat()},
        )


class HistoricalPriorProbabilityBaseline(BaseStatisticalBaseline):
    """Historical prior probability baseline predicting empirical base rate P(Y=1)."""

    def __init__(
        self,
        code_revision: str = "v1.0.0",
    ) -> None:
        super().__init__(
            baseline_type="HistoricalPriorProbabilityBaseline",
            parameters={},
            target_semantics=TargetSemantics.BINARY_PROBABILITY,
            code_revision=code_revision,
        )
        self._prior_probability: Decimal | None = None

    def _fit_empty(self) -> None:
        self._prior_probability = None

    def _fit_samples(self, samples: Sequence[StatisticalSample]) -> None:
        total_ones = sum(
            Decimal(1) for s in samples if s.target_value == Decimal(1)
        )
        self._prior_probability = total_ones / Decimal(len(samples))

    def _predict_sample(self, sample: PredictionInput) -> PredictionResult:
        assert self._knowledge_cutoff is not None
        predicted_val = None
        if self._prior_probability is not None:
            predicted_val = Decimal(1) if self._prior_probability >= Decimal("0.5") else Decimal(0)
        pred_cls = None
        if predicted_val == Decimal(1):
            pred_cls = "1"
        elif predicted_val == Decimal(0):
            pred_cls = "0"
        return PredictionResult(
            sample_id=sample.sample_id,
            prediction_time=sample.feature_knowledge_time,
            predicted_value=predicted_val,
            predicted_probability=self._prior_probability,
            predicted_class=pred_cls,
            is_cold_start=self._is_cold_start,
            metadata={"cutoff": self._knowledge_cutoff.isoformat()},
        )


class MajorityClassBaseline(BaseStatisticalBaseline):
    """Majority class baseline predicting empirical mode with lexical tie-breaking."""

    def __init__(
        self,
        target_semantics: TargetSemantics = TargetSemantics.CATEGORICAL,
        code_revision: str = "v1.0.0",
    ) -> None:
        if target_semantics is not TargetSemantics.CATEGORICAL:
            raise ValueError(
                f"MajorityClassBaseline only supports CATEGORICAL semantics to prevent "
                f"misinterpreting majority prevalence as P(Y=1). Got {target_semantics}."
            )
        super().__init__(
            baseline_type="MajorityClassBaseline",
            parameters={},
            target_semantics=TargetSemantics.CATEGORICAL,
            code_revision=code_revision,
        )
        self._majority_class: str | None = None
        self._prevalence: Decimal | None = None

    def _fit_empty(self) -> None:
        self._majority_class = None
        self._prevalence = None

    def _fit_samples(self, samples: Sequence[StatisticalSample]) -> None:
        counts = Counter(str(s.target_value) for s in samples)
        # Lexical order tie breaking: sort keys then max by count
        sorted_classes = sorted(counts.keys())
        winner = max(sorted_classes, key=lambda c: counts[c])
        self._majority_class = winner
        self._prevalence = Decimal(counts[winner]) / Decimal(len(samples))

    def _predict_sample(self, sample: PredictionInput) -> PredictionResult:
        assert self._knowledge_cutoff is not None
        return PredictionResult(
            sample_id=sample.sample_id,
            prediction_time=sample.feature_knowledge_time,
            predicted_value=None,
            predicted_probability=None,
            predicted_class=self._majority_class,
            is_cold_start=self._is_cold_start,
            metadata={"cutoff": self._knowledge_cutoff.isoformat()},
        )


class LastKnownClassBaseline(BaseStatisticalBaseline):
    """Last known class baseline predicting class of latest observed sample."""

    def __init__(
        self,
        target_semantics: TargetSemantics = TargetSemantics.CATEGORICAL,
        code_revision: str = "v1.0.0",
    ) -> None:
        super().__init__(
            baseline_type="LastKnownClassBaseline",
            parameters={},
            target_semantics=target_semantics,
            code_revision=code_revision,
        )
        self._last_class: str | None = None

    def _fit_empty(self) -> None:
        self._last_class = None

    def _fit_samples(self, samples: Sequence[StatisticalSample]) -> None:
        last_sample = max(samples, key=lambda s: (s.target_knowledge_time, s.sample_id))
        self._last_class = str(last_sample.target_value)

    def _predict_sample(self, sample: PredictionInput) -> PredictionResult:
        assert self._knowledge_cutoff is not None
        return PredictionResult(
            sample_id=sample.sample_id,
            prediction_time=sample.feature_knowledge_time,
            predicted_value=None,
            predicted_probability=None,
            predicted_class=self._last_class,
            is_cold_start=self._is_cold_start,
            metadata={"cutoff": self._knowledge_cutoff.isoformat()},
        )
