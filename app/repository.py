"""Data access and analytics over the incidents dataset (pandas)."""

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

REQUIRED_COLUMNS = {"id", "timestamp", "locality", "severity", "vehicle_type"}


@dataclass
class Filters:
    locality: str | None = None
    severity: str | None = None
    vehicle_type: str | None = None
    year: int | None = None


class IncidentRepository:
    def __init__(self, df: pd.DataFrame):
        missing = REQUIRED_COLUMNS - set(df.columns)
        if missing:
            raise ValueError(f"Dataset is missing columns: {sorted(missing)}")
        self.df = df.copy()
        self.df["timestamp"] = pd.to_datetime(self.df["timestamp"])

    @classmethod
    def from_csv(cls, path: Path) -> "IncidentRepository":
        return cls(pd.read_csv(path))

    def _filtered(self, f: Filters) -> pd.DataFrame:
        df = self.df
        if f.locality:
            df = df[df["locality"].str.casefold() == f.locality.casefold()]
        if f.severity:
            df = df[df["severity"] == f.severity]
        if f.vehicle_type:
            df = df[df["vehicle_type"] == f.vehicle_type]
        if f.year:
            df = df[df["timestamp"].dt.year == f.year]
        return df

    def search(self, f: Filters, limit: int, offset: int) -> tuple[int, list[dict]]:
        df = self._filtered(f).sort_values("timestamp", ascending=False)
        page = df.iloc[offset : offset + limit].copy()
        page["timestamp"] = page["timestamp"].dt.strftime("%Y-%m-%dT%H:%M")
        return len(df), page.to_dict(orient="records")

    def get(self, incident_id: int) -> dict | None:
        match = self.df[self.df["id"] == incident_id]
        if match.empty:
            return None
        row = match.iloc[0].to_dict()
        row["timestamp"] = row["timestamp"].strftime("%Y-%m-%dT%H:%M")
        return row

    def localities(self) -> list[str]:
        return sorted(self.df["locality"].unique().tolist())

    def summary(self, f: Filters) -> dict:
        df = self._filtered(f)
        total = len(df)
        by_severity = df["severity"].value_counts().to_dict()
        busiest_hour = int(df["timestamp"].dt.hour.mode().iloc[0]) if total else None
        return {
            "total": total,
            "by_severity": by_severity,
            "fatality_rate_pct": round(by_severity.get("fatal", 0) / total * 100, 2) if total else 0.0,
            "busiest_hour": busiest_hour,
            "date_range": {
                "from": df["timestamp"].min().strftime("%Y-%m-%d") if total else None,
                "to": df["timestamp"].max().strftime("%Y-%m-%d") if total else None,
            },
        }

    def group_count(self, f: Filters, by: str) -> list[dict]:
        df = self._filtered(f)
        if by == "hour":
            keys = df["timestamp"].dt.hour
            counts = keys.value_counts().reindex(range(24), fill_value=0).sort_index()
        elif by == "weekday":
            order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            counts = df["timestamp"].dt.day_name().value_counts().reindex(order, fill_value=0)
        elif by == "month":
            counts = df["timestamp"].dt.to_period("M").astype(str).value_counts().sort_index()
        else:  # locality, severity, vehicle_type
            counts = df[by].value_counts()
        return [{"key": k if isinstance(k, str) else int(k), "count": int(v)} for k, v in counts.items()]
