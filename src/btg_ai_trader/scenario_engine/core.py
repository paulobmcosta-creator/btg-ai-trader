"""Deterministic research-only Scenario Engine core (Sprint 6)."""

from __future__ import annotations

import hashlib
import json
import types
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from decimal import ROUND_CEILING, Decimal, localcontext
from enum import Enum

from btg_ai_trader.backtesting import BacktestRunManifest, compute_replay_boundary_fingerprint
from btg_ai_trader.statistical_baselines.comparison import (
    EvaluationHistory,
    ProtectedEvidenceUse,
)
from btg_ai_trader.statistical_baselines.domain import (
    EvaluationRole,
    ParityViolationError,
    ProtectedEvidenceReuseError,
)
from btg_ai_trader.statistical_baselines.evaluation import AggregateEvaluationResult
from btg_ai_trader.statistical_baselines.metrics import DEFAULT_NUMERIC_POLICY, NumericPolicy
from btg_ai_trader.statistical_baselines.provenance import StatisticalEvaluationInputBoundary

_VERIFIED_BOUNDARY_TOKEN = object()
_VERIFIED_MODEL_SNAPSHOT_TOKEN = object()
_MODEL_SNAPSHOT_ISSUER_TOKEN = object()


def _require_text(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")


def _require_aware(value: datetime, field_name: str) -> None:
    if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
        raise ValueError(f"{field_name} must be timezone-aware")


def _jsonable(value: object) -> object:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Mapping):
        return {str(k): _jsonable(v) for k, v in sorted(value.items(), key=lambda x: str(x[0]))}
    if isinstance(value, Sequence) and not isinstance(value, str | bytes):
        return [_jsonable(v) for v in value]
    return value


