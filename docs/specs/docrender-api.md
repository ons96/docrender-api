# docrender-api spec (Tier-2)

docrender-api is a boring paid conversion API (text to PDF, image resize/convert) with API-key auth and hard daily caps, built to run gap-tolerant on a supervised-only schedule: public repo for free GH Actions minutes, runtime on VPS with systemd auto-restart, billing via marketplace so no per-order human step, support async-only.

## Acceptance criteria

1. `POST /v1/render/pdf` and `POST /v1/convert/image` work behind `X-API-Key`, daily cap enforced, `pytest` green offline with no network.
2. Gap-tolerant: `GET /health` for watchers, systemd auto-restart documented, CI on free public GH minutes, secrets only in env/GH Secrets, README states async-only support with 1-3 day replies.
3. Billing path needs zero manual steps per order: marketplace (RapidAPI) or Stripe webhook provisions keys, free tier hard-capped, abuse auto-429s.
