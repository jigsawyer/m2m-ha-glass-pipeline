#!/bin/bash
# Path: /config/m2m-pipeline/deploy/pull_state.sh
set -e

REPO_DIR="/config/m2m-ha-glass-pipeline"
HA_URL="http://192.168.1.181:8123"
HA_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiIxOTgxMWU4MmM1YWY0NzQ4ODkyNjIyNDM0M2NiOGE3MiIsImlhdCI6MTc4Mzk2NDE2OSwiZXhwIjoyMDk5MzI0MTY5fQ.ksCyuH_KmPWQA6OOzlrLiqgRSRIlV-byNrBtIIw_f8Q"

cd $REPO_DIR
git fetch origin master

LOCAL=$(git rev-parse @)
REMOTE=$(git rev-parse @{u})

if [ $LOCAL = $REMOTE ]; then
    exit 0
fi

git reset --hard origin/master
git clean -fd

# Trigger API to apply State
curl -X POST -s -o /dev/null \
    -H "Authorization: Bearer $HA_TOKEN" \
    -H "Content-Type: application/json" \
    $HA_URL/api/services/frontend/reload_themes

curl -X POST -s -o /dev/null \
    -H "Authorization: Bearer $HA_TOKEN" \
    -H "Content-Type: application/json" \
    $HA_URL/api/services/lovelace/reload