def _digest(payload: Mapping[str, object]) -> str:
    encoded = json.dumps(
        _jsonable(payload),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _freeze_decimal_mapping(mapping: Mapping[str, Decimal]) -> Mapping[str, Decimal]:
    return types.MappingProxyType({str(k): v for k, v in sorted(mapping.items())})


class SourceKind(str, Enum):
    BACKTEST = "BACKTEST"
    STATISTICAL_EVALUATION = "STATISTICAL_EVALUATION"
    MODEL_EVALUATION = "MODEL_EVALUATION"
    OBSERVED_SERIES = "OBSERVED_SERIES"


class RoleProvenance(str, Enum):
    INHERITED = "INHERITED"
    EXPERIMENT_ASSIGNED = "EXPERIMENT_ASSIGNED"


class RegimeDefinitionMode(str, Enum):
    PREDECLARED = "PREDECLARED"
    DEVELOPMENT_FIT = "DEVELOPMENT_FIT"
    RETROSPECTIVE_EXPLORATORY = "RETROSPECTIVE_EXPLORATORY"


class RegimeUseMode(str, Enum):
    CAUSAL_STRATIFICATION = "CAUSAL_STRATIFICATION"
    STRATEGY_BOUND = "STRATEGY_BOUND"
    RETROSPECTIVE_EXPLORATORY = "RETROSPECTIVE_EXPLORATORY"


class ComparisonOperator(str, Enum):
    LT = "LT"
    LE = "LE"
    GE = "GE"
    GT = "GT"


class ShockTarget(str, Enum):
    FEE_MULTIPLIER = "FEE_MULTIPLIER"
    SLIPPAGE_POINTS = "SLIPPAGE_POINTS"
    TRANSIT_LATENCY_US = "TRANSIT_LATENCY_US"
    MAX_SPREAD = "MAX_SPREAD"


class MetricDirection(str, Enum):
    MINIMIZE = "MINIMIZE"
    MAXIMIZE = "MAXIMIZE"


class ScenarioDisposition(str, Enum):
    FAVORABLE = "FAVORABLE"
    UNFAVORABLE = "UNFAVORABLE"
    CONDITIONAL = "CONDITIONAL"
    INCONCLUSIVE = "INCONCLUSIVE"
    INVALID = "INVALID"


class RobustnessCharacterization(str, Enum):
    ROBUST_WITHIN_DECLARED_SCOPE = "ROBUST_WITHIN_DECLARED_SCOPE"
    FRAGILE = "FRAGILE"
    MIXED = "MIXED"


class LossDirection(str, Enum):
    LOWER_IS_LOSS = "LOWER_IS_LOSS"
    HIGHER_IS_LOSS = "HIGHER_IS_LOSS"


class QuantileConvention(str, Enum):
    NEAREST_RANK = "NEAREST_RANK"


class ResearchArtifactKind(str, Enum):
    REGIME_DEFINITION = "REGIME_DEFINITION"
    SCENARIO_SPEC = "SCENARIO_SPEC"
    SCENARIO_GRID = "SCENARIO_GRID"
    DISPOSITION_POLICY = "DISPOSITION_POLICY"
    TAIL_POLICY = "TAIL_POLICY"


@dataclass(frozen=True, slots=True)
class ScenarioInputBoundary:
    source_kind: SourceKind
    source_artifact_id: str
    source_digest: str
    source_lineage_digest: str
    evaluation_role: EvaluationRole
    protected_boundary_id: str | None
    role_provenance: RoleProvenance
    numeric_policy_digest: str
    source_code_revision: str
    scenario_code_revision: str
    ordered_input_digest: str
    boundary_digest: str
    _verification_token: object = field(default=None, repr=False, compare=False)

    @property
    def is_verified(self) -> bool:
        return self._verification_token is _VERIFIED_BOUNDARY_TOKEN

    @classmethod
    def _build(
        cls,
        *,
        source_kind: SourceKind,
        source_artifact_id: str,
        source_digest: str,
        source_lineage_digest: str,
        evaluation_role: EvaluationRole,
        protected_boundary_id: str | None,
        role_provenance: RoleProvenance,
        numeric_policy_digest: str,
        source_code_revision: str,
        scenario_code_revision: str,
        ordered_input_digest: str,
    ) -> ScenarioInputBoundary:
        for value, name in (
            (source_artifact_id, "source_artifact_id"),
            (source_digest, "source_digest"),
            (source_lineage_digest, "source_lineage_digest"),
            (numeric_policy_digest, "numeric_policy_digest"),
            (source_code_revision, "source_code_revision"),
            (scenario_code_revision, "scenario_code_revision"),
            (ordered_input_digest, "ordered_input_digest"),
        ):
            _require_text(value, name)
        if evaluation_role is EvaluationRole.PROTECTED_TEST:
            if protected_boundary_id is None:
                raise ValueError("PROTECTED_TEST requires protected_boundary_id")
        elif protected_boundary_id is not None:
            raise ValueError("protected_boundary_id is only valid for PROTECTED_TEST")
        payload: dict[str, object] = {
            "source_kind": source_kind.value,
            "source_artifact_id": source_artifact_id,
            "source_digest": source_digest,
            "source_lineage_digest": source_lineage_digest,
            "evaluation_role": evaluation_role.value,
            "protected_boundary_id": protected_boundary_id,
            "role_provenance": role_provenance.value,
            "numeric_policy_digest": numeric_policy_digest,
            "source_code_revision": source_code_revision,
            "scenario_code_revision": scenario_code_revision,
            "ordered_input_digest": ordered_input_digest,
        }
        obj = cls(
            source_kind=source_kind,
            source_artifact_id=source_artifact_id,
            source_digest=source_digest,
            source_lineage_digest=source_lineage_digest,
            evaluation_role=evaluation_role,
            protected_boundary_id=protected_boundary_id,
            role_provenance=role_provenance,
            numeric_policy_digest=numeric_policy_digest,
            source_code_revision=source_code_revision,
            scenario_code_revision=scenario_code_revision,
            ordered_input_digest=ordered_input_digest,
            boundary_digest=_digest(payload),
        )
        object.__setattr__(obj, "_verification_token", _VERIFIED_BOUNDARY_TOKEN)
        return obj

    @classmethod
    def from_backtest_manifest(
        cls,
        manifest: BacktestRunManifest,
        *,
        evaluation_role: EvaluationRole,
        protected_boundary_id: str | None,
        numeric_policy: NumericPolicy,
        scenario_code_revision: str,
    ) -> ScenarioInputBoundary:
        if not manifest.verify_integrity():
            raise ValueError("BacktestRunManifest integrity verification failed")
        replay_fingerprint = compute_replay_boundary_fingerprint(
            manifest.input_boundary.replay_boundary
        ).value
        return cls._build(
            source_kind=SourceKind.BACKTEST,
            source_artifact_id=manifest.run_id.value,
            source_digest=manifest.manifest_hash.value,
            source_lineage_digest=replay_fingerprint,
            evaluation_role=evaluation_role,
            protected_boundary_id=protected_boundary_id,
            role_provenance=RoleProvenance.EXPERIMENT_ASSIGNED,
            numeric_policy_digest=_digest(numeric_policy.to_canonical_dict()),
            source_code_revision=manifest.input_boundary.code_revision.value,
            scenario_code_revision=scenario_code_revision,
            ordered_input_digest=manifest.input_boundary.actions_hash.value,
        )

    @classmethod
    def from_statistical_evaluation(
        cls,
        boundary: StatisticalEvaluationInputBoundary,
        result: AggregateEvaluationResult,
        *,
        protected_boundary_id: str | None,
        scenario_code_revision: str,
    ) -> ScenarioInputBoundary:
        if not boundary.is_verified:
            raise ValueError("StatisticalEvaluationInputBoundary must be verified")
        candidate_ids = {candidate.candidate_id for candidate in boundary.candidate_identities}
        fold_ids = tuple(fold.fold_id for fold in result.fold_results)
        boundary_fold_ids = tuple(str(fold["fold_id"]) for fold in boundary.fold_definitions)
        context_matches = (
            result.candidate_id in candidate_ids
            and result.target_contract_id == boundary.target_contract_id
            and result.code_revision == boundary.code_revision
            and result.numeric_policy == boundary.numeric_policy
            and fold_ids == boundary_fold_ids
            and all(
                fold.evaluation_role is result.evaluation_role
                for fold in result.fold_results
            )
        )
        if not context_matches:
            raise ValueError("statistical evaluation result does not match verified input boundary")
        records = result.protected_evidence_records
        if result.evaluation_role is EvaluationRole.PROTECTED_TEST:
            if len(records) != 1 or not isinstance(records[0], ProtectedEvidenceUse):
                raise ValueError(
                    "PROTECTED_TEST statistical evidence requires one canonical protected record"
                )
            record = records[0]
            if (
                record.candidate_id != result.candidate_id
                or record.evaluation_role is not EvaluationRole.PROTECTED_TEST
                or protected_boundary_id != record.protected_boundary_id
            ):
                raise ValueError(
                    "protected_boundary_id does not match statistical protected evidence record"
                )
        elif records:
            raise ValueError(
                "non-protected statistical evaluation cannot carry protected evidence records"
            )
        source_digest = _digest(
            {
                "logical_evaluation_digest": boundary.logical_evaluation_digest,
                "candidate_id": result.candidate_id,
                "evaluation_role": result.evaluation_role.value,
                "aggregate_metrics": result.aggregate_metrics,
                "evaluation_context_fingerprint": result.evaluation_context_fingerprint,
            }
        )
        return cls._build(
            source_kind=SourceKind.STATISTICAL_EVALUATION,
            source_artifact_id=result.candidate_id,
            source_digest=source_digest,
            source_lineage_digest=boundary.source_lineage_digest,
            evaluation_role=result.evaluation_role,
            protected_boundary_id=protected_boundary_id,
            role_provenance=RoleProvenance.INHERITED,
            numeric_policy_digest=_digest(boundary.numeric_policy.to_canonical_dict()),
            source_code_revision=boundary.code_revision,
            scenario_code_revision=scenario_code_revision,
            ordered_input_digest=_digest(
                {"sample_ids": boundary.sample_ids, "plan_digest": boundary.plan_digest}
            ),
        )

    @classmethod
    def from_model_snapshot(
        cls,
        snapshot: ModelEvidenceSnapshot,
        *,
        scenario_code_revision: str,
    ) -> ScenarioInputBoundary:
        if not snapshot.is_verified:
            raise ValueError("ModelEvidenceSnapshot must be verified")
        return cls._build(
            source_kind=SourceKind.MODEL_EVALUATION,
            source_artifact_id=snapshot.candidate_id,
            source_digest=snapshot.snapshot_digest,
            source_lineage_digest=snapshot.experimental_context_fingerprint,
            evaluation_role=snapshot.evaluation_role,
            protected_boundary_id=snapshot.protected_boundary_id,
            role_provenance=RoleProvenance.INHERITED,
            numeric_policy_digest=snapshot.numeric_policy_digest,
            source_code_revision=snapshot.source_code_revision,
            scenario_code_revision=scenario_code_revision,
            ordered_input_digest=_digest(
                {
                    "dataset_digest": snapshot.dataset_digest,
                    "plan_digest": snapshot.plan_digest,
                }
            ),
        )

    @classmethod
    def from_observed_series(
        cls,
        series: ObservedSeries,
        *,
        evaluation_role: EvaluationRole,
        protected_boundary_id: str | None,
        numeric_policy: NumericPolicy,
        source_code_revision: str,
        scenario_code_revision: str,
    ) -> ScenarioInputBoundary:
        return cls._build(
            source_kind=SourceKind.OBSERVED_SERIES,
            source_artifact_id=series.series_id,
            source_digest=series.series_digest,
            source_lineage_digest=series.source_digest,
            evaluation_role=evaluation_role,
            protected_boundary_id=protected_boundary_id,
            role_provenance=RoleProvenance.EXPERIMENT_ASSIGNED,
            numeric_policy_digest=_digest(numeric_policy.to_canonical_dict()),
            source_code_revision=source_code_revision,
            scenario_code_revision=scenario_code_revision,
            ordered_input_digest=_digest(
                {
                    "observation_ids": series.observation_ids,
                    "timestamps": series.timestamps,
                }
            ),
        )


def verify_experimental_parity(
    boundaries: Sequence[ScenarioInputBoundary],
) -> str:
    if not boundaries:
        raise ValueError("boundaries cannot be empty")
    first = boundaries[0]
    if not first.is_verified:
        raise ValueError("experimental parity requires verified ScenarioInputBoundary values")
    parity_fields = (
        first.source_kind,
        first.source_digest,
        first.source_lineage_digest,
        first.evaluation_role,
        first.protected_boundary_id,
        first.role_provenance,
        first.numeric_policy_digest,
        first.source_code_revision,
        first.scenario_code_revision,
        first.ordered_input_digest,
    )
    for boundary in boundaries[1:]:
        if not boundary.is_verified:
            raise ValueError("experimental parity requires verified ScenarioInputBoundary values")
        current = (
            boundary.source_kind,
            boundary.source_digest,
            boundary.source_lineage_digest,
            boundary.evaluation_role,
            boundary.protected_boundary_id,
            boundary.role_provenance,
            boundary.numeric_policy_digest,
            boundary.source_code_revision,
            boundary.scenario_code_revision,
            boundary.ordered_input_digest,
        )
        if current != parity_fields:
            raise ParityViolationError("Scenario Engine experimental context parity violation")
    return _digest(
        {
            "source_kind": first.source_kind.value,
            "source_digest": first.source_digest,
            "source_lineage_digest": first.source_lineage_digest,
            "evaluation_role": first.evaluation_role.value,
            "protected_boundary_id": first.protected_boundary_id,
            "role_provenance": first.role_provenance.value,
            "numeric_policy_digest": first.numeric_policy_digest,
            "source_code_revision": first.source_code_revision,
            "scenario_code_revision": first.scenario_code_revision,
            "ordered_input_digest": first.ordered_input_digest,
        }
    )


@dataclass(frozen=True, slots=True)
class ModelEvidenceSnapshot:
    candidate_id: str
    evaluation_scope: str
    evaluation_role: EvaluationRole
    protected_boundary_id: str | None
    dataset_digest: str
    plan_digest: str
    target_contract_digest: str
    experimental_context_fingerprint: str
    metrics: Mapping[str, Decimal]
    disposition: str
    source_manifest_ids: tuple[str, ...]
    source_code_revision: str
    numeric_policy_digest: str
    snapshot_digest: str
    _verification_token: object = field(default=None, repr=False, compare=False)

    @property
    def is_verified(self) -> bool:
        return self._verification_token is _VERIFIED_MODEL_SNAPSHOT_TOKEN


def _issue_model_evidence_snapshot(
    *,
    candidate_id: str,
    evaluation_scope: str,
    evaluation_role: EvaluationRole,
    protected_boundary_id: str | None,
    dataset_digest: str,
    plan_digest: str,
    target_contract_digest: str,
    experimental_context_fingerprint: str,
    metrics: Mapping[str, Decimal],
    disposition: str,
    source_manifest_ids: Sequence[str],
    source_code_revision: str,
    numeric_policy: NumericPolicy,
    issuer_token: object,
) -> ModelEvidenceSnapshot:
    if issuer_token is not _MODEL_SNAPSHOT_ISSUER_TOKEN:
        raise PermissionError("ModelEvidenceSnapshot may only be issued by the verified S5 adapter")
    for value, name in (
        (candidate_id, "candidate_id"),
        (evaluation_scope, "evaluation_scope"),
        (dataset_digest, "dataset_digest"),
        (plan_digest, "plan_digest"),
        (target_contract_digest, "target_contract_digest"),
        (experimental_context_fingerprint, "experimental_context_fingerprint"),
        (disposition, "disposition"),
        (source_code_revision, "source_code_revision"),
    ):
        _require_text(value, name)
    if evaluation_scope != "MODEL":
        raise ValueError("model evidence snapshot requires MODEL evaluation scope")
    if evaluation_role is EvaluationRole.PROTECTED_TEST:
        if protected_boundary_id is None:
            raise ValueError("PROTECTED_TEST model evidence requires protected_boundary_id")
    elif protected_boundary_id is not None:
        raise ValueError("non-protected model evidence cannot carry protected_boundary_id")
    manifest_ids = tuple(sorted(source_manifest_ids))
    if not manifest_ids or any(not item for item in manifest_ids):
        raise ValueError("source_manifest_ids must contain non-empty immutable identities")
    if len(set(manifest_ids)) != len(manifest_ids):
        raise ValueError("source_manifest_ids must be unique")
    frozen_metrics = _freeze_decimal_mapping(metrics)
    numeric_policy_digest = _digest(numeric_policy.to_canonical_dict())
    payload: dict[str, object] = {
        "candidate_id": candidate_id,
        "evaluation_scope": evaluation_scope,
        "evaluation_role": evaluation_role.value,
        "protected_boundary_id": protected_boundary_id,
        "dataset_digest": dataset_digest,
        "plan_digest": plan_digest,
        "target_contract_digest": target_contract_digest,
        "experimental_context_fingerprint": experimental_context_fingerprint,
        "metrics": frozen_metrics,
        "disposition": disposition,
        "source_manifest_ids": manifest_ids,
        "source_code_revision": source_code_revision,
        "numeric_policy_digest": numeric_policy_digest,
    }
    obj = ModelEvidenceSnapshot(
        candidate_id=candidate_id,
        evaluation_scope=evaluation_scope,
        evaluation_role=evaluation_role,
        protected_boundary_id=protected_boundary_id,
        dataset_digest=dataset_digest,
        plan_digest=plan_digest,
        target_contract_digest=target_contract_digest,
        experimental_context_fingerprint=experimental_context_fingerprint,
        metrics=frozen_metrics,
        disposition=disposition,
        source_manifest_ids=manifest_ids,
        source_code_revision=source_code_revision,
        numeric_policy_digest=numeric_policy_digest,
        snapshot_digest=_digest(payload),
    )
    object.__setattr__(obj, "_verification_token", _VERIFIED_MODEL_SNAPSHOT_TOKEN)
    return obj


@dataclass(frozen=True, slots=True)
class RegimeObservation:
    observation_id: str
    knowledge_time: datetime
    variables: Mapping[str, Decimal]
    source_lineage_digest: str
    event_time: datetime | None = None
    variable_units: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_text(self.observation_id, "observation_id")
        _require_aware(self.knowledge_time, "knowledge_time")
        _require_text(self.source_lineage_digest, "source_lineage_digest")
        if self.event_time is not None:
            _require_aware(self.event_time, "event_time")
            if self.event_time > self.knowledge_time:
                raise ValueError("event_time cannot be later than knowledge_time")
        frozen_variables = _freeze_decimal_mapping(self.variables)
        frozen_units = types.MappingProxyType(
            {str(key): str(value) for key, value in sorted(self.variable_units.items())}
        )
        if set(frozen_variables) != set(frozen_units):
            raise ValueError("variable_units must declare exactly one unit for every variable")
        for name, unit in frozen_units.items():
            _require_text(name, "variable_name")
            _require_text(unit, f"unit[{name}]")
        object.__setattr__(self, "variables", frozen_variables)
        object.__setattr__(self, "variable_units", frozen_units)


@dataclass(frozen=True, slots=True)
class ThresholdRule:
    variable_name: str
    operator: ComparisonOperator
    threshold: Decimal
    label: str
    unit: str = "unitless"

    def __post_init__(self) -> None:
        _require_text(self.variable_name, "variable_name")
        _require_text(self.label, "label")
        _require_text(self.unit, "unit")
        if not isinstance(self.threshold, Decimal):
            raise TypeError("threshold must be Decimal")


@dataclass(frozen=True, slots=True)
class RegimeDefinition:
    definition_id: str
    mode: RegimeDefinitionMode
    rules: tuple[ThresholdRule, ...]
    default_label: str
    source_lineage_digest: str
    development_boundary_id: str | None = None
    definition_digest: str = field(init=False)

    def __post_init__(self) -> None:
        _require_text(self.definition_id, "definition_id")
        _require_text(self.default_label, "default_label")
        _require_text(self.source_lineage_digest, "source_lineage_digest")
        if not self.rules:
            raise ValueError("rules cannot be empty")
        if self.mode is RegimeDefinitionMode.DEVELOPMENT_FIT:
            if self.development_boundary_id is None:
                raise ValueError("DEVELOPMENT_FIT requires development_boundary_id")
        elif self.development_boundary_id is not None:
            raise ValueError("development_boundary_id is only valid for DEVELOPMENT_FIT")
        payload: dict[str, object] = {
            "definition_id": self.definition_id,
            "mode": self.mode.value,
            "rules": tuple(
                (r.variable_name, r.operator.value, r.threshold, r.label, r.unit)
                for r in self.rules
            ),
            "default_label": self.default_label,
            "source_lineage_digest": self.source_lineage_digest,
            "development_boundary_id": self.development_boundary_id,
        }
        object.__setattr__(self, "definition_digest", _digest(payload))


@dataclass(frozen=True, slots=True)
class RegimeAssignment:
    observation_id: str
    definition_digest: str
    label: str
    use_mode: RegimeUseMode
    knowledge_time: datetime
    as_of_time: datetime


def _rule_matches(rule: ThresholdRule, value: Decimal) -> bool:
    if rule.operator is ComparisonOperator.LT:
        return value < rule.threshold
    if rule.operator is ComparisonOperator.LE:
        return value <= rule.threshold
    if rule.operator is ComparisonOperator.GE:
        return value >= rule.threshold
    return value > rule.threshold


def classify_regime(
    definition: RegimeDefinition,
    observation: RegimeObservation,
    *,
    use_mode: RegimeUseMode,
    as_of_time: datetime,
) -> RegimeAssignment:
    _require_aware(as_of_time, "as_of_time")
    if observation.source_lineage_digest != definition.source_lineage_digest:
        raise ValueError("regime observation source lineage does not match definition")
    if definition.mode is RegimeDefinitionMode.RETROSPECTIVE_EXPLORATORY:
        if use_mode is not RegimeUseMode.RETROSPECTIVE_EXPLORATORY:
            raise ValueError("retrospective regime definition is exploratory-only")
    if use_mode is RegimeUseMode.STRATEGY_BOUND:
        raise ValueError(
            "STRATEGY_BOUND is unavailable until verified upstream regime-use evidence exists"
        )
    if (
        use_mode is not RegimeUseMode.RETROSPECTIVE_EXPLORATORY
        and observation.knowledge_time > as_of_time
    ):
        raise ValueError("causal regime assignment cannot use information known after as_of_time")
    required_variables = {rule.variable_name for rule in definition.rules}
    if any(name not in observation.variables for name in required_variables):
        label = "UNKNOWN"
    else:
        for rule in definition.rules:
            if observation.variable_units[rule.variable_name] != rule.unit:
                raise ValueError(
                    f"regime variable unit mismatch for {rule.variable_name}: "
                    f"{observation.variable_units[rule.variable_name]} != {rule.unit}"
                )
        label = definition.default_label
        for rule in definition.rules:
            if _rule_matches(rule, observation.variables[rule.variable_name]):
                label = rule.label
                break
    return RegimeAssignment(
        observation_id=observation.observation_id,
        definition_digest=definition.definition_digest,
        label=label,
        use_mode=use_mode,
        knowledge_time=observation.knowledge_time,
        as_of_time=as_of_time,
    )


@dataclass(frozen=True, slots=True)
class RegimeMetricSummary:
    label: str
    count: int
    minimum: Decimal
    maximum: Decimal
    mean: Decimal
    definition_digest: str
    use_mode: RegimeUseMode


def summarize_metric_by_regime(
    assignments: Sequence[RegimeAssignment],
    values_by_observation_id: Mapping[str, Decimal],
) -> Mapping[str, RegimeMetricSummary]:
    if not assignments:
        raise ValueError("assignments cannot be empty")
    expected_ids = tuple(assignment.observation_id for assignment in assignments)
    if len(set(expected_ids)) != len(expected_ids):
        raise ValueError("regime assignments must have unique observation_id values")
    if set(values_by_observation_id) != set(expected_ids):
        raise ParityViolationError(
            "regime-conditioned values must exactly match assignment observation IDs"
        )
    definition_digest = assignments[0].definition_digest
    use_mode = assignments[0].use_mode
    if any(
        assignment.definition_digest != definition_digest or assignment.use_mode is not use_mode
        for assignment in assignments
    ):
        raise ParityViolationError(
            "regime-conditioned summaries cannot mix definition digests or use modes"
        )
    grouped: dict[str, list[Decimal]] = {}
    for assignment in assignments:
        grouped.setdefault(assignment.label, []).append(
            values_by_observation_id[assignment.observation_id]
        )
    result: dict[str, RegimeMetricSummary] = {}
    for label in sorted(grouped):
        values = grouped[label]
        result[label] = RegimeMetricSummary(
            label=label,
            count=len(values),
            minimum=min(values),
            maximum=max(values),
            mean=sum(values, Decimal(0)) / Decimal(len(values)),
            definition_digest=definition_digest,
            use_mode=use_mode,
        )
    return types.MappingProxyType(result)


def fit_development_threshold_definition(
    observations: Sequence[RegimeObservation],
    *,
    variable_name: str,
    label_below: str,
    label_at_or_above: str,
    definition_id: str,
    development_boundary_id: str,
    source_lineage_digest: str,
    evaluation_role: EvaluationRole,
    variable_unit: str = "unitless",
) -> RegimeDefinition:
    if evaluation_role is not EvaluationRole.DEVELOPMENT:
        raise ValueError("learned regime threshold may be fit only on DEVELOPMENT evidence")
    if not observations:
        raise ValueError("observations cannot be empty")
    if len({obs.observation_id for obs in observations}) != len(observations):
        raise ValueError("development observations must have unique observation IDs")
    if any(obs.source_lineage_digest != source_lineage_digest for obs in observations):
        raise ValueError("development observation lineage does not match declared source lineage")
    if any(variable_name not in obs.variables for obs in observations):
        raise ValueError("development observations cannot silently drop missing regime values")
    _require_text(variable_unit, "variable_unit")
    if any(obs.variable_units[variable_name] != variable_unit for obs in observations):
        raise ValueError("development observation units do not match variable_unit")
    values = sorted(obs.variables[variable_name] for obs in observations)
    midpoint = len(values) // 2
    if len(values) % 2:
        threshold = values[midpoint]
    else:
        threshold = (values[midpoint - 1] + values[midpoint]) / Decimal(2)
    return RegimeDefinition(
        definition_id=definition_id,
        mode=RegimeDefinitionMode.DEVELOPMENT_FIT,
        rules=(
            ThresholdRule(variable_name, ComparisonOperator.LT, threshold, label_below, variable_unit),
            ThresholdRule(variable_name, ComparisonOperator.GE, threshold, label_at_or_above, variable_unit),
        ),
        default_label="UNKNOWN",
        source_lineage_digest=source_lineage_digest,
        development_boundary_id=development_boundary_id,
    )


@dataclass(frozen=True, slots=True)
class ScenarioShock:
    target: ShockTarget
    value: Decimal
    unit: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, Decimal) or self.value < Decimal(0):
            raise ValueError("shock value must be a non-negative Decimal")
        if self.target is ShockTarget.FEE_MULTIPLIER and self.value < Decimal(1):
            raise ValueError("FEE_MULTIPLIER stress must be at least 1")
        if self.target is ShockTarget.MAX_SPREAD and self.value <= Decimal(0):
            raise ValueError("MAX_SPREAD stress must be positive")
        _require_text(self.unit, "unit")
        expected_units = {
            ShockTarget.FEE_MULTIPLIER: "multiplier",
            ShockTarget.SLIPPAGE_POINTS: "points",
            ShockTarget.TRANSIT_LATENCY_US: "microseconds",
            ShockTarget.MAX_SPREAD: "price",
        }
        if self.unit != expected_units[self.target]:
            raise ValueError(
                f"{self.target.value} requires unit {expected_units[self.target]!r}"
            )


