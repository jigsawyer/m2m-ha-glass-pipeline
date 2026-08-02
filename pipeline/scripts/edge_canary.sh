#!/usr/bin/env bash
# Edge canary health check + auto-rollback (ADR-0064).
# Usage: edge_canary.sh <stable_edge_state_sha>
set -euo pipefail

STABLE_SHA="${1:?stable edge-state SHA required}"
TIMEOUT_SEC="${M2M_CANARY_TIMEOUT_SEC:-60}"
HA_URL="${HA_URL:-http://127.0.0.1:8123}"
LOG_DIR="${M2M_CANARY_LOG_DIR:-pipeline/logs}"
LOG_FILE="${LOG_DIR}/edge_canary.jsonl"
mkdir -p "${LOG_DIR}"

: "${HA_TOKEN:?HA_TOKEN is required for Edge canary (ADR-0064)}"

echo "Canary: probing Edge REST API for up to ${TIMEOUT_SEC}s (ADR-0064)..."

set +e
ssh haos-target "HA_TOKEN=$(printf '%q' "${HA_TOKEN}") HA_URL=$(printf '%q' "${HA_URL}") M2M_CANARY_TIMEOUT_SEC=$(printf '%q' "${TIMEOUT_SEC}") M2M_STABLE_EDGE_SHA=$(printf '%q' "${STABLE_SHA}") bash -s" <<'EOS'
set -euo pipefail
HA_URL="${HA_URL:-http://127.0.0.1:8123}"
TIMEOUT_SEC="${M2M_CANARY_TIMEOUT_SEC:-60}"
TOKEN="${HA_TOKEN:-}"
if [ -z "${TOKEN}" ] && [ -f /config/deploy/ha_token ]; then
  TOKEN="$(tr -d '[:space:]' </config/deploy/ha_token)"
fi
if [ -z "${TOKEN}" ]; then
  echo "FATAL: HA_TOKEN unavailable for canary health check (ADR-0064)."
  exit 1
fi
URL="${HA_URL%/}/api/"
deadline=$((SECONDS + TIMEOUT_SEC))
attempts=0
last_code="none"
while [ "${SECONDS}" -lt "${deadline}" ]; do
  attempts=$((attempts + 1))
  code="$(curl -s -o /dev/null -w '%{http_code}' \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "Content-Type: application/json" \
    --max-time 10 \
    "${URL}" || echo fail)"
  last_code="${code}"
  if [ "${code}" = "200" ]; then
    echo "{\"ok\":true,\"status_code\":200,\"attempts\":${attempts},\"url\":\"${URL}\"}"
    exit 0
  fi
  sleep 2
done
echo "{\"ok\":false,\"status_code\":\"${last_code}\",\"attempts\":${attempts},\"url\":\"${URL}\",\"message\":\"timeout ${TIMEOUT_SEC}s\",\"stable_sha\":\"${M2M_STABLE_EDGE_SHA:-}\",\"adr\":\"ADR-0064\"}" >&2
exit 1
EOS
HEALTH_RC=$?
set -e

if [ "${HEALTH_RC}" -eq 0 ]; then
  echo "Edge canary health OK (ADR-0064)."
  exit 0
fi

FAIL_LINE="{\"event\":\"edge_canary_failure\",\"stable_sha\":\"${STABLE_SHA}\",\"timeout_sec\":${TIMEOUT_SEC},\"adr\":\"ADR-0064\",\"action\":\"rollback_edge_state_to_stable_sha\"}"
printf '%s\n' "${FAIL_LINE}" | tee -a "${LOG_FILE}" >&2
echo "Canary FAILED — rolling back edge-state to ${STABLE_SHA} (ADR-0064)." >&2

ssh haos-target "HA_TOKEN=$(printf '%q' "${HA_TOKEN}") HA_URL=$(printf '%q' "${HA_URL}") STABLE_SHA=$(printf '%q' "${STABLE_SHA}") bash -s" <<'EOS'
set -euo pipefail
STATE_DIR="/config/edge-state"
HA_URL="${HA_URL:-http://127.0.0.1:8123}"
TOKEN="${HA_TOKEN:-}"
if [ -z "${TOKEN}" ] && [ -f /config/deploy/ha_token ]; then
  TOKEN="$(tr -d '[:space:]' </config/deploy/ha_token)"
fi
if [ -z "${TOKEN}" ]; then
  echo "FATAL: HA_TOKEN unavailable during canary rollback (ADR-0064)."
  exit 1
fi
if [ ! -d "${STATE_DIR}/.git" ]; then
  echo "FATAL: ${STATE_DIR} is not a git checkout — cannot rollback."
  exit 1
fi
cd "${STATE_DIR}"
git reset --hard "${STABLE_SHA}"
git clean -fd
mkdir -p /config/www/liquid_glass
if [ -d "${STATE_DIR}/www/liquid_glass" ]; then
  find /config/www/liquid_glass -mindepth 1 -maxdepth 1 -exec rm -rf {} +
  cp -a "${STATE_DIR}/www/liquid_glass/." /config/www/liquid_glass/
fi
TH="$(curl -X POST -s -o /dev/null -w '%{http_code}' \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  "${HA_URL}/api/services/frontend/reload_themes" || echo fail)"
LV="$(curl -X POST -s -o /dev/null -w '%{http_code}' \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  "${HA_URL}/api/events/lovelace_updated" \
  -d '{}' || echo fail)"
echo "rollback reload_themes=${TH} lovelace_updated=${LV}"
if [ "${TH}" != "200" ] || [ "${LV}" != "200" ]; then
  echo "FATAL: UI reload failed during canary rollback (ADR-0064)."
  exit 1
fi
echo "Rolled back edge-state to ${STABLE_SHA} and re-applied stable UI reload."
EOS

echo "Canary rollback complete; deploy job failing closed (ADR-0064)." >&2
exit 1
