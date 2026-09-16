"""Lossless market-data normalization and data-quality evidence platform (S2-B)."""

from btg_ai_trader.data_platform.normalization import (
    NormalizedMarketBatch,
    normalize_market_batch,
)
from btg_ai_trader.data_platform.quality import (
    QualityFinding,
    QualityFindingCategory,
    QualityFindingCode,
    evaluate_envelope_quality,
)
from btg_ai_trader.replay import CausalLane

__all__ = [
    "CausalLane",
    "NormalizedMarketBatch",
    "QualityFinding",
    "QualityFindingCategory",
    "QualityFindingCode",
    "evaluate_envelope_quality",
    "normalize_market_batch",
]
