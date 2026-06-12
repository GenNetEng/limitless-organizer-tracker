from fastapi import FastAPI

app = FastAPI(title="Limitless Organizer Tracker")


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}
