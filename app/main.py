"""Bogotá Road Safety API — query and analyze road incidents."""

import os
from functools import lru_cache
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query

from app.repository import Filters, IncidentRepository
from app.schemas import GroupBy, GroupCount, Incident, IncidentPage, Severity, Summary, VehicleType

DATA_PATH = Path(os.getenv("DATA_PATH", Path(__file__).resolve().parent.parent / "data" / "incidents.csv"))

app = FastAPI(
    title="Bogotá Road Safety API",
    description="REST API to explore and analyze road incidents in Bogotá by locality, time and severity.",
    version="1.0.0",
)


@lru_cache
def get_repository() -> IncidentRepository:
    return IncidentRepository.from_csv(DATA_PATH)


Repo = Annotated[IncidentRepository, Depends(get_repository)]


def get_filters(
    locality: str | None = None,
    severity: Severity | None = None,
    vehicle_type: VehicleType | None = None,
    year: Annotated[int | None, Query(ge=2000, le=2100)] = None,
) -> Filters:
    return Filters(
        locality=locality,
        severity=severity.value if severity else None,
        vehicle_type=vehicle_type.value if vehicle_type else None,
        year=year,
    )


FilterDep = Annotated[Filters, Depends(get_filters)]


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok"}


@app.get("/localities", response_model=list[str], tags=["meta"])
def list_localities(repo: Repo):
    return repo.localities()


@app.get("/incidents", response_model=IncidentPage, tags=["incidents"])
def list_incidents(
    repo: Repo,
    filters: FilterDep,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    total, items = repo.search(filters, limit, offset)
    return {"total": total, "limit": limit, "offset": offset, "items": items}


@app.get("/incidents/{incident_id}", response_model=Incident, tags=["incidents"])
def get_incident(incident_id: int, repo: Repo):
    incident = repo.get(incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@app.get("/stats/summary", response_model=Summary, tags=["stats"])
def summary(repo: Repo, filters: FilterDep):
    return repo.summary(filters)


@app.get("/stats/group", response_model=list[GroupCount], tags=["stats"])
def group(repo: Repo, filters: FilterDep, by: GroupBy = GroupBy.locality):
    """Count incidents grouped by a dimension (locality, severity, vehicle_type, hour, weekday, month)."""
    return repo.group_count(filters, by.value)
