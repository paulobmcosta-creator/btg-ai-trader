"""Unit tests for StatisticalSample, PredictionResult, and CandidateIdentity domain models."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from btg_ai_trader.statistical_baselines.domain import (
    CandidateIdentity,
    EvaluationRole,
    PredictionResult,
    StatisticalSample,
    TargetSemantics,
)


def test_target_semantics_enum() -> None:
    assert TargetSemantics.CONTINUOUS.value == "CONTINUOUS"
    assert TargetSemantics.BINARY_PROBABILITY.value == "BINARY_PROBABILITY"
    assert TargetSemantics.CATEGORICAL.value == "CATEGORICAL"


def test_evaluation_role_enum() -> None:
    assert EvaluationRole.DEVELOPMENT.value == "DEVELOPMENT"
    assert EvaluationRole.TRAINING_FIT.value == "TRAINING_FIT"
    assert EvaluationRole.VALIDATION_SELECTION.value == "VALIDATION_SELECTION"
    assert EvaluationRole.PROTECTED_TEST.value == "PROTECTED_TEST"


def test_statistical_sample_valid_continuous() -> None:
    t0 = datetime(2026, 9, 1, 10, 0, tzinfo=UTC)
    t1 = datetime(2026, 9, 1, 10, 5, tzinfo=UTC)
    sample = StatisticalSample(
        sample_id="s_001",
        feature_knowledge_time=t0,
        target_knowledge_time=t1,
        target_value=Decimal("123.45"),
        target_semantics=TargetSemantics.CONTINUOUS,
        reference_value=Decimal("120.00"),
        information_interval=(t0, t1),
        source_lineage="WINV26.M1",
        metadata={"key": "val"},
    )
    assert sample.sample_id == "s_001"
    assert sample.is_causally_admissible_for_fit(t1) is True
    assert sample.is_causally_admissible_for_fit(t0) is False


def test_statistical_sample_valid_binary_probability() -> None:
    t0 = datetime(2026, 9, 1, 10, 0, tzinfo=UTC)
    t1 = datetime(2026, 9, 1, 10, 1, tzinfo=UTC)

    sample_int = StatisticalSample(
        sample_id="s_bin_int",
        feature_knowledge_time=t0,
        target_knowledge_time=t1,
        target_value=1,
        target_semantics=TargetSemantics.BINARY_PROBABILITY,
    )
    assert sample_int.target_value == 1

    sample_dec = StatisticalSample(
        sample_id="s_bin_dec",
        feature_knowledge_time=t0,
        target_knowledge_time=t1,
        target_value=Decimal(0),
        target_semantics=TargetSemantics.BINARY_PROBABILITY,
    )
    assert sample_dec.target_value == Decimal(0)


def test_statistical_sample_valid_categorical() -> None:
    t0 = datetime(2026, 9, 1, 10, 0, tzinfo=UTC)
    t1 = datetime(2026, 9, 1, 10, 1, tzinfo=UTC)
    sample = StatisticalSample(
        sample_id="s_cat",
        feature_knowledge_time=t0,
        target_knowledge_time=t1,
        target_value="UP",
        target_semantics=TargetSemantics.CATEGORICAL,
    )
    assert sample.target_value == "UP"


def test_statistical_sample_invalid_id() -> None:
    t0 = datetime(2026, 9, 1, 10, 0, tzinfo=UTC)
    with pytest.raises(ValueError, match="non-empty string"):
        StatisticalSample(
            sample_id="",
            feature_knowledge_time=t0,
            target_knowledge_time=t0,
            target_value=Decimal("1"),
            target_semantics=TargetSemantics.CONTINUOUS,
        )


def test_statistical_sample_naive_datetime_rejected() -> None:
    naive_t = datetime(2026, 9, 1, 10, 0)
    aware_t = datetime(2026, 9, 1, 10, 0, tzinfo=UTC)

    with pytest.raises(ValueError, match="timezone-aware"):
        StatisticalSample(
            sample_id="s_naive_feat",
            feature_knowledge_time=naive_t,
            target_knowledge_time=aware_t,
            target_value=Decimal("1"),
            target_semantics=TargetSemantics.CONTINUOUS,
        )

    with pytest.raises(ValueError, match="timezone-aware"):
        StatisticalSample(
            sample_id="s_naive_tgt",
            feature_knowledge_time=aware_t,
            target_knowledge_time=naive_t,
            target_value=Decimal("1"),
            target_semantics=TargetSemantics.CONTINUOUS,
        )


def test_statistical_sample_feature_after_target_rejected() -> None:
    t0 = datetime(2026, 9, 1, 10, 5, tzinfo=UTC)
    t1 = datetime(2026, 9, 1, 10, 0, tzinfo=UTC)
    with pytest.raises(ValueError, match="cannot be later than target_knowledge_time"):
        StatisticalSample(
            sample_id="s_inv",
            feature_knowledge_time=t0,
            target_knowledge_time=t1,
            target_value=Decimal("1"),
            target_semantics=TargetSemantics.CONTINUOUS,
        )


def test_statistical_sample_information_interval_validation() -> None:
    t0 = datetime(2026, 9, 1, 10, 0, tzinfo=UTC)
    t1 = datetime(2026, 9, 1, 10, 5, tzinfo=UTC)
    naive_t = datetime(2026, 9, 1, 10, 0)

    with pytest.raises(ValueError, match="timezone-aware"):
        StatisticalSample(
            sample_id="s_info_naive_start",
            feature_knowledge_time=t0,
            target_knowledge_time=t1,
            target_value=Decimal("1"),
            target_semantics=TargetSemantics.CONTINUOUS,
            information_interval=(naive_t, t1),
        )

    with pytest.raises(ValueError, match="timezone-aware"):
        StatisticalSample(
            sample_id="s_info_naive_end",
            feature_knowledge_time=t0,
            target_knowledge_time=t1,
            target_value=Decimal("1"),
            target_semantics=TargetSemantics.CONTINUOUS,
            information_interval=(t0, naive_t),
        )

    with pytest.raises(ValueError, match="cannot be after end"):
        StatisticalSample(
            sample_id="s_info_inv",
            feature_knowledge_time=t0,
            target_knowledge_time=t1,
            target_value=Decimal("1"),
            target_semantics=TargetSemantics.CONTINUOUS,
            information_interval=(t1, t0),
        )


def test_statistical_sample_type_mismatches() -> None:
    t0 = datetime(2026, 9, 1, 10, 0, tzinfo=UTC)
    t1 = datetime(2026, 9, 1, 10, 5, tzinfo=UTC)

    # Continuous requires Decimal
    with pytest.raises(TypeError, match="must be Decimal"):
        StatisticalSample(
            sample_id="s_mismatch_cont",
            feature_knowledge_time=t0,
            target_knowledge_time=t1,
            target_value=123.45,  # type: ignore[arg-type]
            target_semantics=TargetSemantics.CONTINUOUS,
        )

    # Binary probability requires 0 or 1
    with pytest.raises(ValueError, match="must be 0 or 1"):
        StatisticalSample(
            sample_id="s_mismatch_bin_int",
            feature_knowledge_time=t0,
            target_knowledge_time=t1,
            target_value=2,
            target_semantics=TargetSemantics.BINARY_PROBABILITY,
        )

    with pytest.raises(ValueError, match="must be 0 or 1"):
        StatisticalSample(
            sample_id="s_mismatch_bin_dec",
            feature_knowledge_time=t0,
            target_knowledge_time=t1,
            target_value=Decimal("0.5"),
            target_semantics=TargetSemantics.BINARY_PROBABILITY,
        )

    with pytest.raises(TypeError, match="must be int or Decimal"):
        StatisticalSample(
            sample_id="s_mismatch_bin_str",
            feature_knowledge_time=t0,
            target_knowledge_time=t1,
            target_value="1",
            target_semantics=TargetSemantics.BINARY_PROBABILITY,
        )

    # Categorical requires str
    with pytest.raises(TypeError, match="must be str"):
        StatisticalSample(
            sample_id="s_mismatch_cat",
            feature_knowledge_time=t0,
            target_knowledge_time=t1,
            target_value=123,
            target_semantics=TargetSemantics.CATEGORICAL,
        )

    # Unsupported target semantics
    with pytest.raises(ValueError, match="Unsupported target_semantics"):
        StatisticalSample(
            sample_id="s_unsupported",
            feature_knowledge_time=t0,
            target_knowledge_time=t1,
            target_value="val",
            target_semantics="UNKNOWN",  # type: ignore[arg-type]
        )


def test_causal_admissibility_naive_cutoff_rejected() -> None:
    t0 = datetime(2026, 9, 1, 10, 0, tzinfo=UTC)
    t1 = datetime(2026, 9, 1, 10, 5, tzinfo=UTC)
    sample = StatisticalSample(
        sample_id="s_001",
        feature_knowledge_time=t0,
        target_knowledge_time=t1,
        target_value=Decimal("10"),
        target_semantics=TargetSemantics.CONTINUOUS,
    )
    with pytest.raises(ValueError, match="timezone-aware"):
        sample.is_causally_admissible_for_fit(datetime(2026, 9, 1, 10, 5))


def test_prediction_result() -> None:
    t0 = datetime(2026, 9, 1, 10, 0, tzinfo=UTC)
    res = PredictionResult(
        sample_id="s_001",
        prediction_time=t0,
        predicted_value=Decimal("105.5"),
        predicted_probability=Decimal("0.75"),
        predicted_class="UP",
        is_cold_start=False,
    )
    assert res.predicted_value == Decimal("105.5")
    assert res.predicted_probability == Decimal("0.75")
    assert res.predicted_class == "UP"
    assert res.is_cold_start is False


def test_prediction_result_invalid_probability() -> None:
    t0 = datetime(2026, 9, 1, 10, 0, tzinfo=UTC)
    with pytest.raises(ValueError, match="must be in"):
        PredictionResult(
            sample_id="s_001",
            prediction_time=t0,
            predicted_probability=Decimal("1.5"),
        )
    with pytest.raises(ValueError, match="must be in"):
        PredictionResult(
            sample_id="s_001",
            prediction_time=t0,
            predicted_probability=Decimal("-0.1"),
        )


def test_candidate_identity_deterministic_and_parameters() -> None:
    cid1 = CandidateIdentity(
        baseline_type="HistoricalMeanBaseline",
        parameters={"window": 10, "weight": Decimal("1.5"), "nested": {"sub": [Decimal("0.1"), 2]}},
        target_semantics=TargetSemantics.CONTINUOUS,
        code_revision="git:abc1234",
    )
    cid2 = CandidateIdentity(
        baseline_type="HistoricalMeanBaseline",
        parameters={"window": 10, "weight": Decimal("1.5"), "nested": {"sub": [Decimal("0.1"), 2]}},
        target_semantics=TargetSemantics.CONTINUOUS,
        code_revision="git:abc1234",
    )
    assert cid1.identity_hash == cid2.identity_hash

    # Parameter change alters hash
    cid_diff_param = CandidateIdentity(
        baseline_type="HistoricalMeanBaseline",
        parameters={"window": 11, "weight": Decimal("1.5"), "nested": {"sub": [Decimal("0.1"), 2]}},
        target_semantics=TargetSemantics.CONTINUOUS,
        code_revision="git:abc1234",
    )
    assert cid1.identity_hash != cid_diff_param.identity_hash

    # Code revision change alters hash
    cid_diff_code = CandidateIdentity(
        baseline_type="HistoricalMeanBaseline",
        parameters={"window": 10, "weight": Decimal("1.5"), "nested": {"sub": [Decimal("0.1"), 2]}},
        target_semantics=TargetSemantics.CONTINUOUS,
        code_revision="git:def5678",
    )
    assert cid1.identity_hash != cid_diff_code.identity_hash


def test_candidate_identity_validation() -> None:
    with pytest.raises(ValueError, match="baseline_type must be a non-empty string"):
        CandidateIdentity(
            baseline_type="",
            parameters={},
            target_semantics=TargetSemantics.CONTINUOUS,
            code_revision="git:123",
        )
    with pytest.raises(ValueError, match="code_revision must be a non-empty string"):
        CandidateIdentity(
            baseline_type="Mean",
            parameters={},
            target_semantics=TargetSemantics.CONTINUOUS,
            code_revision="",
        )


def test_candidate_identity_custom_param_types() -> None:
    class CustomObj:
        def __str__(self) -> str:
            return "custom_val"

    cid = CandidateIdentity(
        baseline_type="CustomBaseline",
        parameters={"custom": CustomObj()},
        target_semantics=TargetSemantics.CATEGORICAL,
        code_revision="git:rev1",
    )
    assert cid.identity_hash is not None


def test_prediction_result_none_probability() -> None:
    t0 = datetime(2026, 9, 1, 10, 0, tzinfo=UTC)
    res = PredictionResult(
        sample_id="s_none_prob",
        prediction_time=t0,
        predicted_probability=None,
    )
    assert res.predicted_probability is None
