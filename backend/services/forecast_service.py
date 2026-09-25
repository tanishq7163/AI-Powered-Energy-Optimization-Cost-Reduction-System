from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from prophet import Prophet
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error, mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler
from sqlalchemy.orm import Session
from xgboost import XGBRegressor

try:
    from tensorflow import keras
except ModuleNotFoundError:
    keras = None

from db.database import MODELS_DIR
from db.models import Forecast
from schemas.contracts import ForecastPoint, ForecastResponse, ModelMetric
from services.data_service import load_records_dataframe


HORIZON_MAP = {"24h": 24, "7d": 24 * 7, "30d": 24 * 30}
MODEL_META_PATH = MODELS_DIR / "forecast_metadata.json"
TRADITIONAL_MODEL_PATH = MODELS_DIR / "best_forecast_model.joblib"
SCALER_PATH = MODELS_DIR / "forecast_scaler.joblib"
LSTM_MODEL_PATH = MODELS_DIR / "lstm_forecast_model.keras"
SEQUENCE_LENGTH = 24
FEATURE_COLUMNS = [
    "voltage",
    "current",
    "power_factor",
    "tariff_rate",
    "temperature",
    "occupancy",
    "hour",
    "day",
    "weekday",
    "week",
    "month",
    "quarter",
    "season_code",
    "is_weekend",
    "time_index",
]


def _metrics(model_name: str, actual: np.ndarray, predicted: np.ndarray, status: str = "trained") -> ModelMetric:
    mse = mean_squared_error(actual, predicted)
    return ModelMetric(
        model_name=model_name,
        mae=float(mean_absolute_error(actual, predicted)),
        mse=float(mse),
        rmse=float(np.sqrt(mse)),
        mape=float(mean_absolute_percentage_error(actual, predicted)),
        r2=float(r2_score(actual, predicted)),
        status=status,
    )


def _prepare_frame(db: Session) -> pd.DataFrame:
    frame = load_records_dataframe(db)
    if frame.empty:
        raise ValueError("No energy records available for forecasting.")
    frame = frame.sort_values("timestamp").reset_index(drop=True)
    frame["time_index"] = np.arange(len(frame))
    return frame


