"""Generates a synthetic dataset of road incidents in Bogotá.

The data is randomly generated (it is NOT official data) but follows realistic
patterns: more incidents at rush hours, on weekdays and in larger localities.
Replace data/incidents.csv with an open dataset (e.g. from datosabiertos.bogota.gov.co)
using the same columns to run the API on real data.

Usage:
    python scripts/generate_sample_data.py --rows 5000 --seed 42
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

LOCALITIES = {
    # locality: relative weight
    "Kennedy": 14, "Suba": 13, "Engativá": 12, "Bosa": 8, "Fontibón": 7,
    "Usaquén": 7, "Puente Aranda": 7, "Chapinero": 6, "Ciudad Bolívar": 6,
    "Teusaquillo": 5, "Barrios Unidos": 4, "Los Mártires": 4, "Santa Fe": 3,
    "Rafael Uribe Uribe": 3, "San Cristóbal": 3, "Tunjuelito": 2,
    "Antonio Nariño": 2, "La Candelaria": 1, "Usme": 2,
}
SEVERITIES = {"property_damage": 0.70, "injured": 0.27, "fatal": 0.03}
VEHICLES = {"car": 0.38, "motorcycle": 0.30, "bus": 0.10, "truck": 0.08, "bicycle": 0.08, "pedestrian": 0.06}
# Relative incident weight by hour of the day (peaks at 6-8 and 17-19)
HOUR_WEIGHTS = np.array([2, 1, 1, 1, 2, 4, 8, 9, 7, 5, 5, 5, 6, 6, 5, 5, 6, 8, 9, 7, 5, 4, 3, 2], dtype=float)


def _pick(rng, options: dict, size: int):
    keys = list(options)
    weights = np.array(list(options.values()), dtype=float)
    return rng.choice(keys, size=size, p=weights / weights.sum())


def generate(rows: int, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    days = pd.date_range("2023-01-01", "2025-12-31", freq="D")
    day_weights = np.where(days.dayofweek < 5, 1.0, 0.7)  # fewer incidents on weekends
    dates = rng.choice(days, size=rows, p=day_weights / day_weights.sum())
    hours = rng.choice(24, size=rows, p=HOUR_WEIGHTS / HOUR_WEIGHTS.sum())
    minutes = rng.integers(0, 60, size=rows)
    timestamps = pd.to_datetime(dates) + pd.to_timedelta(hours, unit="h") + pd.to_timedelta(minutes, unit="m")

    df = pd.DataFrame({
        "timestamp": timestamps,
        "locality": _pick(rng, LOCALITIES, rows),
        "severity": _pick(rng, SEVERITIES, rows),
        "vehicle_type": _pick(rng, VEHICLES, rows),
    })
    df = df.sort_values("timestamp").reset_index(drop=True)
    df.insert(0, "id", np.arange(1, rows + 1))
    return df


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--rows", type=int, default=5000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out", type=Path, default=Path(__file__).resolve().parent.parent / "data" / "incidents.csv")
    args = parser.parse_args()

    args.out.parent.mkdir(parents=True, exist_ok=True)
    generate(args.rows, args.seed).to_csv(args.out, index=False)
    print(f"Wrote {args.rows} rows to {args.out}")


if __name__ == "__main__":
    main()
