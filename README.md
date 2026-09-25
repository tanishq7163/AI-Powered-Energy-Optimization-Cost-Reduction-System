# AI-Powered Energy Consumption Optimization & Cost Reduction System

An end-to-end local analytics platform for energy data ingestion, preprocessing, forecasting, anomaly detection, cost estimation, optimization recommendations, and PDF reporting.

## Architecture

- Frontend: Next.js, TypeScript, Tailwind CSS, Recharts, Plotly, shadcn-style components
- Backend: FastAPI, SQLAlchemy, ReportLab
- Database: PostgreSQL
- ML and analytics: Pandas, NumPy, Scikit-learn, XGBoost, Prophet, TensorFlow/Keras

See documentation/architecture.md and documentation/er-diagram.md for the detailed architecture and schema view.

## Folder structure

```text
frontend/
backend/
  api/
  db/
  ml/
  models/
  schemas/
  scripts/
  services/
  utils/
  migrations/
dataset/
reports/
documentation/
```

## Features

- CSV, Excel, and manual data ingestion
- Data cleaning with missing value handling, duplicate removal, outlier filtering, scaling, normalization, and time-based feature engineering
- Daily, weekly, monthly, and yearly analytics
- Forecasting with Linear Regression, Random Forest, XGBoost, Prophet, and LSTM
- Automatic best-model selection using MAE, MSE, RMSE, MAPE, and R²
- Anomaly detection using Isolation Forest and Local Outlier Factor
- Tariff-based cost estimation and forecast cost projection
- Dynamic optimization recommendations
- PDF report generation and export
- Synthetic dataset generation for 50,000 sample records
- Public dataset download integration

## PostgreSQL setup

1. Create a PostgreSQL database named energy_optimization.
2. Update backend/.env from backend/.env.example if your local credentials differ.
3. Run backend/schema.sql against PostgreSQL, or let SQLAlchemy create the tables on first backend startup.

## Backend setup

```bash
cd backend
pip install -r requirements.txt
copy .env.example .env
python scripts/generate_synthetic_dataset.py
uvicorn main:app --reload
```

Backend base URL: http://127.0.0.1:8000

Useful API endpoints:

- GET /health
- POST /api/records/upload
- POST /api/records/manual
- GET /api/analytics
- GET /api/forecasts?horizon=24h
- POST /api/anomalies/detect
- GET /api/costs
- POST /api/recommendations/generate
- POST /api/reports/generate

## Frontend setup

```bash
cd frontend
npm install
npm run dev
```

Frontend URL: http://localhost:3000

If the backend runs on a different host or port, define NEXT_PUBLIC_API_BASE_URL before starting the frontend.

## Synthetic dataset

Generate the requested 50,000-row sample dataset with:

```bash
cd backend
python scripts/generate_synthetic_dataset.py
```

Generated files:

- dataset/synthetic_energy_dataset.csv
- dataset/synthetic_energy_dataset.xlsx

## Public dataset integration

Download the public energy dataset with:

```bash
cd backend
python scripts/fetch_public_dataset.py
```

This fetches the UCI Individual Household Electric Power Consumption archive into dataset/public_dataset/.

## Reports

Generated PDF files are written to reports/ and indexed in the generated_reports table.

## Validation performed

- Backend syntax validation with python -m compileall
- Frontend lint validation with npm run lint

## Notes

- Prophet and TensorFlow are included because they are part of the requested forecasting stack. Initial installation can take time on a fresh machine.
- The application intentionally excludes authentication, JWT, RBAC, CI/CD, Docker, Kubernetes, Redis, monitoring, and email verification.
