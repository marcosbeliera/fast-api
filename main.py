# uvicorn main:app --reload

from fastapi import FastAPI

from routers import reservations, users

app = FastAPI(title="Restaurant API", version="1.0.0")

# Routers
app.include_router(users.router)
app.include_router(reservations.router)


@app.get("/")
async def root():
    return {"status": "API running"}
