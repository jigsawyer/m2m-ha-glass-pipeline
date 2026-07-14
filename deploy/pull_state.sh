#!/bin/bash
# Path: /config/deploy/pull_state.sh (HA host)
# GitOps consumer for this HA instance:
#   publish_edge.sh → origin/edge-state
#   this script     → /config/edge-state + /config/www/liquid_glass + UI reload
#
# Invoked on HA via shell_command.gitops_pull_state.
# Do NOT set lovelace.resource_mode: yaml unless you also ship a full
# lovelace.resources: list — HACS cards live in .storage/lovelace_resources.
set -euo pipefail

STATE_DIR="/config/edge-state"
HA_URL="http://192.168.1.181:8123"
# Long-lived token — set on the HA host only (never commit a real token).
HA_TOKEN="${HA_TOKEN:-}"

if [ -z "${HA_TOKEN}" ]; then
  echo "FATAL: HA_TOKEN env var is empty. Export it on the HA host before running."
  exit 1
fi

echo "[$(date -Iseconds)] Starting Pull-based sync..."

git config --global --add safe.directory "${STATE_DIR}"

cd "${STATE_DIR}"
git fetch origin edge-state

if ! git rev-parse --abbrev-ref --symbolic-full-name @{u} >/dev/null 2>&1; then
  git branch --set-upstream-to=origin/edge-state edge-state 2>/dev/null || true
fi

LOCAL=$(git rev-parse @)
REMOTE=$(git rev-parse @{u})

if [ "$LOCAL" = "$REMOTE" ]; then
  echo "[$(date -Iseconds)] Git is in sync with origin/edge-state."
else
  echo "[$(date -Iseconds)] Desync detected. Applying mutations..."
  git reset --hard origin/edge-state
  git clean -fd
fi

# Always copy wallpapers into /config/www (real files). Symlinks are not served by /local.
mkdir -p /config/www
rm -rf /config/www/liquid_glass
mkdir -p /config/www/liquid_glass
if [ -d "${STATE_DIR}/www/liquid_glass" ]; then
  cp -a "${STATE_DIR}/www/liquid_glass/." /config/www/liquid_glass/
  echo "[$(date -Iseconds)] Synced www/liquid_glass ($(ls -1 /config/www/liquid_glass | wc -l) files)."
else
  echo "[$(date -Iseconds)] WARNING: ${STATE_DIR}/www/liquid_glass missing"
fi

TH=$(curl -X POST -s -o /dev/null -w "%{http_code}" \
    -H "Authorization: Bearer ${HA_TOKEN}" \
    -H "Content-Type: application/json" \
    "${HA_URL}/api/services/frontend/reload_themes" || echo fail)
# YAML dashboard path for this host (configuration.yaml → liquid-glass-main)
LV=$(curl -X POST -s -o /dev/null -w "%{http_code}" \
    -H "Authorization: Bearer ${HA_TOKEN}" \
    -H "Content-Type: application/json" \
    "${HA_URL}/api/services/lovelace/reload" \
    -d '{"url_path":"liquid-glass-main"}' || echo fail)

echo "[$(date -Iseconds)] reload_themes=${TH} lovelace.reload=${LV}"
echo "[$(date -Iseconds)] Deployment pipeline successfully executed."
