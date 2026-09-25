from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.preprocessing import MinMaxScaler
from sqlalchemy.orm import Session

from db.models import Anomaly
from schemas.contracts import AnomalyItem, AnomalyResponse
from services.data_service import load_records_dataframe


def detect_anomalies(db: Session) -> AnomalyResponse:
    frame = load_records_dataframe(db)
    if frame.empty or len(frame) < 30:
        return AnomalyResponse(count=0, anomalies=[], severity_breakdown=[])

    feature_columns = [
        "energy_consumption_kwh",
        "voltage",
        "current",
        "power_factor",
        "temperature",
        "occupancy",
        "hour",
        "is_weekend",
    ]
    feature_frame = frame[feature_columns].copy()

    isolation_forest = IsolationForest(contamination=0.03, random_state=42)
    iso_flags = isolation_forest.fit_predict(feature_frame)
    iso_scores = -isolation_forest.score_samples(feature_frame)

    neighbor_count = min(max(5, len(frame) // 30), len(frame) - 1)
    lof = LocalOutlierFactor(n_neighbors=neighbor_count, contamination=0.03)
    lof_flags = lof.fit_predict(feature_frame)
    lof_scores = -lof.negative_outlier_factor_

    spike_score = np.abs(frame["energy_consumption_kwh"].pct_change().fillna(0))
    scaler = MinMaxScaler()
    combined_score = scaler.fit_transform(
        np.column_stack([iso_scores, lof_scores, spike_score.to_numpy()])
    ).mean(axis=1)

    anomaly_mask = (iso_flags == -1) | (lof_flags == -1) | (spike_score > 0.45)
    anomalies_frame = frame[anomaly_mask].copy()
    anomalies_frame["combined_score"] = combined_score[anomaly_mask]

    if anomalies_frame.empty:
        return AnomalyResponse(count=0, anomalies=[], severity_breakdown=[])

    q50 = anomalies_frame["combined_score"].quantile(0.5)
    q75 = anomalies_frame["combined_score"].quantile(0.75)
    q90 = anomalies_frame["combined_score"].quantile(0.9)

    def severity(score: float) -> str:
        if score >= q90:
            return "Critical"
        if score >= q75:
            return "High"
        if score >= q50:
            return "Medium"
        return "Low"

    db.query(Anomaly).delete()
    db.commit()

    items: list[AnomalyItem] = []
    for _, row in anomalies_frame.sort_values("combined_score", ascending=False).head(150).iterrows():
        severity_level = severity(float(row["combined_score"]))
        description = (
            f"{row['device_name']} consumed {row['energy_consumption_kwh']:.2f} kWh at "
            f"{pd.to_datetime(row['timestamp']).strftime('%Y-%m-%d %H:%M')} which deviates from the learned profile."
        )
        db.add(
            Anomaly(
                record_id=int(row["id"]) if "id" in row and not pd.isna(row["id"]) else None,
                timestamp=pd.to_datetime(row["timestamp"]).to_pydatetime(),
                method="Isolation Forest + LOF",
                anomaly_score=float(row["combined_score"]),
                severity_level=severity_level,
                description=description,
            )
        )
        items.append(
            AnomalyItem(
                timestamp=pd.to_datetime(row["timestamp"]).to_pydatetime(),
                device_name=str(row["device_name"]),
                energy_consumption_kwh=round(float(row["energy_consumption_kwh"]), 3),
                anomaly_score=round(float(row["combined_score"]), 4),
                severity_level=severity_level,
                description=description,
                method="Isolation Forest + LOF",
            )
        )
    db.commit()

    severity_breakdown = (
        pd.DataFrame([item.model_dump() for item in items])["severity_level"]
        .value_counts()
        .rename_axis("severity")
        .reset_index(name="count")
        .to_dict(orient="records")
    )

    return AnomalyResponse(count=len(items), anomalies=items, severity_breakdown=severity_breakdown)
