#!/bin/bash
# Live verify on the VPS: provision -> pdf -> usage -> revoke. Prints one line each.
set -u
BASE="${1:-http://127.0.0.1:8091}"
A=$(grep ADMIN ~/.secrets/docrender.env | cut -d= -f2)
echo "health: $(curl -s $BASE/health)"
K=$(curl -s -X POST $BASE/v1/admin/provision -H "X-Admin-Key: $A" -H 'Content-Type: application/json' -d '{"label":"livetest"}' | python3 -c 'import json,sys; print(json.load(sys.stdin)["key"])')
echo "pdf: $(curl -s -o /dev/null -w '%{http_code}' -X POST $BASE/v1/render/pdf -H "X-API-Key: $K" -H 'Content-Type: application/json' -d '{"text":"live"}')"
echo "usage: $(curl -s $BASE/v1/usage -H "X-API-Key: $K")"
echo "revoke: $(curl -s -X POST $BASE/v1/admin/revoke -H "X-Admin-Key: $A" -H 'Content-Type: application/json' -d "{\"key\":\"$K\"}")"
