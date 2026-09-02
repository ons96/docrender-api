# docrender-api

Boring document/image conversion API. Two endpoints, key auth, hard daily caps.

- `GET /health` -> `{"ok": true}`
- `POST /v1/render/pdf` JSON `{"text": "..."}` -> PDF (max 50000 chars)
- `POST /v1/convert/image?w=&h=&fmt=` multipart `f` -> converted image

Auth: `X-API-Key` must be in `DOCRENDER_API_KEYS` (comma list). Cap: `DOCRENDER_DAILY_CAP` per key per day (default 100), else 429.

Run: `pip install -r requirements.txt && uvicorn app:app --port 8000`.
Test: `pytest -q`.

Support is async-only: replies in 1-3 business days, no SLA, no phone. Billing via marketplace so provisioning needs no human step. Secrets live in env only, never in repo.
