from fastapi import FastAPI

from app.api.routers import status as status_router

app = FastAPI(title="Limitless Organizer Tracker")
app.include_router(status_router.router)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}
