from datetime import datetime
from pydantic import BaseModel, Field

class SecondaryPrediction(BaseModel):
    macro: str
    detail: str


class ClassificationRequest(BaseModel):
    text: str
    classifier: str


class ClassificationResponse(BaseModel):
    classifier: str
    macro: str
    detail: str
    macro_confidence: float
    detail_confidence: float
    secondary_predictions: list[SecondaryPrediction] = Field(default_factory=list)


class GetClassificationResponse(BaseModel):
    id: int
    text: str
    classifier: str
    macro: str
    detail: str
    macro_confidence: float
    detail_confidence: float
    secondary_predictions: list[SecondaryPrediction] = Field(default_factory=list)
    created_at: datetime


class MetricItem(BaseModel):
    label: str
    value: int


class DailyMetricItem(BaseModel):
    date: str
    value: int


class MetricsSummaryResponse(BaseModel):
    total_predictions: int
    avg_macro_confidence: float
    avg_detail_confidence: float
    by_classifier: list[MetricItem]


class MetricsDistributionResponse(BaseModel):
    macro_distribution: list[MetricItem]
    detail_distribution: list[MetricItem]
    daily_volume: list[DailyMetricItem]