@dataclass(frozen=True, slots=True)
class ScenarioSpec:
    scenario_id: str
    baseline_evidence_ref: str
    shocks: tuple[ScenarioShock, ...]
    structural_constraints: tuple[str, ...]
    predeclared: bool
    research_history_ref: str
    code_revision: str
    scenario_digest: str = field(init=False)

    def __post_init__(self) -> None:
        for value, name in (
            (self.scenario_id, "scenario_id"),
            (self.baseline_evidence_ref, "baseline_evidence_ref"),
            (self.research_history_ref, "research_history_ref"),
            (self.code_revision, "code_revision"),
        ):
            _require_text(value, name)
        if not self.shocks:
            raise ValueError("scenario must contain at least one shock")
        targets = tuple(shock.target for shock in self.shocks)
        if len(set(targets)) != len(targets):
            raise ValueError("scenario cannot contain duplicate shock targets")
        if len(self.shocks) > 1 and not self.structural_constraints:
            raise ValueError("multi-variable stress requires structural consistency constraints")
        payload: dict[str, object] = {
            "scenario_id": self.scenario_id,
            "baseline_evidence_ref": self.baseline_evidence_ref,
            "shocks": tuple((s.target.value, s.value, s.unit) for s in self.shocks),
            "structural_constraints": self.structural_constraints,
            "predeclared": self.predeclared,
            "research_history_ref": self.research_history_ref,
            "code_revision": self.code_revision,
        }
        object.__setattr__(self, "scenario_digest", _digest(payload))


