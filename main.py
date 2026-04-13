from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
import os
from datetime import datetime, timezone

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

GENDERIZE_URL = "https://api.genderize.io/"


@app.get("/api/classify")
async def classify(name: str = Query(default=None)):
    # Validate: missing or empty name
    if not name or not name.strip():
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": "name query parameter is required"},
        )

    # Validate: non-string (FastAPI enforces str type, but handle numeric-only strings
    # that were passed as plain numbers — Query already coerces, so we check the type)
    if not isinstance(name, str):
        return JSONResponse(
            status_code=422,
            content={"status": "error", "message": "name must be a string"},
        )

    # Call Genderize API
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(GENDERIZE_URL, params={"name": name})
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPStatusError as exc:
        return JSONResponse(
            status_code=502,
            content={"status": "error", "message": f"Genderize API error: {exc.response.status_code}"},
        )
    except Exception:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": "Failed to reach Genderize API"},
        )

    gender = data.get("gender")
    count = data.get("count", 0)

    # Edge case: no prediction available
    if gender is None or count == 0:
        return JSONResponse(
            status_code=200,
            content={"status": "error", "message": "No prediction available for the provided name"},
        )

    probability = data.get("probability", 0.0)
    sample_size = count
    is_confident = probability >= 0.7 and sample_size >= 100
    processed_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    return JSONResponse(
        status_code=200,
        content={
            "status": "success",
            "data": {
                "name": data.get("name", name),
                "gender": gender,
                "probability": probability,
                "sample_size": sample_size,
                "is_confident": is_confident,
                "processed_at": processed_at,
            },
        },
    )


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 5000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
