from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler, StandardScaler


REQUIRED_COLUMNS = [
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
]

NUMERIC_COLUMNS = [
    "energy_consumption_kwh",
    "voltage",
    "current",
    "power_factor",
    "tariff_rate",
    "temperature",
    "occupancy",
]


@dataclass
class ProcessingSummary:
    initial_rows: int
    final_rows: int
    removed_duplicates: int
    removed_outliers: int


class DataPreprocessor:
    def validate_columns(self, frame: pd.DataFrame) -> None:
        missing_columns = [column for column in REQUIRED_COLUMNS if column not in frame.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")

    def clean(self, frame: pd.DataFrame) -> tuple[pd.DataFrame, ProcessingSummary]:
        prepared = frame.copy()
        prepared.columns = [column.strip().lower() for column in prepared.columns]
        self.validate_columns(prepared)

        initial_rows = len(prepared)

        prepared["timestamp"] = pd.to_datetime(prepared["timestamp"], errors="coerce")
        prepared["date"] = pd.to_datetime(prepared["date"], errors="coerce")
        prepared.loc[prepared["date"].isna(), "date"] = prepared.loc[prepared["date"].isna(), "timestamp"]
        prepared.loc[prepared["timestamp"].isna(), "timestamp"] = prepared.loc[prepared["timestamp"].isna(), "date"]
        prepared["date"] = prepared["date"].dt.date

        for column in NUMERIC_COLUMNS:
            prepared[column] = pd.to_numeric(prepared[column], errors="coerce")

        for column in NUMERIC_COLUMNS:
            median_value = float(prepared[column].median()) if not prepared[column].dropna().empty else 0.0
            prepared[column] = prepared[column].fillna(median_value)

        prepared["device_name"] = prepared["device_name"].fillna("Unknown").astype(str)
        prepared = prepared.dropna(subset=["timestamp", "date", "energy_consumption_kwh"])

        before_duplicates = len(prepared)
        prepared = prepared.drop_duplicates(subset=["timestamp", "device_name"]).sort_values("timestamp")
        removed_duplicates = before_duplicates - len(prepared)

        q1 = prepared["energy_consumption_kwh"].quantile(0.25)
        q3 = prepared["energy_consumption_kwh"].quantile(0.75)
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        without_outliers = prepared[
            prepared["energy_consumption_kwh"].between(lower_bound, upper_bound)
        ].copy()
        removed_outliers = len(prepared) - len(without_outliers)
        prepared = without_outliers.reset_index(drop=True)

        prepared["hour"] = prepared["timestamp"].dt.hour
        prepared["day"] = prepared["timestamp"].dt.day
        prepared["weekday"] = prepared["timestamp"].dt.weekday
        prepared["week"] = prepared["timestamp"].dt.isocalendar().week.astype(int)
        prepared["month"] = prepared["timestamp"].dt.month
        prepared["quarter"] = prepared["timestamp"].dt.quarter
        prepared["season"] = prepared["month"].map(
            {
                12: "winter",
                1: "winter",
                2: "winter",
                3: "spring",
                4: "spring",
                5: "spring",
                6: "summer",
                7: "summer",
                8: "summer",
                9: "autumn",
                10: "autumn",
                11: "autumn",
            }
        )
        prepared["season_code"] = prepared["season"].map(
            {"winter": 0, "spring": 1, "summer": 2, "autumn": 3}
        )
        prepared["is_weekend"] = prepared["weekday"].isin([5, 6]).astype(int)

        standard_scaler = StandardScaler()
        minmax_scaler = MinMaxScaler()

        standardized = standard_scaler.fit_transform(prepared[NUMERIC_COLUMNS])
        normalized = minmax_scaler.fit_transform(prepared[NUMERIC_COLUMNS])

        for index, column in enumerate(NUMERIC_COLUMNS):
            prepared[f"{column}_scaled"] = standardized[:, index]
            prepared[f"{column}_normalized"] = normalized[:, index]

        prepared.replace([np.inf, -np.inf], np.nan, inplace=True)
        prepared.fillna(0, inplace=True)

        summary = ProcessingSummary(
            initial_rows=initial_rows,
            final_rows=len(prepared),
            removed_duplicates=removed_duplicates,
            removed_outliers=removed_outliers,
        )
        return prepared, summary