@dataclass(frozen=True, slots=True)
class ScenarioGrid:
    grid_id: str
    scenarios: tuple[ScenarioSpec, ...]
    predeclared: bool
    grid_digest: str = field(init=False)

    def __post_init__(self) -> None:
        _require_text(self.grid_id, "grid_id")
        if not self.predeclared:
            raise ValueError("ScenarioGrid must be predeclared")
        if not self.scenarios:
            raise ValueError("ScenarioGrid cannot be empty")
        ids = tuple(s.scenario_id for s in self.scenarios)
        if ids != tuple(sorted(ids)):
            raise ValueError("ScenarioGrid must be canonically ordered by scenario_id")
        if len(set(ids)) != len(ids):
            raise ValueError("ScenarioGrid scenario IDs must be unique")
        if any(not scenario.predeclared for scenario in self.scenarios):
            raise ValueError("ScenarioGrid cannot contain non-predeclared scenarios")
        object.__setattr__(
            self,
            "grid_digest",
            _digest(
                {
                    "grid_id": self.grid_id,
                    "scenario_digests": tuple(s.scenario_digest for s in self.scenarios),
                    "predeclared": self.predeclared,
                }
            ),
        )


@dataclass(frozen=True, slots=True)
class ScenarioOutcome:
    scenario_id: str
    metrics: Mapping[str, Decimal]
    stressed_manifest_hash: str

    def __post_init__(self) -> None:
        _require_text(self.scenario_id, "scenario_id")
        _require_text(self.stressed_manifest_hash, "stressed_manifest_hash")
        object.__setattr__(self, "metrics", _freeze_decimal_mapping(self.metrics))


