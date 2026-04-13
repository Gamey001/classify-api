from fastapi import FastAPI, Query, Request
from fastapi.responses import JSONResponse
import httpx
import os
from datetime import datetime, timezone

app = FastAPI()

CORS_HEADERS = {"Access-Control-Allow-Origin": "*"}
GENDERIZE_URL = "https://api.genderize.io/"


@app.middleware("http")
async def add_cors_header(request: Request, call_next):
    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response


@app.options("/api/classify")
async def options_classify():
    return JSONResponse(
        status_code=200,
        content={},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        },
    )


@app.get("/api/classify")
async def classify(name: str = Query(default=None)):
    if not name or not name.strip():
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": "name query parameter is required"},
            headers=CORS_HEADERS,
        )

    if not isinstance(name, str):
        return JSONResponse(
            status_code=422,
            content={"status": "error", "message": "name must be a string"},
            headers=CORS_HEADERS,
        )

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(GENDERIZE_URL, params={"name": name})
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPStatusError as exc:
        return JSONResponse(
            status_code=502,
            content={"status": "error", "message": f"Genderize API error: {exc.response.status_code}"},
            headers=CORS_HEADERS,
        )
    except Exception:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": "Failed to reach Genderize API"},
            headers=CORS_HEADERS,
        )

    gender = data.get("gender")
    count = data.get("count", 0)

    if gender is None or count == 0:
        return JSONResponse(
            status_code=200,
            content={"status": "error", "message": "No prediction available for the provided name"},
            headers=CORS_HEADERS,
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
        headers=CORS_HEADERS,
    )


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 5000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
