from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from db.models import Recommendation
from schemas.contracts import RecommendationItem, RecommendationResponse
from services.analytics_service import get_analytics_summary
from services.anomaly_service import detect_anomalies
from services.cost_service import get_cost_summary
from services.forecast_service import generate_forecast


def generate_recommendations(db: Session) -> RecommendationResponse:
    analytics = get_analytics_summary(db)
    anomalies = detect_anomalies(db)
    costs = get_cost_summary(db)
    forecast = generate_forecast(db, "7d")

    recommendations: list[RecommendationItem] = []

    if analytics.peak_hour_average > analytics.average_consumption * 1.25:
        recommendations.append(
            RecommendationItem(
                category="Peak Shifting",
                priority="High",
                title="Reduce peak-hour usage",
                description=(
                    f"Consumption spikes around {analytics.peak_hour}:00. Shift flexible loads such as HVAC pre-cooling,"
                    " charging, or heavy processing to lower-tariff periods to flatten the load curve."
                ),
                estimated_savings=round(costs.peak_cost_contribution * costs.monthly_cost * 0.22, 2),
                source_context={"peak_hour": analytics.peak_hour, "peak_hour_average": analytics.peak_hour_average},
            )
        )

    if anomalies.count > 0:
        critical_count = sum(1 for item in anomalies.anomalies if item.severity_level in {"High", "Critical"})
        recommendations.append(
            RecommendationItem(
                category="Anomaly Response",
                priority="High" if critical_count else "Medium",
                title="Review abnormal devices",
                description=(
                    f"Detected {anomalies.count} anomalies, including {critical_count} high-severity events."
                    " Inspect those timestamps and devices for leakage, idle consumption, or failing equipment."
                ),
                estimated_savings=round(min(costs.potential_savings * 0.35, costs.monthly_cost * 0.18), 2),
                source_context={"anomaly_count": anomalies.count, "critical_count": critical_count},
            )
        )

    if forecast.forecast:
        forecast_average = sum(point.predicted_consumption_kwh for point in forecast.forecast) / len(forecast.forecast)
        if forecast_average > analytics.average_consumption * 1.08:
            recommendations.append(
                RecommendationItem(
                    category="Forecast Planning",
                    priority="Medium",
                    title="Optimize operating schedules",
                    description=(
                        "The next 7-day forecast is above the recent operating baseline."
                        " Review production plans, HVAC setpoints, and shift schedules before the demand increase materializes."
                    ),
                    estimated_savings=round(costs.forecast_cost * 0.1, 2),
                    source_context={"forecast_average": forecast_average, "recent_average": analytics.average_consumption},
                )
            )

    if costs.potential_savings > 0:
        recommendations.append(
            RecommendationItem(
                category="Standby Reduction",
                priority="Medium",
                title="Reduce standby power consumption",
                description=(
                    "Off-hours consumption remains non-trivial. Apply shutdown schedules, smart strips, or automation"
                    " to trim loads when occupancy is low."
                ),
                estimated_savings=round(costs.potential_savings * 0.45, 2),
                source_context={"potential_savings": costs.potential_savings},
            )
        )

    if not recommendations:
        recommendations.append(
            RecommendationItem(
                category="Optimization",
                priority="Low",
                title="Maintain current efficiency controls",
                description="No major inefficiency drivers are currently present. Keep tracking tariff alignment and device-level trends.",
                estimated_savings=0,
                source_context={},
            )
        )

    db.query(Recommendation).delete()
    db.commit()
    for item in recommendations:
        db.add(Recommendation(**item.model_dump()))
    db.commit()

    return RecommendationResponse(generated_at=datetime.utcnow(), recommendations=recommendations)