@dataclass(frozen=True, slots=True)
class ScenarioOutcomeSet:
    grid_digest: str
    outcomes: tuple[ScenarioOutcome, ...]
    outcome_set_digest: str = field(init=False)

    def __post_init__(self) -> None:
        _require_text(self.grid_digest, "grid_digest")
        if not self.outcomes:
            raise ValueError("ScenarioOutcomeSet cannot be empty")
        object.__setattr__(
            self,
            "outcome_set_digest",
            _digest(
                {
                    "grid_digest": self.grid_digest,
                    "outcomes": tuple(
                        (o.scenario_id, o.metrics, o.stressed_manifest_hash) for o in self.outcomes
                    ),
                }
            ),
        )


def build_scenario_outcome_set(
    grid: ScenarioGrid,
    outcomes: Sequence[ScenarioOutcome],
) -> ScenarioOutcomeSet:
    outcome_tuple = tuple(outcomes)
    expected = tuple(s.scenario_id for s in grid.scenarios)
    actual = tuple(o.scenario_id for o in outcome_tuple)
    if actual != expected:
        raise ValueError("scenario outcomes must exactly match canonical ScenarioGrid order")
    return ScenarioOutcomeSet(grid.grid_digest, outcome_tuple)


@dataclass(frozen=True, slots=True)
class ScenarioMetricRange:
    minimum: Decimal
    maximum: Decimal
    mean: Decimal
    scenario_count: int
    effective_count: int
    missing_count: int


def summarize_scenario_outcomes(
    outcome_set: ScenarioOutcomeSet,
) -> Mapping[str, ScenarioMetricRange]:
    metric_names = sorted({name for outcome in outcome_set.outcomes for name in outcome.metrics})
    summary: dict[str, ScenarioMetricRange] = {}
    for name in metric_names:
        values = [
            outcome.metrics[name]
            for outcome in outcome_set.outcomes
            if name in outcome.metrics
        ]
        summary[name] = ScenarioMetricRange(
            minimum=min(values),
            maximum=max(values),
            mean=sum(values, Decimal(0)) / Decimal(len(values)),
            scenario_count=len(outcome_set.outcomes),
            effective_count=len(values),
            missing_count=len(outcome_set.outcomes) - len(values),
        )
    return types.MappingProxyType(summary)


