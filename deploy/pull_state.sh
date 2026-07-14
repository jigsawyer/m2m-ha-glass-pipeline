#!/bin/bash
# Path: /config/deploy/pull_state.sh
set -e

# Constraints
STATE_DIR="/config/edge-state"
HA_URL="http://192.168.1.181:8123"
HA_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiIxOTgxMWU4MmM1YWY0NzQ4ODkyNjIyNDM0M2NiOGE3MiIsImlhdCI6MTc4Mzk2NDE2OSwiZXhwIjoyMDk5MzI0MTY5fQ.ksCyuH_KmPWQA6OOzlrLiqgRSRIlV-byNrBtIIw_f8Q" 

echo "[$(date -Iseconds)] Starting Pull-based sync..."

# Security override для Git, якщо запускається з-під іншого юзера
git config --global --add safe.directory "${STATE_DIR}"

cd "${STATE_DIR}"
git fetch origin edge-state

LOCAL=$(git rev-parse @)
REMOTE=$(git rev-parse @{u})

if [ "$LOCAL" = "$REMOTE" ]; then
    echo "[$(date -Iseconds)] State is in sync. No mutation required."
    exit 0
fi

echo "[$(date -Iseconds)] Desync detected. Applying mutations..."
git reset --hard origin/edge-state
git clean -fd

# -- Symlink Routing для статики (www) --
# HA очікує шпалери у /config/www/liquid_glass. Замість копіювання - лінкуємо.
mkdir -p /config/www
rm -rf /config/www/liquid_glass
ln -sfn "${STATE_DIR}/www/liquid_glass" /config/www/liquid_glass

# -- Trigger UI Reload (Zero Downtime) --
# Перезавантаження тем
curl -X POST -s -o /dev/null -w "%{http_code}" \
    -H "Authorization: Bearer ${HA_TOKEN}" \
    -H "Content-Type: application/json" \
    "${HA_URL}/api/services/frontend/reload_themes"

# Перезавантаження дашбордів
curl -X POST -s -o /dev/null -w "%{http_code}" \
    -H "Authorization: Bearer ${HA_TOKEN}" \
    -H "Content-Type: application/json" \
    "${HA_URL}/api/services/lovelace/reload"

echo "[$(date -Iseconds)] Deployment pipeline successfully executed."