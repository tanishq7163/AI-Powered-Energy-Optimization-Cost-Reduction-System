from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class EnergyRecordBase(BaseModel):
    date: date
    timestamp: datetime
    energy_consumption_kwh: float = Field(ge=0)
    voltage: float
    current: float
    power_factor: float = Field(ge=0, le=1.5)
    tariff_rate: float = Field(ge=0)
    temperature: float
    occupancy: float = Field(ge=0)
    device_name: str


class EnergyRecordCreate(EnergyRecordBase):
    pass


class EnergyRecordUpdate(BaseModel):
    energy_consumption_kwh: float | None = None
    voltage: float | None = None
    current: float | None = None
    power_factor: float | None = None
    tariff_rate: float | None = None
    temperature: float | None = None
    occupancy: float | None = None
    device_name: str | None = None


class EnergyRecordRead(EnergyRecordBase):
    id: int

    model_config = {"from_attributes": True}


class AggregatedPoint(BaseModel):
    period: str
    energy_consumption_kwh: float
    average_consumption_kwh: float
    cost: float


class AnalyticsSummary(BaseModel):
    total_energy: float
    average_consumption: float
    peak_consumption: float
    minimum_consumption: float
    estimated_monthly_cost: float
    savings_opportunity: float
    trend_direction: str
    peak_hour: int
    peak_hour_average: float
    seasonal_profile: list[dict[str, Any]]
    daily_trend: list[AggregatedPoint]
    weekly_trend: list[AggregatedPoint]
    monthly_trend: list[AggregatedPoint]
    yearly_trend: list[AggregatedPoint]
    peak_hour_heatmap: list[dict[str, Any]]
    device_breakdown: list[dict[str, Any]]


class ModelMetric(BaseModel):
    model_name: str
    mae: float
    mse: float
    rmse: float
    mape: float
    r2: float
    status: str = "trained"


class ForecastPoint(BaseModel):
    timestamp: datetime
    predicted_consumption_kwh: float
    lower_bound: float
    upper_bound: float


class ForecastResponse(BaseModel):
    best_model: str
    selected_horizon: Literal["24h", "7d", "30d"]
    metrics: list[ModelMetric]
    forecast: list[ForecastPoint]


class AnomalyItem(BaseModel):
    timestamp: datetime
    device_name: str
    energy_consumption_kwh: float
    anomaly_score: float
    severity_level: str
    description: str
    method: str


class AnomalyResponse(BaseModel):
    count: int
    anomalies: list[AnomalyItem]
    severity_breakdown: list[dict[str, Any]]


class CostSummary(BaseModel):
    current_cost: float
    daily_cost: float
    weekly_cost: float
    monthly_cost: float
    forecast_cost: float
    potential_savings: float
    peak_cost_contribution: float
    breakdown: list[dict[str, Any]]


class RecommendationItem(BaseModel):
    category: str
    priority: str
    title: str
    description: str
    estimated_savings: float
    source_context: dict[str, Any]


class RecommendationResponse(BaseModel):
    generated_at: datetime
    recommendations: list[RecommendationItem]


class ReportResponse(BaseModel):
    id: int
    report_name: str
    file_path: str
    created_at: datetime

    model_config = {"from_attributes": True}


class DashboardResponse(BaseModel):
    analytics: AnalyticsSummary
    forecast: ForecastResponse
    anomalies: AnomalyResponse
    costs: CostSummary
    recommendations: RecommendationResponse


class DatasetGenerationRequest(BaseModel):
    records: int = Field(default=50000, ge=1000, le=250000)


class DatasetGenerationResponse(BaseModel):
    csv_path: str
    excel_path: str
    records: int


class SettingsResponse(BaseModel):
    app_name: str
    database_url: str
    reports_dir: str
    dataset_dir: str
    models_dir: str