@dataclass(frozen=True, slots=True)
class ObservedSeries:
    series_id: str
    population: str
    observation_unit: str
    value_unit: str
    values: tuple[Decimal, ...]
    observation_ids: tuple[str, ...]
    source_digest: str
    missing_policy: str
    timestamps: tuple[datetime, ...] = ()
    series_digest: str = field(init=False)

    def __post_init__(self) -> None:
        for value, name in (
            (self.series_id, "series_id"),
            (self.population, "population"),
            (self.observation_unit, "observation_unit"),
            (self.value_unit, "value_unit"),
            (self.source_digest, "source_digest"),
            (self.missing_policy, "missing_policy"),
        ):
            _require_text(value, name)
        if not self.values:
            raise ValueError("ObservedSeries cannot be empty")
        if len(self.values) != len(self.observation_ids):
            raise ValueError("observation_ids must align one-to-one with values")
        if len(set(self.observation_ids)) != len(self.observation_ids):
            raise ValueError("observation_ids must be unique")
        if self.timestamps:
            if len(self.timestamps) != len(self.values):
                raise ValueError("timestamps must align one-to-one with values")
            for timestamp in self.timestamps:
                _require_aware(timestamp, "timestamp")
            if any(b < a for a, b in zip(self.timestamps, self.timestamps[1:], strict=False)):
                raise ValueError("timestamps must be monotonically non-decreasing")
        object.__setattr__(
            self,
            "series_digest",
            _digest(
                {
                    "series_id": self.series_id,
                    "population": self.population,
                    "observation_unit": self.observation_unit,
                    "value_unit": self.value_unit,
                    "values": self.values,
                    "observation_ids": self.observation_ids,
                    "source_digest": self.source_digest,
                    "missing_policy": self.missing_policy,
                    "timestamps": self.timestamps,
                }
            ),
        )


@dataclass(frozen=True, slots=True)
class ObservedDistributionSummary:
    count: int
    minimum: Decimal
    maximum: Decimal
    mean: Decimal
    median: Decimal
    empirical_probability_of_loss: Decimal
    loss_direction: LossDirection
    loss_threshold: Decimal


def summarize_observed_series(
    series: ObservedSeries,
    *,
    loss_direction: LossDirection,
    loss_threshold: Decimal = Decimal(0),
    numeric_policy: NumericPolicy = DEFAULT_NUMERIC_POLICY,
) -> ObservedDistributionSummary:
    with localcontext(numeric_policy.get_context()):
        ordered = sorted(series.values)
        n = len(ordered)
        midpoint = n // 2
        median = (
            ordered[midpoint]
            if n % 2
            else (ordered[midpoint - 1] + ordered[midpoint]) / Decimal(2)
        )
        if loss_direction is LossDirection.LOWER_IS_LOSS:
            loss_count = sum(1 for value in ordered if value < loss_threshold)
        else:
            loss_count = sum(1 for value in ordered if value > loss_threshold)
        return ObservedDistributionSummary(
            count=n,
            minimum=ordered[0],
            maximum=ordered[-1],
            mean=sum(ordered, Decimal(0)) / Decimal(n),
            median=median,
            empirical_probability_of_loss=Decimal(loss_count) / Decimal(n),
            loss_direction=loss_direction,
            loss_threshold=loss_threshold,
        )


@dataclass(frozen=True, slots=True)
class TailMetricPolicy:
    tail_fraction: Decimal
    loss_direction: LossDirection
    convention: QuantileConvention
    minimum_total_count: int
    minimum_tail_count: int
    missing_policy: str = "REJECT"
    numeric_policy: NumericPolicy = DEFAULT_NUMERIC_POLICY
    predeclared: bool = True
    policy_digest: str = field(init=False)

    def __post_init__(self) -> None:
        if not self.predeclared:
            raise ValueError("TailMetricPolicy must be predeclared")
        if not (Decimal(0) < self.tail_fraction <= Decimal("0.5")):
            raise ValueError("tail_fraction must be in (0, 0.5]")
        if self.minimum_total_count <= 0 or self.minimum_tail_count <= 0:
            raise ValueError("minimum sample counts must be positive")
        _require_text(self.missing_policy, "missing_policy")
        object.__setattr__(
            self,
            "policy_digest",
            _digest(
                {
                    "tail_fraction": self.tail_fraction,
                    "loss_direction": self.loss_direction.value,
                    "convention": self.convention.value,
                    "minimum_total_count": self.minimum_total_count,
                    "minimum_tail_count": self.minimum_tail_count,
                    "missing_policy": self.missing_policy,
                    "numeric_policy": self.numeric_policy.to_canonical_dict(),
                    "predeclared": self.predeclared,
                }
            ),
        )


@dataclass(frozen=True, slots=True)
class TailMetricResult:
    value_at_risk: Decimal | None
    expected_shortfall: Decimal | None
    total_count: int
    tail_count: int
    empirical_resolution: Decimal
    sufficient: bool
    policy_digest: str


def compute_tail_metrics(
    series: ObservedSeries,
    policy: TailMetricPolicy,
) -> TailMetricResult:
    if not isinstance(series, ObservedSeries):
        raise TypeError("tail metrics require ObservedSeries; ScenarioOutcomeSet is not empirical")
    if series.missing_policy != policy.missing_policy:
        raise ValueError("ObservedSeries missing_policy does not match TailMetricPolicy")
    with localcontext(policy.numeric_policy.get_context()):
        n = len(series.values)
        k = int(
            (Decimal(n) * policy.tail_fraction).to_integral_value(rounding=ROUND_CEILING)
        )
        resolution = Decimal(1) / Decimal(n)
        sufficient = n >= policy.minimum_total_count and k >= policy.minimum_tail_count
        if not sufficient:
            return TailMetricResult(
                None, None, n, k, resolution, False, policy.policy_digest
            )
        ordered = sorted(
            series.values,
            reverse=policy.loss_direction is LossDirection.HIGHER_IS_LOSS,
        )
        tail = ordered[:k]
        return TailMetricResult(
            value_at_risk=tail[-1],
            expected_shortfall=sum(tail, Decimal(0)) / Decimal(k),
            total_count=n,
            tail_count=k,
            empirical_resolution=resolution,
            sufficient=True,
            policy_digest=policy.policy_digest,
        )


@dataclass(frozen=True, slots=True)
class PathMetricResult:
    max_drawdown_amount: Decimal
    max_drawdown_ratio: Decimal | None
    max_underwater_seconds: Decimal | None


def _duration_seconds(start: datetime, end: datetime) -> Decimal:
    delta = end - start
    return (
        Decimal(delta.days * 86400 + delta.seconds)
        + Decimal(delta.microseconds) / Decimal(1_000_000)
    )


