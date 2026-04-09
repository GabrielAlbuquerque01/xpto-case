from datetime import datetime

from pydantic import BaseModel


class ClassificationRequest(BaseModel):
    text: str
    model_type: str
    save_prediction: bool = True


class ClassificationResponse(BaseModel):
    macro: str
    macro_confidence: float
    micro: str
    micro_confidence: float
    model: str
    is_ambiguous: bool = False
    metadata: dict | None = None


class GetClassificationResponse(BaseModel):
    id: int
    text: str
    model_type: str
    macro: str
    micro: str
    macro_confidence: float
    micro_confidence: float
    is_ambiguous: bool
    created_at: datetime


class MetricItem(BaseModel):
    label: str
    value: int


class DailyMetricItem(BaseModel):
    date: str
    value: int


class MetricsSummaryResponse(BaseModel):
    total_predictions: int
    ambiguous_predictions: int
    ambiguity_rate: float
    avg_macro_confidence: float
    avg_micro_confidence: float
    by_model: list[MetricItem]


class MetricsDistributionResponse(BaseModel):
    macro_distribution: list[MetricItem]
    micro_distribution: list[MetricItem]
    daily_volume: list[DailyMetricItem]