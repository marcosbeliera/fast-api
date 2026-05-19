from datetime import date, time
from fastapi import HTTPException, status
from pydantic import UUID4

def check_future_date(value: date | None) -> date | None:
    if value is not None and value <= date.today():
        raise ValueError("The reservation date must be strictly in the future.")
    return value

def check_timeslot_conflict(
    reservation_date: date, 
    reservation_time: time, 
    reservation_list: list, 
    current_id: UUID4 | None = None
) -> None:
    """
    Checks if a date and time slot is already taken by another reservation.
    Raises an HTTP 409 Conflict if a clash is found.
    """
    if any(
        r.reservation_date == reservation_date
        and r.reservation_time == reservation_time 
        and r.id != current_id  # If editing, ignore the reservation itself
        for r in reservation_list
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, 
            detail="This date and time slot is already reserved."
        )