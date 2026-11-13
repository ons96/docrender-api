# DocRender API - RapidAPI listing copy

> Draft listing copy. Paste into the RapidAPI console when the public HTTPS
> host is live. Console steps are user-only.

## Short description (RapidAPI "API description" field)

Text to PDF and image resize, two REST calls. No SDK, no headless browser,
no scraping. Send text, get a PDF. Send an image URL, get a resized PNG.
Boring, fast, works from curl.

## Long description

DocRender does exactly two things and does them from any HTTP client:

- POST /v1/render/pdf - plain text in, PDF out (max 20,000 chars, Helvetica 12).
- POST /v1/convert/image - give it a public image URL and a target width
  (16-4000), get back a width-fitted PNG (source fetch capped at 8MB).

Both accept your RapidAPI key via the standard `X-RapidAPI-Key` header - no
second signup, no dashboard. GET /v1/usage reports your daily count and cap.

No headless browser, no PDF bloat, no image CDNs behind the scenes. Single
small Python process, SQLite usage metering, hard per-key daily caps so a
runaway script can't surprise you on a paid tier.

## Pricing tiers (suggested)

| Tier | Price | Limit |
|------|-------|-------|
| Free | $0 | 100 requests/day |
| Basic | $15/mo | 1,000 requests/day |
| Pro | $49/mo | 10,000 requests/day |
| Ultra | $199/mo | 100,000 requests/day |

Provider-side caps (DOCRENDER_DAILY_CAP) enforce the free tier; paid tiers
are metered by RapidAPI and the provider cap acts as a safety net.

## Example requests (paste as "Endpoints documentation")

Render a PDF:

    curl -X POST https://YOUR-HOST/v1/render/pdf \
      -H "X-RapidAPI-Key: <your key>" \
      -H "Content-Type: application/json" \
      -d '{"text":"Hello world"}'

Resize an image:

    curl -X POST https://YOUR-HOST/v1/convert/image \
      -H "X-RapidAPI-Key: <your key>" \
      -H "Content-Type: application/json" \
      -d '{"url":"https://example.com/photo.jpg","width":800}'

Check usage:

    curl https://YOUR-HOST/v1/usage -H "X-RapidAPI-Key: <your key>"

## Console checklist (user-only, ~30-60 min)

1. Create API named "DocRender" (category: Tools or Documents).
2. Base URL: https://YOUR-HOST (the Caddy host deployed from deploy/runbook.md).
3. Upload openapi.json (repo root, 6.1K) - endpoints and schemas import from it.
4. Create the four tiers above.
5. Copy the proxy secret from the console into the server env as
   DOCRENDER_RAPIDAPI_SECRET, restart the service.
6. Verify from an external network: /health 200, render 200 with a test key.

## Launch gates

- [ ] Public HTTPS host live (deploy/deploy.sh + Caddy, runbook.md).
- [ ] DOCRENDER_RAPIDAPI_SECRET set on the server.
- [ ] openapi.json matches current app (regenerated after auth change).
- [ ] External e2e test through RapidAPI proxy passes.
