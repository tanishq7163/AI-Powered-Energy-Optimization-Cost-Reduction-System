from __future__ import annotations

import urllib.request
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

from db.database import DATASET_DIR


PUBLIC_DATASET_URL = "https://archive.ics.uci.edu/ml/machine-learning-databases/00235/household_power_consumption.zip"


def fetch_public_dataset() -> Path:
    target_dir = DATASET_DIR / "public_dataset"
    target_dir.mkdir(parents=True, exist_ok=True)
    zip_path = target_dir / "household_power_consumption.zip"
    urllib.request.urlretrieve(PUBLIC_DATASET_URL, zip_path)
    with zipfile.ZipFile(zip_path, "r") as archive:
        archive.extractall(target_dir)
    return target_dir


def transform_public_dataset(dataset_dir: Path) -> pd.DataFrame:
    source_file = dataset_dir / "household_power_consumption.txt"
    if not source_file.exists():
        raise FileNotFoundError("Public dataset file was not found after extraction.")

    frame = pd.read_csv(source_file, sep=";", low_memory=False)
    frame = frame.replace("?", np.nan)
    frame["timestamp"] = pd.to_datetime(
        frame["Date"].astype(str) + " " + frame["Time"].astype(str),
        format="%d/%m/%Y %H:%M:%S",
        errors="coerce",
    )
    frame = frame.dropna(subset=["timestamp"]).copy()

    numeric_columns = [
        "Global_active_power",
        "Voltage",
        "Global_intensity",
        "Sub_metering_1",
        "Sub_metering_2",
        "Sub_metering_3",
    ]
    for column in numeric_columns:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")

    frame["energy_consumption_kwh"] = frame["Global_active_power"].fillna(frame["Global_intensity"] * 0.230)
    frame["voltage"] = frame["Voltage"].fillna(frame["Voltage"].median())
    frame["current"] = frame["Global_intensity"].fillna(frame["Global_intensity"].median())
    apparent_power = (frame["voltage"] * frame["current"]) / 1000
    frame["power_factor"] = np.where(
        apparent_power > 0,
        frame["energy_consumption_kwh"] / apparent_power,
        0.92,
    )
    frame["power_factor"] = frame["power_factor"].clip(lower=0.5, upper=1.0).fillna(0.92)
    frame["tariff_rate"] = np.where(frame["timestamp"].dt.hour.between(17, 22), 0.15, 0.11)
    frame["temperature"] = 22 + 8 * np.sin(2 * np.pi * frame["timestamp"].dt.dayofyear / 365.25)
    frame["occupancy"] = np.where(frame["timestamp"].dt.hour.between(8, 18), 42, 12)
    frame["device_name"] = "Whole Building"
    frame["date"] = frame["timestamp"].dt.date

    standardized = frame[
        [
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
    ].copy()
    standardized = standardized.dropna(subset=["energy_consumption_kwh", "voltage", "current"])
    return standardized.reset_index(drop=True)


if __name__ == "__main__":
    print(fetch_public_dataset())
