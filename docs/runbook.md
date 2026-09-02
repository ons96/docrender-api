# runbook (gap-tolerant ops)

Service: systemd user unit `docrender-api`, port 127.0.0.1:8091, auto-restart always, 350M cap.
Deploy/recover: `bash deploy/deploy.sh` (idempotent, safe after any offline gap).
Keys: `~/.secrets/docrender.env` (`DOCRENDER_API_KEYS=a,b`), chmod 600, never in repo.
Health: `curl localhost:8091/health`. Logs: `journalctl --user -u docrender-api -n 30`.
Update: push to main, re-run deploy.sh (git pull + restart). CI must be green first.
Offline behavior: caps enforced in sqlite, abuse auto-429s, no human step per order.
Support: async-only, 1-3 business days. Never promise faster.
Public ingress later: Caddy/reverse-proxy + marketplace (RapidAPI) in front; keys stay private.
