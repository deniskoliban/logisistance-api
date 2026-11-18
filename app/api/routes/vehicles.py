"""Vehicle profiles owned by the current user."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.vehicle_catalog import load_catalog
from app.db.session import get_db
from app.models.user import User
from app.models.vehicle import Vehicle
from app.schemas.vehicle import VehicleCreate, VehicleList, VehicleRead, VehicleUpdate

router = APIRouter(prefix="/vehicles", tags=["vehicles"])

_NOT_FOUND = HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")


def _get_owned_vehicle(vehicle_id: int, owner: User, db: Session) -> Vehicle:
    vehicle = db.get(Vehicle, vehicle_id)
    # A vehicle belonging to somebody else is reported as missing, not forbidden.
    if vehicle is None or vehicle.owner_id != owner.id:
        raise _NOT_FOUND
    return vehicle


def _conflict_detail(error: IntegrityError, plate: str, vin: str | None) -> str:
    """Name the field that actually collided instead of blaming the plate every time."""
    message = str(error.orig)
    if "vin" in message.lower() and vin:
        return f"A vehicle with VIN {vin} already exists in your fleet"
    return f"A vehicle with plate {plate} already exists in your fleet"


def _commit_or_conflict(db: Session, plate: str, vin: str | None) -> None:
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=_conflict_detail(error, plate, vin),
        ) from None


def _require_catalog_entry(make: str, model: str) -> None:
    """A PATCH can move a vehicle to another make/model: check the pair again."""
    catalog = load_catalog()
    if catalog.make(make) is None or not catalog.has_model(make, model):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Unknown vehicle {make!r} {model!r}: pick a make and model from the catalogue",
        )


@router.get("", response_model=VehicleList)
def list_vehicles(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> VehicleList:
    vehicles = db.scalars(
        select(Vehicle).where(Vehicle.owner_id == current_user.id).order_by(Vehicle.id)
    ).all()
    total = db.scalar(
        select(func.count()).select_from(Vehicle).where(Vehicle.owner_id == current_user.id)
    )
    return VehicleList(items=[VehicleRead.model_validate(v) for v in vehicles], total=total or 0)


@router.post("", response_model=VehicleRead, status_code=status.HTTP_201_CREATED)
def create_vehicle(
    payload: VehicleCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Vehicle:
    data = payload.model_dump()
    vehicle = Vehicle(owner_id=current_user.id, **data)
    db.add(vehicle)
    _commit_or_conflict(db, payload.plate, payload.vin)
    db.refresh(vehicle)
    return vehicle


@router.get("/{vehicle_id}", response_model=VehicleRead)
def read_vehicle(
    vehicle_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Vehicle:
    return _get_owned_vehicle(vehicle_id, current_user, db)


@router.patch("/{vehicle_id}", response_model=VehicleRead)
def update_vehicle(
    vehicle_id: int,
    payload: VehicleUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Vehicle:
    vehicle = _get_owned_vehicle(vehicle_id, current_user, db)
    changes = payload.model_dump(exclude_unset=True)
    make = changes.get("make", vehicle.make)
    model = changes.get("model", vehicle.model)
    if "make" in changes or "model" in changes:
        _require_catalog_entry(make, model)
    for field, value in changes.items():
        setattr(vehicle, field, value)
    db.add(vehicle)
    _commit_or_conflict(
        db,
        changes.get("plate", vehicle.plate),
        changes.get("vin", vehicle.vin),
    )
    db.refresh(vehicle)
    return vehicle


@router.delete("/{vehicle_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vehicle(
    vehicle_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    vehicle = _get_owned_vehicle(vehicle_id, current_user, db)
    db.delete(vehicle)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
