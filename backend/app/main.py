from fastapi import FastAPI

app = FastAPI(title="UPCP Backend")


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "upcp-backend",
    }
