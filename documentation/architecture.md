# System Architecture

## Overview

The platform uses a decoupled frontend and backend architecture optimized for local execution:

- Next.js frontend for dashboards, data entry, uploads, and report actions.
- FastAPI backend for ingestion, preprocessing, analytics, ML inference, anomaly detection, recommendations, and PDF generation.
- PostgreSQL as the system of record for operational data and generated outputs.
- Local filesystem storage for trained models, exported datasets, and generated PDF reports.

## Backend flow

1. Data arrives through CSV upload, Excel upload, or manual entry.
2. The preprocessing pipeline validates the required schema, imputes missing values, removes duplicates and outliers, and derives temporal features.
3. Analytics services aggregate the cleaned data into daily, weekly, monthly, yearly, and heatmap-friendly structures.
4. Forecasting services train and evaluate Linear Regression, Random Forest, XGBoost, Prophet, and LSTM models, then persist the best model metadata locally.
5. Anomaly detection combines Isolation Forest, Local Outlier Factor, and spike heuristics for severity scoring.
6. Cost estimation converts energy usage to tariff-based cost snapshots and forecast cost exposure.
7. Recommendation generation synthesizes analytics, forecast output, anomalies, and cost findings into actionable suggestions.
8. PDF generation writes local reports through ReportLab and tracks them in PostgreSQL.

## Frontend flow

- The Next.js app consumes the FastAPI endpoints directly through fetch-based API helpers.
- Recharts powers trend and cost visualizations.
- Plotly renders anomaly scatter/bubble charts.
- Shared shadcn-style UI components provide consistent cards, buttons, badges, and input controls.
- Route pages cover Home, Upload, Dashboard, Forecasting, Anomaly Detection, Costs, Recommendations, Reports, and Settings.

## Project structure

- frontend/: Next.js application
- backend/: FastAPI application, services, database models, scripts, and local model artifacts
- dataset/: generated synthetic and downloaded public datasets
- reports/: generated PDF files
- documentation/: architecture and ER diagram assets
