from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from db.database import DATASET_DIR


DEVICE_NAMES = [
    "HVAC",
    "Lighting",
    "Compressor",
    "Server Rack",
    "Production Line",
    "Refrigeration",
    "Elevator",
    "Pumps",
]


def generate_synthetic_dataset(records: int = 50000) -> tuple[Path, Path, int]:
    rng = np.random.default_rng(42)
    timestamps = pd.date_range(start="2021-01-01", periods=records, freq="h")
    hour_values = timestamps.hour.to_numpy()
    day_of_week = timestamps.dayofweek.to_numpy()
    day_of_year = timestamps.dayofyear.to_numpy()

    base_load = np.asarray(18 + 6 * np.sin(2 * np.pi * hour_values / 24), dtype=float)
    weekly_signal = np.asarray(3 * np.where(day_of_week < 5, 1.0, 0.82), dtype=float)
    seasonal_signal = np.asarray(4 * np.sin(2 * np.pi * day_of_year / 365.25), dtype=float)
    occupancy = np.asarray(np.clip(20 + 75 * np.sin(2 * np.pi * (hour_values - 6) / 24), 0, None), dtype=float)
    occupancy *= np.where(day_of_week < 5, 1, 0.55)
    temperature = np.asarray(
        24 + 8 * np.sin(2 * np.pi * day_of_year / 365.25) + rng.normal(0, 1.5, size=records),
        dtype=float,
    )
    tariff = np.asarray(0.11 + 0.04 * ((hour_values >= 17) & (hour_values <= 22)).astype(float), dtype=float)
    voltage = np.asarray(228 + rng.normal(0, 4.5, size=records), dtype=float)
    current = np.asarray(48 + 8 * np.sin(2 * np.pi * hour_values / 24) + rng.normal(0, 3.2, size=records), dtype=float)
    power_factor = np.asarray(np.clip(0.87 + rng.normal(0, 0.03, size=records), 0.72, 0.99), dtype=float)

    energy = np.asarray(
        base_load + weekly_signal + seasonal_signal + 0.03 * occupancy + 0.08 * np.maximum(temperature - 25, 0),
        dtype=float,
    ).copy()
    energy += rng.normal(0, 1.2, size=records)

    spike_indices = rng.choice(records, size=max(records // 140, 25), replace=False)
    energy[spike_indices] *= rng.uniform(1.35, 1.8, size=len(spike_indices))

    dataset = pd.DataFrame(
        {
            "date": timestamps.date,
            "timestamp": timestamps,
            "energy_consumption_kwh": np.round(np.clip(energy, 3, None), 3),
            "voltage": np.round(voltage, 3),
            "current": np.round(np.clip(current, 5, None), 3),
            "power_factor": np.round(power_factor, 3),
            "tariff_rate": np.round(tariff + rng.normal(0, 0.005, size=records), 4),
            "temperature": np.round(temperature, 3),
            "occupancy": np.round(np.clip(occupancy + rng.normal(0, 4, size=records), 0, None), 0),
            "device_name": rng.choice(DEVICE_NAMES, size=records, p=[0.23, 0.17, 0.12, 0.08, 0.16, 0.11, 0.05, 0.08]),
        }
    )

    csv_path = DATASET_DIR / "synthetic_energy_dataset.csv"
    excel_path = DATASET_DIR / "synthetic_energy_dataset.xlsx"
    dataset.to_csv(csv_path, index=False)
    dataset.to_excel(excel_path, index=False)
    return csv_path, excel_path, len(dataset)


if __name__ == "__main__":
    generate_synthetic_dataset()
