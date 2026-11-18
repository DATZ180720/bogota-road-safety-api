from enum import Enum

from pydantic import BaseModel


class Severity(str, Enum):
    property_damage = "property_damage"
    injured = "injured"
    fatal = "fatal"


class VehicleType(str, Enum):
    car = "car"
    motorcycle = "motorcycle"
    bus = "bus"
    truck = "truck"
    bicycle = "bicycle"
    pedestrian = "pedestrian"


class GroupBy(str, Enum):
    locality = "locality"
    severity = "severity"
    vehicle_type = "vehicle_type"
    hour = "hour"
    weekday = "weekday"
    month = "month"


class Incident(BaseModel):
    id: int
    timestamp: str
    locality: str
    severity: Severity
    vehicle_type: VehicleType


class IncidentPage(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[Incident]


class Summary(BaseModel):
    total: int
    by_severity: dict[str, int]
    fatality_rate_pct: float
    busiest_hour: int | None
    date_range: dict[str, str | None]


class GroupCount(BaseModel):
    key: str | int
    count: int
