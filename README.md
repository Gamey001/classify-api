# classify-api

A FastAPI service that classifies a name's gender using the [Genderize.io](https://genderize.io) API.

## Endpoint

```
GET /api/classify?name=<name>
```

### Success response

```json
{
  "status": "success",
  "data": {
    "name": "mark",
    "gender": "male",
    "probability": 1.0,
    "sample_size": 1378167,
    "is_confident": true,
    "processed_at": "2026-04-13T11:00:00Z"
  }
}
```

### Error response

```json
{ "status": "error", "message": "<error message>" }
```

| Case | Status |
|------|--------|
| Missing / empty `name` | 400 |
| Non-string `name` | 422 |
| No prediction available | 200 (error body) |
| Genderize API failure | 500 / 502 |

## Run locally

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```
