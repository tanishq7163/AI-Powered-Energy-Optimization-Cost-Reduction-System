from __future__ import annotations

from datetime import datetime

import pandas as pd
from sqlalchemy.orm import Session

from db.models import CostEstimation, Forecast
from schemas.contracts import CostSummary
from services.data_service import load_records_dataframe


def get_cost_summary(db: Session) -> CostSummary:
    frame = load_records_dataframe(db)
    if frame.empty:
        return CostSummary(
            current_cost=0,
            daily_cost=0,
            weekly_cost=0,
            monthly_cost=0,
            forecast_cost=0,
            potential_savings=0,
            peak_cost_contribution=0,
            breakdown=[],
        )

    frame["cost"] = frame["energy_consumption_kwh"] * frame["tariff_rate"]
    latest_timestamp = frame["timestamp"].max()
    current_slice = frame[frame["timestamp"] == latest_timestamp]
    daily_slice = frame[frame["timestamp"] >= latest_timestamp - pd.Timedelta(days=1)]
    weekly_slice = frame[frame["timestamp"] >= latest_timestamp - pd.Timedelta(days=7)]
    monthly_slice = frame[frame["timestamp"] >= latest_timestamp - pd.Timedelta(days=30)]

    peak_cost = frame[frame["hour"].between(17, 22)]["cost"].sum()
    total_cost = frame["cost"].sum()
    forecast_points = (
        db.query(Forecast.forecast_time, Forecast.predicted_consumption_kwh)
        .order_by(Forecast.forecast_time.asc())
        .all()
    )
    recent_tariff = float(frame["tariff_rate"].tail(24).mean()) if not frame.empty else 0.0
    forecast_energy = float(sum(row[1] for row in forecast_points))
    forecast_cost = forecast_energy * recent_tariff
    potential_savings = peak_cost * 0.16 + monthly_slice[monthly_slice["occupancy"] < 10]["cost"].sum() * 0.09

    breakdown = (
        frame.groupby("device_name")[["energy_consumption_kwh", "cost"]]
        .sum()
        .sort_values("cost", ascending=False)
        .head(12)
        .reset_index()
        .to_dict(orient="records")
    )

    snapshots = [
        ("daily", daily_slice),
        ("weekly", weekly_slice),
        ("monthly", monthly_slice),
    ]
    db.query(CostEstimation).delete()
    cost_records = []
    for period_type, slice_frame in snapshots:
        if slice_frame.empty:
            continue
        cost_records.append(
            CostEstimation(
                period_type=period_type,
                period_start=pd.to_datetime(slice_frame["timestamp"].min()).to_pydatetime(),
                period_end=pd.to_datetime(slice_frame["timestamp"].max()).to_pydatetime(),
                energy_kwh=float(slice_frame["energy_consumption_kwh"].sum()),
                estimated_cost=float(slice_frame["cost"].sum()),
                peak_cost_contribution=float(peak_cost / total_cost) if total_cost else 0,
                potential_savings=float(potential_savings),
                forecasted=False,
            )
        )
    if forecast_points:
        cost_records.append(
            CostEstimation(
                period_type="forecast",
                period_start=forecast_points[0][0],
                period_end=forecast_points[-1][0],
                energy_kwh=forecast_energy,
                estimated_cost=float(forecast_cost),
                peak_cost_contribution=float(peak_cost / total_cost) if total_cost else 0,
                potential_savings=float(potential_savings),
                forecasted=True,
            )
        )
    if cost_records:
        db.add_all(cost_records)
    db.commit()

    return CostSummary(
        current_cost=round(float(current_slice["cost"].sum()), 2),
        daily_cost=round(float(daily_slice["cost"].sum()), 2),
        weekly_cost=round(float(weekly_slice["cost"].sum()), 2),
        monthly_cost=round(float(monthly_slice["cost"].sum()), 2),
        forecast_cost=round(float(forecast_cost), 2),
        potential_savings=round(float(potential_savings), 2),
        peak_cost_contribution=round(float(peak_cost / total_cost), 4) if total_cost else 0,
        breakdown=breakdown,
    )