def compute_path_metrics(
    series: ObservedSeries,
    *,
    capital_denominator: Decimal | None = None,
) -> PathMetricResult:
    if capital_denominator is not None and capital_denominator <= Decimal(0):
        raise ValueError("capital_denominator must be positive")
    peak = series.values[0]
    max_drawdown = Decimal(0)
    underwater_start: datetime | None = None
    max_underwater = Decimal(0)
    for index, value in enumerate(series.values):
        if value >= peak:
            peak = value
            if underwater_start is not None and series.timestamps:
                max_underwater = max(
                    max_underwater,
                    _duration_seconds(underwater_start, series.timestamps[index]),
                )
                underwater_start = None
        else:
            max_drawdown = max(max_drawdown, peak - value)
            if underwater_start is None and series.timestamps:
                underwater_start = series.timestamps[index - 1] if index else series.timestamps[0]
    if underwater_start is not None and series.timestamps:
        max_underwater = max(
            max_underwater,
            _duration_seconds(underwater_start, series.timestamps[-1]),
        )
    ratio = (
        max_drawdown / capital_denominator
        if capital_denominator is not None
        else None
    )
    return PathMetricResult(
        max_drawdown_amount=max_drawdown,
        max_drawdown_ratio=ratio,
        max_underwater_seconds=max_underwater if series.timestamps else None,
    )


@dataclass(frozen=True, slots=True)
class MetricCondition:
    metric_name: str
    direction: MetricDirection
    threshold: Decimal
    required: bool = True

    def __post_init__(self) -> None:
        _require_text(self.metric_name, "metric_name")


@dataclass(frozen=True, slots=True)
class ScenarioDispositionPolicy:
    evaluation_scope: str
    conditions: tuple[MetricCondition, ...]
    invalidity_labels: tuple[str, ...]
    definition_mode: RegimeDefinitionMode
    development_boundary_id: str | None = None
    policy_digest: str = field(init=False)

    def __post_init__(self) -> None:
        _require_text(self.evaluation_scope, "evaluation_scope")
        if not self.conditions:
            raise ValueError("conditions cannot be empty")
        if self.definition_mode is RegimeDefinitionMode.RETROSPECTIVE_EXPLORATORY:
            raise ValueError("disposition policy cannot be retrospectively optimized")
        if self.definition_mode is RegimeDefinitionMode.DEVELOPMENT_FIT:
            if self.development_boundary_id is None:
                raise ValueError("DEVELOPMENT_FIT policy requires development_boundary_id")
        elif self.development_boundary_id is not None:
            raise ValueError("development_boundary_id only valid for DEVELOPMENT_FIT policy")
        object.__setattr__(
            self,
            "policy_digest",
            _digest(
                {
                    "evaluation_scope": self.evaluation_scope,
                    "conditions": tuple(
                        (c.metric_name, c.direction.value, c.threshold, c.required)
                        for c in self.conditions
                    ),
                    "invalidity_labels": self.invalidity_labels,
                    "definition_mode": self.definition_mode.value,
                    "development_boundary_id": self.development_boundary_id,
                }
            ),
        )


@dataclass(frozen=True, slots=True)
class ScenarioDispositionResult:
    disposition: ScenarioDisposition
    failed_metrics: tuple[str, ...]
    missing_required_metrics: tuple[str, ...]
    policy_digest: str


def _condition_passes(condition: MetricCondition, value: Decimal) -> bool:
    if condition.direction is MetricDirection.MAXIMIZE:
        return value >= condition.threshold
    return value <= condition.threshold


def evaluate_disposition(
    policy: ScenarioDispositionPolicy,
    metrics: Mapping[str, Decimal],
    *,
    invalidity_labels: Sequence[str] = (),
) -> ScenarioDispositionResult:
    if any(label in policy.invalidity_labels for label in invalidity_labels):
        return ScenarioDispositionResult(
            ScenarioDisposition.INVALID, (), (), policy.policy_digest
        )
    missing = tuple(
        condition.metric_name
        for condition in policy.conditions
        if condition.required and condition.metric_name not in metrics
    )
    if missing:
        return ScenarioDispositionResult(
            ScenarioDisposition.INCONCLUSIVE, (), missing, policy.policy_digest
        )
    evaluated = [
        (condition.metric_name, _condition_passes(condition, metrics[condition.metric_name]))
        for condition in policy.conditions
        if condition.metric_name in metrics
    ]
    if not evaluated:
        return ScenarioDispositionResult(
            ScenarioDisposition.INCONCLUSIVE, (), (), policy.policy_digest
        )
    failed = tuple(name for name, passed in evaluated if not passed)
    passed_count = sum(1 for _, passed in evaluated if passed)
    if passed_count == len(evaluated):
        disposition = ScenarioDisposition.FAVORABLE
    elif passed_count == 0:
        disposition = ScenarioDisposition.UNFAVORABLE
    else:
        disposition = ScenarioDisposition.CONDITIONAL
    return ScenarioDispositionResult(disposition, failed, (), policy.policy_digest)


def characterize_robustness(
    policy: ScenarioDispositionPolicy,
    scenario_metrics: Sequence[Mapping[str, Decimal]],
) -> RobustnessCharacterization:
    if not scenario_metrics:
        raise ValueError("scenario_metrics cannot be empty")
    dispositions = tuple(
        evaluate_disposition(policy, metrics).disposition for metrics in scenario_metrics
    )
    if all(value is ScenarioDisposition.FAVORABLE for value in dispositions):
        return RobustnessCharacterization.ROBUST_WITHIN_DECLARED_SCOPE
    if all(value is ScenarioDisposition.UNFAVORABLE for value in dispositions):
        return RobustnessCharacterization.FRAGILE
    return RobustnessCharacterization.MIXED


@dataclass(frozen=True, slots=True)
class ResearchAttemptRecord:
    artifact_digest: str
    evaluation_role: EvaluationRole
    protected_boundary_id: str | None
    disposition: str

    def __post_init__(self) -> None:
        _require_text(self.artifact_digest, "artifact_digest")
        _require_text(self.disposition, "disposition")
        if self.evaluation_role is EvaluationRole.PROTECTED_TEST:
            if self.protected_boundary_id is None:
                raise ValueError("PROTECTED_TEST attempt requires protected_boundary_id")
        elif self.protected_boundary_id is not None:
            raise ValueError("protected_boundary_id is only valid for PROTECTED_TEST attempt")


@dataclass(frozen=True, slots=True)
class ProtectedAdaptationRecord:
    protected_boundary_id: str
    source_artifact_digest: str
    derived_artifact_digest: str

    def __post_init__(self) -> None:
        _require_text(self.protected_boundary_id, "protected_boundary_id")
        _require_text(self.source_artifact_digest, "source_artifact_digest")
        _require_text(self.derived_artifact_digest, "derived_artifact_digest")


@dataclass(frozen=True, slots=True)
class ResearchArtifactRecord:
    artifact_digest: str
    kind: ResearchArtifactKind
    predeclared: bool
    parent_digests: tuple[str, ...] = ()
    protected_informed: bool = False

    def __post_init__(self) -> None:
        _require_text(self.artifact_digest, "artifact_digest")
        if any(not digest for digest in self.parent_digests):
            raise ValueError("parent_digests must contain non-empty identities")


