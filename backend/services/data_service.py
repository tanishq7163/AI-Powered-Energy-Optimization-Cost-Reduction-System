from __future__ import annotations

import io
from datetime import date, datetime
from pathlib import Path

import pandas as pd
from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from db.database import MODELS_DIR
from db.models import Anomaly, CostEstimation, EnergyRecord, Forecast, Recommendation
from db.models import EnergyRecord
from schemas.contracts import EnergyRecordCreate, EnergyRecordUpdate
from utils.preprocessing import DataPreprocessor


preprocessor = DataPreprocessor()

MODEL_ARTIFACT_PATHS = [
    MODELS_DIR / "forecast_metadata.json",
    MODELS_DIR / "best_forecast_model.joblib",
    MODELS_DIR / "forecast_scaler.joblib",
    MODELS_DIR / "lstm_forecast_model.keras",
]


def invalidate_derived_state(db: Session) -> None:
    for artifact_path in MODEL_ARTIFACT_PATHS:
        if artifact_path.exists():
            artifact_path.unlink()

    db.query(Forecast).delete()
    db.query(Anomaly).delete()
    db.query(Recommendation).delete()
    db.query(CostEstimation).delete()
    db.commit()


def _read_upload(upload_file: UploadFile) -> pd.DataFrame:
    file_bytes = upload_file.file.read()
    upload_file.file.seek(0)
    filename = upload_file.filename or "dataset.csv"
    if filename.lower().endswith(".csv"):
        return pd.read_csv(io.BytesIO(file_bytes))
    if filename.lower().endswith((".xls", ".xlsx")):
        return pd.read_excel(io.BytesIO(file_bytes))
    raise ValueError("Only CSV and Excel uploads are supported.")


def ingest_upload(db: Session, upload_file: UploadFile) -> dict:
    frame = _read_upload(upload_file)
    cleaned, summary = preprocessor.clean(frame)
    replace_records(db, cleaned)
    return {
        "message": "Dataset imported successfully.",
        "processing_summary": summary.__dict__,
        "imported_rows": len(cleaned),
    }


def persist_dataframe(db: Session, frame: pd.DataFrame) -> None:
    records = []
    for row in frame.to_dict(orient="records"):
        records.append(
            EnergyRecord(
                date=row["date"],
                timestamp=pd.to_datetime(row["timestamp"]).to_pydatetime(),
                energy_consumption_kwh=float(row["energy_consumption_kwh"]),
                voltage=float(row["voltage"]),
                current=float(row["current"]),
                power_factor=float(row["power_factor"]),
                tariff_rate=float(row["tariff_rate"]),
                temperature=float(row["temperature"]),
                occupancy=float(row["occupancy"]),
                device_name=str(row["device_name"]),
            )
        )
    db.add_all(records)
    db.commit()


def create_manual_record(db: Session, payload: EnergyRecordCreate) -> EnergyRecord:
    record = EnergyRecord(**payload.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    invalidate_derived_state(db)
    return record


def update_record(db: Session, record_id: int, payload: EnergyRecordUpdate) -> EnergyRecord:
    record = db.get(EnergyRecord, record_id)
    if record is None:
        raise ValueError("Record not found.")
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(record, field, value)
    db.commit()
    db.refresh(record)
    invalidate_derived_state(db)
    return record


def delete_record(db: Session, record_id: int) -> None:
    record = db.get(EnergyRecord, record_id)
    if record is None:
        raise ValueError("Record not found.")
    db.delete(record)
    db.commit()
    invalidate_derived_state(db)


def list_records(db: Session, limit: int = 500, skip: int = 0) -> list[EnergyRecord]:
    statement = select(EnergyRecord).order_by(EnergyRecord.timestamp.desc()).offset(skip).limit(limit)
    return list(db.scalars(statement))


def export_records(db: Session) -> pd.DataFrame:
    return load_records_dataframe(db)


def load_records_dataframe(
    db: Session,
    start_date: date | None = None,
    end_date: date | None = None,
) -> pd.DataFrame:
    statement = select(EnergyRecord).order_by(EnergyRecord.timestamp.asc())
    records = list(db.scalars(statement))
    if not records:
        return pd.DataFrame(columns=[
            "id",
            "date",
            "timestamp",
            "energy_consumption_kwh",
            "voltage",
            "current",
            "power_factor",
            "tariff_rate",
            "temperature",
            "occupancy",
            "device_name",
        ])

    frame = pd.DataFrame(
        [
            {
                "id": record.id,
                "date": record.date,
                "timestamp": record.timestamp,
                "energy_consumption_kwh": record.energy_consumption_kwh,
                "voltage": record.voltage,
                "current": record.current,
                "power_factor": record.power_factor,
                "tariff_rate": record.tariff_rate,
                "temperature": record.temperature,
                "occupancy": record.occupancy,
                "device_name": record.device_name,
            }
            for record in records
        ]
    )

    frame["timestamp"] = pd.to_datetime(frame["timestamp"])
    if start_date is not None:
        frame = frame[frame["timestamp"].dt.date >= start_date]
    if end_date is not None:
        frame = frame[frame["timestamp"].dt.date <= end_date]
    cleaned, _ = preprocessor.clean(frame)
    if "id" in frame.columns and len(cleaned) == len(frame):
        cleaned["id"] = frame["id"].values
    return cleaned.reset_index(drop=True)


def preprocess_existing_records(db: Session) -> dict:
    frame = load_records_dataframe(db)
    cleaned, summary = preprocessor.clean(frame)
    return {
        "processing_summary": summary.__dict__,
        "preview": cleaned.head(20).to_dict(orient="records"),
    }


def replace_records(db: Session, frame: pd.DataFrame) -> None:
    invalidate_derived_state(db)
    db.query(EnergyRecord).delete()
    db.commit()
    persist_dataframe(db, frame)


def import_dataframe(db: Session, frame: pd.DataFrame, replace_existing: bool = True) -> dict:
    cleaned, summary = preprocessor.clean(frame)
    if replace_existing:
        replace_records(db, cleaned)
    else:
        persist_dataframe(db, cleaned)
    return {
        "processing_summary": summary.__dict__,
        "imported_rows": len(cleaned),
    }
