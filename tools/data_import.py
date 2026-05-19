import csv
from pathlib import Path
from typing import Type

# Import user data

def load_users_from_csv(csv_path: Path, user_model: Type) -> None:
    """Populate user_list from a CSV file. Called once at app startup."""
    
    user_list = []
    
    with csv_path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            user_list.append(user_model(
                id=row["id_user"],
                first_name=row["first_name"],
                last_name=row["last_name"],
                phone=row["phone"],
                postal_code=row["postal_code"],
                age=int(row["age"]),
                email=row["email"],
                created_at=row["created_at"],
            ))
    return user_list

# Import reservation data

def load_reservations_from_csv(csv_path: Path, Reservation: Type) -> list:
    """Populate reservation_list from a CSV file. Called once at app startup."""

    reservation_list = []

    with csv_path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            reservation_list.append(Reservation(
                id=row["id"],
                user_id=row["user_id"],
                number_of_guests=int(row["number_of_guests"]),
                occasion=row["occasion"],
                reservation_date=row["reservation_date"],
                reservation_time=row["reservation_time"],
                created_at=row["created_at"],
            ))
    return reservation_list