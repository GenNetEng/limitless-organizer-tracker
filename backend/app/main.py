from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import status as status_router
from app.config import settings

app = FastAPI(title="Limitless Organizer Tracker")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins.split(","),
    allow_methods=["GET"],
    allow_headers=["*"],
)
app.include_router(status_router.router)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}
