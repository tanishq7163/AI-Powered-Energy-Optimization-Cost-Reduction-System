from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sqlalchemy.orm import Session

from schemas.contracts import AggregatedPoint, AnalyticsSummary
from services.data_service import load_records_dataframe


def _aggregate(frame: pd.DataFrame, frequency: str) -> list[AggregatedPoint]:
    if frame.empty:
        return []
    grouped = (
        frame.set_index("timestamp")
        .groupby(pd.Grouper(freq=frequency))
        .agg(
            energy_consumption_kwh=("energy_consumption_kwh", "sum"),
            average_consumption_kwh=("energy_consumption_kwh", "mean"),
            cost=("cost", "sum"),
        )
        .reset_index()
    )
    return [
        AggregatedPoint(
            period=row["timestamp"].strftime("%Y-%m-%d"),
            energy_consumption_kwh=round(float(row["energy_consumption_kwh"]), 3),
            average_consumption_kwh=round(float(row["average_consumption_kwh"]), 3),
            cost=round(float(row["cost"]), 2),
        )
        for _, row in grouped.iterrows()
    ]


def get_analytics_summary(
    db: Session,
    start_date: date | None = None,
    end_date: date | None = None,
) -> AnalyticsSummary:
    frame = load_records_dataframe(db, start_date, end_date)
    if frame.empty:
        return AnalyticsSummary(
            total_energy=0,
            average_consumption=0,
            peak_consumption=0,
            minimum_consumption=0,
            estimated_monthly_cost=0,
            savings_opportunity=0,
            trend_direction="stable",
            peak_hour=0,
            peak_hour_average=0,
            seasonal_profile=[],
            daily_trend=[],
            weekly_trend=[],
            monthly_trend=[],
            yearly_trend=[],
            peak_hour_heatmap=[],
            device_breakdown=[],
        )

    frame["cost"] = frame["energy_consumption_kwh"] * frame["tariff_rate"]
    total_energy = float(frame["energy_consumption_kwh"].sum())
    average_consumption = float(frame["energy_consumption_kwh"].mean())
    peak_consumption = float(frame["energy_consumption_kwh"].max())
    minimum_consumption = float(frame["energy_consumption_kwh"].min())

    monthly_costs = frame.set_index("timestamp").groupby(pd.Grouper(freq="ME"))["cost"].sum()
    estimated_monthly_cost = float(monthly_costs.iloc[-1]) if not monthly_costs.empty else float(frame["cost"].sum())

    grouped_hours = frame.groupby("hour")["energy_consumption_kwh"].mean().sort_values(ascending=False)
    peak_hour = int(grouped_hours.index[0]) if not grouped_hours.empty else 0
    peak_hour_average = float(grouped_hours.iloc[0]) if not grouped_hours.empty else 0

    trend_input = np.arange(len(frame)).reshape(-1, 1)
    model = LinearRegression().fit(trend_input, frame["energy_consumption_kwh"])
    slope = float(model.coef_[0])
    trend_direction = "increasing" if slope > 0.01 else "decreasing" if slope < -0.01 else "stable"

    seasonal_profile = (
        frame.groupby("season")[["energy_consumption_kwh", "cost"]]
        .mean()
        .reset_index()
        .rename(columns={"energy_consumption_kwh": "average_energy", "cost": "average_cost"})
        .to_dict(orient="records")
    )

    peak_heatmap = (
        frame.groupby(["weekday", "hour"])["energy_consumption_kwh"]
        .mean()
        .reset_index()
        .rename(columns={"energy_consumption_kwh": "value"})
        .to_dict(orient="records")
    )

    device_breakdown = (
        frame.groupby("device_name")[["energy_consumption_kwh", "cost"]]
        .sum()
        .sort_values("energy_consumption_kwh", ascending=False)
        .head(12)
        .reset_index()
        .to_dict(orient="records")
    )

    peak_window = frame[frame["hour"].between(17, 22)]["cost"].sum()
    off_hours = frame[frame["hour"].between(0, 5)]["cost"].sum()
    savings_opportunity = float(max(peak_window * 0.14 + off_hours * 0.05, 0))

    return AnalyticsSummary(
        total_energy=round(total_energy, 3),
        average_consumption=round(average_consumption, 3),
        peak_consumption=round(peak_consumption, 3),
        minimum_consumption=round(minimum_consumption, 3),
        estimated_monthly_cost=round(estimated_monthly_cost, 2),
        savings_opportunity=round(savings_opportunity, 2),
        trend_direction=trend_direction,
        peak_hour=peak_hour,
        peak_hour_average=round(peak_hour_average, 3),
        seasonal_profile=seasonal_profile,
        daily_trend=_aggregate(frame, "D"),
        weekly_trend=_aggregate(frame, "W"),
        monthly_trend=_aggregate(frame, "ME"),
        yearly_trend=_aggregate(frame, "YE"),
        peak_hour_heatmap=peak_heatmap,
        device_breakdown=device_breakdown,
    )
