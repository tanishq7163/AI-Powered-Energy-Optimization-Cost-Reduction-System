from __future__ import annotations

import io
from datetime import date

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session

from db.database import get_db, settings
from schemas.contracts import (
    AnalyticsSummary,
    AnomalyResponse,
    CostSummary,
    DashboardResponse,
    DatasetGenerationRequest,
    DatasetGenerationResponse,
    EnergyRecordCreate,
    EnergyRecordRead,
    EnergyRecordUpdate,
    ForecastResponse,
    RecommendationResponse,
    ReportResponse,
    SettingsResponse,
)
from services.analytics_service import get_analytics_summary
from services.anomaly_service import detect_anomalies
from services.cost_service import get_cost_summary
from services.data_service import (
    create_manual_record,
    delete_record,
    export_records,
    import_dataframe,
    ingest_upload,
    list_records,
    preprocess_existing_records,
    update_record,
)
from services.forecast_service import generate_forecast, train_models
from services.recommendation_service import generate_recommendations
from services.report_service import generate_pdf_report, list_reports
from scripts.fetch_public_dataset import fetch_public_dataset, transform_public_dataset
from scripts.generate_synthetic_dataset import generate_synthetic_dataset


router = APIRouter(prefix="/api")


@router.get("/records", response_model=list[EnergyRecordRead])
def get_records(limit: int = 500, skip: int = 0, db: Session = Depends(get_db)):
    return list_records(db, limit=limit, skip=skip)


@router.post("/records/manual", response_model=EnergyRecordRead)
def create_record(payload: EnergyRecordCreate, db: Session = Depends(get_db)):
    return create_manual_record(db, payload)


@router.put("/records/{record_id}", response_model=EnergyRecordRead)
def edit_record(record_id: int, payload: EnergyRecordUpdate, db: Session = Depends(get_db)):
    try:
        return update_record(db, record_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/records/{record_id}")
def remove_record(record_id: int, db: Session = Depends(get_db)):
    try:
        delete_record(db, record_id)
        return {"message": "Record deleted successfully."}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/records/upload")
def upload_records(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        return ingest_upload(db, file)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/records/export")
def download_records(db: Session = Depends(get_db)):
    frame = export_records(db)
    csv_stream = io.StringIO()
    frame.to_csv(csv_stream, index=False)
    return StreamingResponse(
        iter([csv_stream.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=energy_records_export.csv"},
    )


@router.get("/preprocessing")
def preview_preprocessing(db: Session = Depends(get_db)):
    return preprocess_existing_records(db)


@router.get("/analytics", response_model=AnalyticsSummary)
def analytics(
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
):
    return get_analytics_summary(db, start_date, end_date)


@router.post("/forecasts/train")
def train_forecasting_models(db: Session = Depends(get_db)):
    return {"message": "Training completed.", "metrics": [item.model_dump() for item in train_models(db)]}


@router.get("/forecasts", response_model=ForecastResponse)
def forecast(horizon: str = Query(default="24h"), db: Session = Depends(get_db)):
    try:
        return generate_forecast(db, horizon)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/anomalies/detect", response_model=AnomalyResponse)
@router.post("/anomalies/detect", response_model=AnomalyResponse)
def anomaly_detection(db: Session = Depends(get_db)):
    return detect_anomalies(db)


@router.get("/costs", response_model=CostSummary)
def costs(db: Session = Depends(get_db)):
    return get_cost_summary(db)


@router.post("/recommendations/generate", response_model=RecommendationResponse)
def recommendations(db: Session = Depends(get_db)):
    return generate_recommendations(db)


@router.post("/reports/generate", response_model=ReportResponse)
def reports(db: Session = Depends(get_db)):
    return generate_pdf_report(db)


@router.get("/reports", response_model=list[ReportResponse])
def reports_index(db: Session = Depends(get_db)):
    return list_reports(db)


@router.get("/reports/download")
def report_download(path: str):
    return FileResponse(path)


@router.get("/dashboard", response_model=DashboardResponse)
def dashboard(db: Session = Depends(get_db)):
    return DashboardResponse(
        analytics=get_analytics_summary(db),
        forecast=generate_forecast(db, "24h"),
        anomalies=detect_anomalies(db),
        costs=get_cost_summary(db),
        recommendations=generate_recommendations(db),
    )


@router.post("/datasets/generate", response_model=DatasetGenerationResponse)
def generate_dataset(payload: DatasetGenerationRequest, db: Session = Depends(get_db)):
    csv_path, excel_path, records = generate_synthetic_dataset(payload.records)
    frame = pd.read_csv(csv_path)
    import_dataframe(db, frame, replace_existing=True)
    return DatasetGenerationResponse(csv_path=str(csv_path), excel_path=str(excel_path), records=records)


@router.post("/datasets/fetch-public")
def fetch_dataset(db: Session = Depends(get_db)):
    dataset_path = fetch_public_dataset()
    frame = transform_public_dataset(dataset_path)
    import_result = import_dataframe(db, frame, replace_existing=True)
    return {
        "message": "Public dataset downloaded and imported.",
        "dataset_path": str(dataset_path),
        **import_result,
    }


@router.get("/settings", response_model=SettingsResponse)
def app_settings():
    return SettingsResponse(
        app_name=settings.app_name,
        database_url=settings.database_url,
        reports_dir=settings.reports_dir,
        dataset_dir=settings.dataset_dir,
        models_dir=settings.models_dir,
    )
