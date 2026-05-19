from datetime import datetime
from pathlib import Path
from uuid import uuid4
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Query
from pydantic import UUID4, BaseModel, EmailStr, Field

from tools.data_import import load_users_from_csv

# Router configuration for user endpoints - Go to http://127.0.0.1:8000/users
router = APIRouter(
    prefix="/users",
    responses={404: {"message": "not found"}},
    tags=["users"],
)


# User data model (matches user_data.csv)
class User(BaseModel):
    id: UUID4 = Field(default_factory=uuid4)
    first_name: str
    last_name: str
    phone: str
    postal_code: str
    age: int = Field(gt=21)
    email: EmailStr
    created_at: datetime = Field(default_factory=datetime.now)


# upload my current data
user_list = load_users_from_csv(
    csv_path=Path(__file__).resolve().parent.parent / "user_data.csv",
    user_model=User,
)


# ============================
# POST user
# ============================

@router.post("/", response_model=User, status_code=status.HTTP_201_CREATED)
async def create_user(user: User):
    if any(u.email == user.email for u in user_list):
        raise HTTPException(status_code=409, detail="Email already exists")

    user_list.append(user)
    return user


# ============================
# GET users
# ============================

@router.get("/", response_model=list[User])
async def get_users():
    return user_list


# ============================
# GET User Status
# ============================

# Use a separate endpoint to satisfy the requirement to "Check if the user has an account or not first - using Phone Number and Name".

@router.get("/profile-check", response_model=User)
async def get_profile_check(
    phone: Optional[str] = Query(None, description="Search by phone"),
    last_name: Optional[str] = Query(None, description="Search by last_name")
):
    # 1. Validate that at least one parameter was provided
    if not phone and not last_name:
        raise HTTPException(
            status_code=400,
            detail="You must provide at least one search parameter: 'phone' or 'last_name'."
        )

    # 2. Search the list applying the "one or the other" logic
    user = None
    for u in user_list:
        if phone and u.phone == phone:
            user = u
            break
        # Using .lower() makes the name search case-insensitive
        if last_name and u.last_name.lower() == last_name.lower():
            user = u
            break

    # 3. If no user matched either criteria
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    return user


# ============================
# GET user
# ============================

@router.get("/{email}", response_model=User)
async def get_user(email: EmailStr):
    user = next(
        (u for u in user_list if u.email == email),
        None,
    )

    if user is None:
        raise HTTPException(status_code=404, detail="user not found")

    return user