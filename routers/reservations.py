from datetime import date, datetime, time
from pathlib import Path
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import UUID4, AfterValidator, BaseModel, ConfigDict, Field

from tools.data_import import load_reservations_from_csv
from tools.validations import check_future_date, check_timeslot_conflict

# Router configuration for reservation endpoints - Go to http://127.0.0.1:8000/reservations
router = APIRouter(
    prefix="/reservations",
    responses={404: {"message": "not found"}},
    tags=["Reservations"],
)


# Reservation data model (matches reservation_data.csv)
class Reservation(BaseModel):
    # validate_assignment so setattr() in PATCH re-runs field validators
    model_config = ConfigDict(validate_assignment=True)

    id: UUID4 = Field(default_factory=uuid4)
    user_id: UUID4
    number_of_guests: int = Field(ge=1)
    location: str
    reservation_date: Annotated[date, AfterValidator(check_future_date)]
    reservation_time: time
    created_at: datetime = Field(default_factory=datetime.now)


class ReservationUpdate(BaseModel):
    user_id: UUID4 | None = None
    number_of_guests: int | None = Field(default=None, ge=1)
    location: str | None = None
    reservation_date: Annotated[date | None, AfterValidator(check_future_date)] = None
    reservation_time: time | None = None


# upload my current data
reservation_list = load_reservations_from_csv(
    csv_path=Path(__file__).resolve().parent.parent / "reservation_data.csv",
    Reservation=Reservation,
)


# ============================
# GET Reservations
# Page 1 = /reservations/?limit=10&offset=0
# Page 2 = /reservations/?limit=10&offset=10
# Page 3 = /reservations/?limit=10&offset=20
# ============================

@router.get("/", response_model=list[Reservation])
async def get_reservations(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    return reservation_list[offset : offset + limit]


# ============================
# SEARCH Reservation /reservations/search?reservation_id=&user_id=&reservation_date=&created_at=
# ============================

@router.get("/search", response_model=list[Reservation])
async def search_reservation(
    reservation_id: UUID4 | None = None,
    user_id: UUID4 | None = None,
    reservation_date: date | None = None,
    reservation_time: time | None = None,
    created_at: datetime | None = None,
):
    """
    Search for reservations using optional filters.

    Requirements:
    - At least one filter query parameter must be provided.
    - Multiple filters will be combined using an AND condition.
    """

    filters = (reservation_id, user_id, reservation_date, reservation_time, created_at)
    if all(v is None for v in filters):
        raise HTTPException(
            status_code=400,
            detail="provide at least one filter: reservation_id, user_id, reservation_date, reservation_time or created_at",
        )

    results = [
        r for r in reservation_list
        if (reservation_id is None or r.id == reservation_id)
        and (user_id is None or r.user_id == user_id)
        and (reservation_date is None or r.reservation_date == reservation_date)
        and (reservation_time is None or r.reservation_time == reservation_time)
        and (created_at is None or r.created_at == created_at)
    ]

    if not results:
        raise HTTPException(status_code=404, detail="reservation not found")

    return results


# ============================
# POST Reservation /reservations/
# ============================

@router.post("/", response_model=Reservation, status_code=status.HTTP_201_CREATED)
async def create_reservation(reservation: Reservation):
    """
    Create a new reservation.

    Requirements:
    - Target date and time must not be already booked.
    - Date must be in the future; guests must be at least 1 (enforced by schema).
    - id and created_at are auto-generated when the client omits them.
    """

    check_timeslot_conflict(
        reservation_date=reservation.reservation_date,
        reservation_time=reservation.reservation_time,
        reservation_list=reservation_list,
    )

    reservation_list.append(reservation)
    return reservation


# ============================
# CANCEL Reservation /reservations/
# ============================

@router.delete("/", response_model=Reservation)
async def delete_reservation(
    reservation_id: UUID4 | None = None,
    reservation_date: date | None = None,
    reservation_time: time | None = None,
):
    """
    Cancel and remove a reservation from the system.

    Requirements:
    - Must provide either 'reservation_id' OR both 'reservation_date' and 'reservation_time'.
    - If 'reservation_date' is provided without 'reservation_time' (or vice versa), it will fail.
    """
    if reservation_id is None and not (reservation_date and reservation_time):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must provide either 'reservation_id' OR both 'reservation_date' and 'reservation_time'.",
        )

    index_to_delete = None
    for index, r in enumerate(reservation_list):
        if reservation_id is not None and r.id == reservation_id:
            index_to_delete = index
            break
        if (
            reservation_date is not None
            and reservation_time is not None
            and r.reservation_date == reservation_date
            and r.reservation_time == reservation_time
        ):
            index_to_delete = index
            break

    if index_to_delete is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reservation not found with the provided criteria.",
        )

    return reservation_list.pop(index_to_delete)


# ============================
# Update Reservation /reservations/{id}
# ============================

@router.patch("/{id}", response_model=Reservation, status_code=status.HTTP_200_OK)
async def update_reservation(id: UUID4, update_data: ReservationUpdate):
    """
    Partially update an existing reservation.

    Requirements:
    - The reservation ID must exist.
    - Allows partial updates for: user_id, number_of_guests, location, reservation_date, reservation_time.
    """

    current_res = next((r for r in reservation_list if r.id == id), None)
    if current_res is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reservation not found.",
        )

    updated_fields = update_data.model_dump(exclude_unset=True)

    new_date = updated_fields.get("reservation_date", current_res.reservation_date)
    new_time = updated_fields.get("reservation_time", current_res.reservation_time)
    check_timeslot_conflict(
        reservation_date=new_date,
        reservation_time=new_time,
        reservation_list=reservation_list,
        current_id=id,
    )

    # validate_assignment on Reservation re-runs field validators on each setattr
    for key, value in updated_fields.items():
        setattr(current_res, key, value)

    return current_res
