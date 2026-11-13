# docrender-api

Boring document/image conversion API. Two endpoints, key auth, hard daily caps.

- `GET /health` -> `{"ok": true}`
- `POST /v1/render/pdf` JSON `{"text": "..."}` -> PDF (max 20,000 chars)
- `POST /v1/convert/image` JSON `{"url": "...", "width": 800}` -> resized PNG
- `GET /v1/usage` -> `{"used", "cap", "day"}`
- `POST /v1/admin/provision` / `POST /v1/admin/revoke` (X-Admin-Key)

Auth (either):
- Direct: `X-API-Key`, validated against `DOCRENDER_API_KEYS` (comma list) or the SQLite `keys` table.
- RapidAPI: `X-RapidAPI-Key` + `X-RapidAPI-Proxy-Secret` must equal `DOCRENDER_RAPIDAPI_SECRET` (set it when listing on RapidAPI; leave unset to disable that path).

Cap: `DOCRENDER_DAILY_CAP` per key per day (default 100), else 429. Run: `pip install -r requirements.txt && uvicorn app:app --port 8000`. Test: `pytest -q`.

RapidAPI listing copy: `docs/RAPIDAPI_LISTING.md`. Deploy: `deploy/deploy.sh`, public ingress via Caddy per `deploy/runbook.md`.

Support is async-only: replies in 1-3 business days, no SLA, no phone. Billing via marketplace so provisioning needs no human step. Secrets live in env only, never in repo.