def _split(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    split_index = max(int(len(frame) * 0.8), SEQUENCE_LENGTH + 5)
    return frame.iloc[:split_index].copy(), frame.iloc[split_index:].copy()


def _train_lstm(train_values: np.ndarray, test_values: np.ndarray):
    if keras is None:
        raise RuntimeError("TensorFlow is not installed.")

    x_train, y_train = [], []
    for index in range(SEQUENCE_LENGTH, len(train_values)):
        x_train.append(train_values[index - SEQUENCE_LENGTH : index])
        y_train.append(train_values[index])

    x_test, y_test = [], []
    full_series = np.concatenate([train_values[-SEQUENCE_LENGTH:], test_values])
    for index in range(SEQUENCE_LENGTH, len(full_series)):
        x_test.append(full_series[index - SEQUENCE_LENGTH : index])
        y_test.append(full_series[index])

    x_train = np.array(x_train).reshape((-1, SEQUENCE_LENGTH, 1))
    x_test = np.array(x_test).reshape((-1, SEQUENCE_LENGTH, 1))

    model = keras.Sequential(
        [
            keras.layers.Input(shape=(SEQUENCE_LENGTH, 1)),
            keras.layers.LSTM(32, activation="tanh"),
            keras.layers.Dense(16, activation="relu"),
            keras.layers.Dense(1),
        ]
    )
    model.compile(optimizer="adam", loss="mse")
    model.fit(x_train, np.array(y_train), epochs=8, batch_size=32, verbose=0)
    predictions = model.predict(x_test, verbose=0).flatten()
    return model, predictions[-len(test_values) :]


def train_models(db: Session) -> list[ModelMetric]:
    frame = _prepare_frame(db)
    if len(frame) < max(SEQUENCE_LENGTH + 10, 48):
        return _persist_naive_model(frame)

    train_frame, test_frame = _split(frame)

    x_train = train_frame[FEATURE_COLUMNS]
    x_test = test_frame[FEATURE_COLUMNS]
    y_train = train_frame["energy_consumption_kwh"]
    y_test = test_frame["energy_consumption_kwh"]

    evaluations: list[ModelMetric] = []
    models: dict[str, object] = {}

    linear_model = LinearRegression()
    linear_model.fit(x_train, y_train)
    linear_predictions = linear_model.predict(x_test)
    evaluations.append(_metrics("Linear Regression", y_test.to_numpy(), linear_predictions))
    models["Linear Regression"] = linear_model

    random_forest = RandomForestRegressor(n_estimators=150, random_state=42)
    random_forest.fit(x_train, y_train)
    rf_predictions = random_forest.predict(x_test)
    evaluations.append(_metrics("Random Forest", y_test.to_numpy(), rf_predictions))
    models["Random Forest"] = random_forest

    xgb_model = XGBRegressor(
        n_estimators=300,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.9,
        colsample_bytree=0.9,
        objective="reg:squarederror",
        random_state=42,
    )
    xgb_model.fit(x_train, y_train)
    xgb_predictions = xgb_model.predict(x_test)
    evaluations.append(_metrics("XGBoost", y_test.to_numpy(), xgb_predictions))
    models["XGBoost"] = xgb_model

    try:
        prophet_train = train_frame[["timestamp", "energy_consumption_kwh"]].rename(
            columns={"timestamp": "ds", "energy_consumption_kwh": "y"}
        )
        prophet_model = Prophet(daily_seasonality=True, weekly_seasonality=True, yearly_seasonality=True)
        prophet_model.fit(prophet_train)
        prophet_future = prophet_model.make_future_dataframe(periods=len(test_frame), freq="h", include_history=False)
        prophet_forecast = prophet_model.predict(prophet_future)
        prophet_predictions = prophet_forecast["yhat"].to_numpy()
        evaluations.append(_metrics("Prophet", y_test.to_numpy(), prophet_predictions))
        models["Prophet"] = prophet_model
    except Exception:
        evaluations.append(
            ModelMetric(
                model_name="Prophet",
                mae=0.0,
                mse=0.0,
                rmse=0.0,
                mape=0.0,
                r2=0.0,
                status="skipped",
            )
        )

    scaler = StandardScaler()
    scaled_series = scaler.fit_transform(frame[["energy_consumption_kwh"]]).flatten()
    if keras is not None and len(test_frame) > 0:
        train_values = scaled_series[: len(train_frame)]
        test_values = scaled_series[len(train_frame) :]
        lstm_model, lstm_predictions_scaled = _train_lstm(train_values, test_values)
        lstm_predictions = scaler.inverse_transform(lstm_predictions_scaled.reshape(-1, 1)).flatten()
        evaluations.append(_metrics("LSTM", y_test.to_numpy(), lstm_predictions))
        models["LSTM"] = lstm_model
    else:
        evaluations.append(
            ModelMetric(
                model_name="LSTM",
                mae=0.0,
                mse=0.0,
                rmse=0.0,
                mape=0.0,
                r2=0.0,
                status="skipped",
            )
        )

    trained_metrics = [metric for metric in evaluations if metric.model_name in models]
    if not trained_metrics:
        return _persist_naive_model(frame)

    best_metric = min(trained_metrics, key=lambda metric: metric.rmse)
    best_model = models[best_metric.model_name]

    if best_metric.model_name == "LSTM" and keras is not None:
        best_model.save(LSTM_MODEL_PATH)
    elif best_metric.model_name == "Prophet":
        joblib.dump(best_model, TRADITIONAL_MODEL_PATH)
    else:
        joblib.dump(best_model, TRADITIONAL_MODEL_PATH)

    joblib.dump(scaler, SCALER_PATH)

    MODEL_META_PATH.write_text(
        json.dumps(
            {
                "best_model": best_metric.model_name,
                "metrics": [metric.model_dump() for metric in evaluations],
                "residual_std": float(best_metric.rmse),
                "train_rows": len(train_frame),
                "total_rows": len(frame),
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    return evaluations


def _persist_naive_model(frame: pd.DataFrame) -> list[ModelMetric]:
    recent_mean = float(frame["energy_consumption_kwh"].tail(min(len(frame), 24)).mean())
    residual_std = float(frame["energy_consumption_kwh"].std(ddof=0) or 0.15)
    metrics = [
        ModelMetric(
            model_name="Naive Baseline",
            mae=0.0,
            mse=0.0,
            rmse=0.0,
            mape=0.0,
            r2=0.0,
            status="baseline",
        )
    ]
    MODEL_META_PATH.write_text(
        json.dumps(
            {
                "best_model": "Naive Baseline",
                "metrics": [metric.model_dump() for metric in metrics],
                "residual_std": residual_std,
                "baseline_value": recent_mean,
                "train_rows": len(frame),
                "total_rows": len(frame),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return metrics


def _future_frame(frame: pd.DataFrame, periods: int) -> pd.DataFrame:
    last_timestamp = frame["timestamp"].max()
    inferred_step = frame["timestamp"].diff().median()
    if pd.isna(inferred_step) or inferred_step <= pd.Timedelta(0):
        inferred_step = pd.Timedelta(hours=1)

    future_timestamps = [last_timestamp + inferred_step * (index + 1) for index in range(periods)]
    medians = {column: float(frame[column].median()) for column in [
        "voltage",
        "current",
        "power_factor",
        "tariff_rate",
        "temperature",
        "occupancy",
    ]}
    future_frame = pd.DataFrame({"timestamp": future_timestamps, **medians})
    future_frame["date"] = future_frame["timestamp"].dt.date
    future_frame["hour"] = future_frame["timestamp"].dt.hour
    future_frame["day"] = future_frame["timestamp"].dt.day
    future_frame["weekday"] = future_frame["timestamp"].dt.weekday
    future_frame["week"] = future_frame["timestamp"].dt.isocalendar().week.astype(int)
    future_frame["month"] = future_frame["timestamp"].dt.month
    future_frame["quarter"] = future_frame["timestamp"].dt.quarter
    future_frame["season_code"] = future_frame["month"].map({12: 0, 1: 0, 2: 0, 3: 1, 4: 1, 5: 1, 6: 2, 7: 2, 8: 2, 9: 3, 10: 3, 11: 3})
    future_frame["is_weekend"] = future_frame["weekday"].isin([5, 6]).astype(int)
    future_frame["time_index"] = np.arange(len(frame), len(frame) + periods)
    return future_frame


def generate_forecast(db: Session, horizon: str = "24h") -> ForecastResponse:
    if horizon not in HORIZON_MAP:
        raise ValueError("Unsupported horizon. Use 24h, 7d, or 30d.")
    if not MODEL_META_PATH.exists():
        train_models(db)

    metadata = json.loads(MODEL_META_PATH.read_text(encoding="utf-8"))
    frame = _prepare_frame(db)
    periods = HORIZON_MAP[horizon]
    residual_std = float(metadata.get("residual_std", 0.15))
    future_frame = _future_frame(frame, periods)
    best_model_name = metadata["best_model"]

    if best_model_name == "Naive Baseline":
        baseline_value = float(metadata.get("baseline_value", frame["energy_consumption_kwh"].mean()))
        predictions = [baseline_value] * periods
    elif best_model_name == "LSTM":
        if keras is None:
            raise ValueError("Saved forecast model requires TensorFlow, but TensorFlow is not installed.")
        scaler: StandardScaler = joblib.load(SCALER_PATH)
        lstm_model = keras.models.load_model(LSTM_MODEL_PATH)
        history = scaler.transform(frame[["energy_consumption_kwh"]]).flatten().tolist()
        predictions = []
        for _ in range(periods):
            window = np.array(history[-SEQUENCE_LENGTH:]).reshape((1, SEQUENCE_LENGTH, 1))
            next_scaled = float(lstm_model.predict(window, verbose=0).flatten()[0])
            history.append(next_scaled)
            next_value = float(scaler.inverse_transform(np.array([[next_scaled]])).flatten()[0])
            predictions.append(next_value)
    elif best_model_name == "Prophet":
        prophet_model: Prophet = joblib.load(TRADITIONAL_MODEL_PATH)
        future = future_frame[["timestamp"]].rename(columns={"timestamp": "ds"})
        predictions = prophet_model.predict(future)["yhat"].to_list()
    else:
        model = joblib.load(TRADITIONAL_MODEL_PATH)
        predictions = model.predict(future_frame[FEATURE_COLUMNS]).tolist()

    forecast_points = []
    db.query(Forecast).filter(Forecast.horizon == horizon).delete()
    db.commit()

    for timestamp, prediction in zip(future_frame["timestamp"], predictions, strict=True):
        lower_bound = max(float(prediction) - residual_std * 1.96, 0)
        upper_bound = float(prediction) + residual_std * 1.96
        forecast_points.append(
            ForecastPoint(
                timestamp=pd.to_datetime(timestamp).to_pydatetime(),
                predicted_consumption_kwh=round(float(prediction), 3),
                lower_bound=round(lower_bound, 3),
                upper_bound=round(upper_bound, 3),
            )
        )
        db.add(
            Forecast(
                model_name=best_model_name,
                horizon=horizon,
                forecast_time=pd.to_datetime(timestamp).to_pydatetime(),
                predicted_consumption_kwh=float(prediction),
                lower_bound=lower_bound,
                upper_bound=upper_bound,
            )
        )
    db.commit()

    return ForecastResponse(
        best_model=best_model_name,
        selected_horizon=horizon,
        metrics=[ModelMetric(**metric) for metric in metadata["metrics"]],
        forecast=forecast_points,
    )
