# Restaurant API

REST API built with FastAPI to manage restaurant users and reservations. Data is loaded from CSV files at startup and kept in memory.

## Requirements

- Python 3.10+
- Dependencies listed in `requirements.txt`

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Running

```bash
uvicorn main:app --reload
```

The API will be available at `http://127.0.0.1:8000` and the interactive docs at `http://127.0.0.1:8000/docs`.

## Test it

Follow these steps in order. Some steps reuse IDs from earlier responses — replace the placeholder values when you get there.

### 1. View all users

```
GET http://127.0.0.1:8000/users
```

### 2. View all reservations

```
GET http://127.0.0.1:8000/reservations
```

### 3. Create a user

```bash
curl -X POST "http://127.0.0.1:8000/users" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Marcos",
    "last_name": "Beliera",
    "email": "marcos.beliera@telus.com",
    "phone": "22234242433",
    "postal_code": "7600",
    "age": 30
  }'
```

Expected response: the created user, including the generated `id`. **Copy that `id` — you will need it in step 5.**

### 4. View the user by email

```
GET http://127.0.0.1:8000/users/marcos.beliera@telus.com
```

### 5. Create a reservation

Replace `<user_id>` with the `id` returned in step 3.

```bash
curl -X POST "http://127.0.0.1:8000/reservations" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "<user_id>",
    "number_of_guests": 4,
    "location": "front",
    "reservation_date": "2026-07-01",
    "reservation_time": "09:00:00"
  }'
```

Copy the reservation `id` returned — you will need it in steps 8 and 9.

### 6. Search reservations by date

```bash
curl -X GET "http://127.0.0.1:8000/reservations/search?reservation_date=2026-07-01"
```

### 7. Try to create a reservation at the same date and time

```bash
curl -X POST "http://127.0.0.1:8000/reservations" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "<user_id>",
    "number_of_guests": 4,
    "location": "front",
    "reservation_date": "2026-07-01",
    "reservation_time": "09:00:00"
  }'
```

Expected response: error — the timeslot is already booked.

### 8. Update the reservation

Replace `<reservation_id>` with the reservation `id` from step 5.

```bash
curl -X PATCH "http://127.0.0.1:8000/reservations/<reservation_id>" \
  -H "Content-Type: application/json" \
  -d '{
    "number_of_guests": 10
  }'
```

### 9. Cancel the reservation

By id:

```
DELETE http://127.0.0.1:8000/reservations/?reservation_id=<reservation_id>
```

Or by date and time:

```
DELETE http://127.0.0.1:8000/reservations/?reservation_date=2026-05-25&reservation_time=18:30:00
```

### 10. Check profile status

```
GET http://127.0.0.1:8000/users/profile-check?last_name=Stewart
```

## Project structure

```
.
├── main.py                  # Entry point and router registration
├── routers/
│   ├── users.py             # User endpoints and model
│   └── reservations.py      # Reservation endpoints and model
├── tools/
│   ├── data_import.py       # CSV loaders for users and reservations
│   └── validations.py       # Shared validators (future date, timeslot conflict)
├── user_data.csv            # Initial user data
├── reservation_data.csv     # Initial reservation data
└── requirements.txt
```