class ScenarioResearchHistory:
    def __init__(self) -> None:
        self._artifacts: list[ResearchArtifactRecord] = []
        self._attempts: list[ResearchAttemptRecord] = []
        self._adaptations: list[ProtectedAdaptationRecord] = []

    @property
    def artifacts(self) -> tuple[ResearchArtifactRecord, ...]:
        return tuple(self._artifacts)

    @property
    def attempts(self) -> tuple[ResearchAttemptRecord, ...]:
        return tuple(self._attempts)

    @property
    def adaptations(self) -> tuple[ProtectedAdaptationRecord, ...]:
        return tuple(self._adaptations)

    @property
    def history_digest(self) -> str:
        return _digest(
            {
                "artifacts": tuple(
                    (
                        record.artifact_digest,
                        record.kind.value,
                        record.predeclared,
                        record.parent_digests,
                        record.protected_informed,
                    )
                    for record in self._artifacts
                ),
                "attempts": tuple(
                    (
                        record.artifact_digest,
                        record.evaluation_role.value,
                        record.protected_boundary_id,
                        record.disposition,
                    )
                    for record in self._attempts
                ),
                "adaptations": tuple(
                    (
                        record.protected_boundary_id,
                        record.source_artifact_digest,
                        record.derived_artifact_digest,
                    )
                    for record in self._adaptations
                ),
            }
        )

    def record_artifact(self, record: ResearchArtifactRecord) -> None:
        if any(existing.artifact_digest == record.artifact_digest for existing in self._artifacts):
            raise ValueError("research artifact digest already registered")
        known = {existing.artifact_digest for existing in self._artifacts}
        if any(parent not in known for parent in record.parent_digests):
            raise ValueError("parent_digests must reference previously registered artifacts")
        self._artifacts.append(record)

    def record_scenario_spec(self, scenario: ScenarioSpec) -> None:
        if not scenario.predeclared:
            raise ValueError("scenario predeclaration history requires predeclared ScenarioSpec")
        if scenario.research_history_ref != self.history_digest:
            raise ValueError(
                "ScenarioSpec research_history_ref must equal history digest before registration"
            )
        self.record_artifact(
            ResearchArtifactRecord(
                artifact_digest=scenario.scenario_digest,
                kind=ResearchArtifactKind.SCENARIO_SPEC,
                predeclared=True,
            )
        )

    def record_scenario_grid(self, grid: ScenarioGrid) -> None:
        registered = {record.artifact_digest for record in self._artifacts}
        parents = tuple(scenario.scenario_digest for scenario in grid.scenarios)
        if any(parent not in registered for parent in parents):
            raise ValueError("ScenarioGrid requires all ScenarioSpec values registered first")
        self.record_artifact(
            ResearchArtifactRecord(
                artifact_digest=grid.grid_digest,
                kind=ResearchArtifactKind.SCENARIO_GRID,
                predeclared=grid.predeclared,
                parent_digests=parents,
            )
        )

    def record_attempt(self, record: ResearchAttemptRecord) -> None:
        if not any(
            artifact.artifact_digest == record.artifact_digest for artifact in self._artifacts
        ):
            raise ValueError("research attempt must reference a registered artifact")
        self._attempts.append(record)

    def record_protected_adaptation(self, record: ProtectedAdaptationRecord) -> None:
        source_seen = any(
            attempt.artifact_digest == record.source_artifact_digest
            and attempt.evaluation_role is EvaluationRole.PROTECTED_TEST
            and attempt.protected_boundary_id == record.protected_boundary_id
            for attempt in self._attempts
        )
        if not source_seen:
            raise ValueError("protected adaptation requires prior protected evaluation evidence")
        derived = next(
            (
                artifact
                for artifact in self._artifacts
                if artifact.artifact_digest == record.derived_artifact_digest
            ),
            None,
        )
        if derived is None:
            raise ValueError("protected adaptation derived artifact must be registered")
        if not derived.protected_informed:
            raise ValueError(
                "protected adaptation derived artifact must be marked protected_informed"
            )
        self._adaptations.append(record)

    def _protected_informed_digests(self, protected_boundary_id: str) -> set[str]:
        informed = {
            record.derived_artifact_digest
            for record in self._adaptations
            if record.protected_boundary_id == protected_boundary_id
        }
        changed = True
        while changed:
            changed = False
            for artifact in self._artifacts:
                if (
                    artifact.artifact_digest not in informed
                    and any(parent in informed for parent in artifact.parent_digests)
                ):
                    informed.add(artifact.artifact_digest)
                    changed = True
        return informed

    def check_admissibility(
        self,
        *,
        artifact_digest: str,
        evaluation_role: EvaluationRole,
        protected_boundary_id: str | None,
        evaluation_history: EvaluationHistory | None = None,
        candidate_id: str | None = None,
        parent_candidate_ids: tuple[str, ...] = (),
    ) -> None:
        if evaluation_role is not EvaluationRole.PROTECTED_TEST:
            return
        if protected_boundary_id is None:
            raise ValueError("PROTECTED_TEST requires protected_boundary_id")
        if artifact_digest in self._protected_informed_digests(protected_boundary_id):
            raise ProtectedEvidenceReuseError(
                "protected-informed artifact cannot reuse the same protected boundary"
            )
        if evaluation_history is not None:
            if candidate_id is None:
                raise ValueError("candidate_id is required when EvaluationHistory is supplied")
            evaluation_history.check_admissibility(
                candidate_id=candidate_id,
                protected_boundary_id=protected_boundary_id,
                role=evaluation_role,
                parent_candidate_ids=parent_candidate_ids,
            )


@dataclass(frozen=True, slots=True)
class ScenarioRunManifest:
    boundary_digest: str
    regime_definition_digests: tuple[str, ...]
    scenario_grid_digest: str | None
    observed_series_digest: str | None
    disposition_policy_digest: str | None
    research_history_digest: str
    result_digest: str
    code_revision: str
    manifest_digest: str = field(init=False)

    def __post_init__(self) -> None:
        for value, name in (
            (self.boundary_digest, "boundary_digest"),
            (self.research_history_digest, "research_history_digest"),
            (self.result_digest, "result_digest"),
            (self.code_revision, "code_revision"),
        ):
            _require_text(value, name)
        object.__setattr__(
            self,
            "manifest_digest",
            _digest(
                {
                    "boundary_digest": self.boundary_digest,
                    "regime_definition_digests": self.regime_definition_digests,
                    "scenario_grid_digest": self.scenario_grid_digest,
                    "observed_series_digest": self.observed_series_digest,
                    "disposition_policy_digest": self.disposition_policy_digest,
                    "research_history_digest": self.research_history_digest,
                    "result_digest": self.result_digest,
                    "code_revision": self.code_revision,
                }
            ),
        )


def verify_deterministic_equivalence(
    first: ScenarioRunManifest,
    second: ScenarioRunManifest,
) -> str:
    if first.manifest_digest != second.manifest_digest:
        raise ValueError("ScenarioRunManifest deterministic equivalence violation")
    return first.manifest_digest
