#!/bin/bash
# Idempotent deploy: pull, venv, install, restart. Safe to re-run after offline gaps.
set -u
DIR="${1:-$HOME/docrender-api}"
[ -d "$DIR/.git" ] || git clone https://github.com/ons96/docrender-api.git "$DIR"
cd "$DIR" || exit 1
git pull --ff-only || true
[ -d .venv ] || python3 -m venv .venv
.venv/bin/pip install -q -r requirements.txt
mkdir -p ~/.config/systemd/user ~/.secrets
cp deploy/docrender-api.service ~/.config/systemd/user/
[ -f ~/.secrets/docrender.env ] || { echo "DOCRENDER_API_KEYS=change-me" > ~/.secrets/docrender.env; chmod 600 ~/.secrets/docrender.env; echo "EDIT ~/.secrets/docrender.env THEN RE-RUN"; }
systemctl --user daemon-reload
systemctl --user enable --now docrender-api.service
for i in 1 2 3 4 5 6; do sleep 5; curl -sf http://127.0.0.1:8091/health && exit 0; done
echo "NOT UP - journalctl --user -u docrender-api -n 30"; exit 1
