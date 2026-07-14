#!/bin/bash
set -euo pipefail

# Single deploy path: dashboard YAML + HA theme + wallpapers, then ONE core restart.
# Staging must already be built (pipeline/scripts/build_engine.py).

# --- CONFIGURATION ---
TARGET_IP="192.168.1.181"
TARGET_USER="root"
SSH_KEY="${HOME}/.ssh/id_rsa"
# LogLevel=ERROR suppresses host-key noise ("Permanently added ... to the list of known hosts").
SSH_OPTS=(
  -o BatchMode=yes
  -o StrictHostKeyChecking=no
  -o UserKnownHostsFile=/dev/null
  -o GlobalKnownHostsFile=/dev/null
  -o LogLevel=ERROR
  -i "${SSH_KEY}"
)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

STAGING_DIR="${PROJECT_ROOT}/build/staging"
REMOTE_BASE_DIR="/root/config/dashboards/liquid_glass_theme"
REMOTE_CURRENT="${REMOTE_BASE_DIR}/current_build"
REMOTE_BACKUP="${REMOTE_BASE_DIR}/backup"
REMOTE_TMP="${REMOTE_BASE_DIR}/tmp_extraction"
REMOTE_THEMES_DIR="/root/config/themes"
REMOTE_WWW_DIR="/root/config/www/liquid_glass"

echo "[1/5] Pre-flight Check (Staging Resolution)..."
if [ ! -d "${STAGING_DIR}" ] || [ -z "$(ls -A "${STAGING_DIR}")" ]; then
    echo "FATAL EXCEPTION: Staging directory is missing or empty at ${STAGING_DIR}"
    exit 1
fi
if [ ! -f "${STAGING_DIR}/dashboard.yaml" ]; then
    echo "FATAL EXCEPTION: Missing ${STAGING_DIR}/dashboard.yaml — run build_engine first"
    exit 1
fi
if [ ! -f "${STAGING_DIR}/button_card_templates.yaml" ]; then
    echo "FATAL EXCEPTION: Missing ${STAGING_DIR}/button_card_templates.yaml — run build_engine first"
    exit 1
fi

THEME_COUNT=0
if [ -d "${STAGING_DIR}/themes" ]; then
    THEME_COUNT="$(find "${STAGING_DIR}/themes" -maxdepth 1 -name '*.yaml' | wc -l | tr -d ' ')"
fi
WWW_COUNT=0
if [ -d "${STAGING_DIR}/www/liquid_glass" ]; then
    WWW_COUNT="$(find "${STAGING_DIR}/www/liquid_glass" -maxdepth 1 -type f ! -name '.*' | wc -l | tr -d ' ')"
fi
if [ "${THEME_COUNT}" -lt 1 ]; then
    echo "FATAL EXCEPTION: No staged theme YAML under ${STAGING_DIR}/themes/ — run build_engine first"
    exit 1
fi
if [ "${WWW_COUNT}" -lt 1 ]; then
    echo "FATAL EXCEPTION: No staged wallpapers under ${STAGING_DIR}/www/liquid_glass/ — run build_engine first"
    exit 1
fi

echo "[2/5] Remote State Backup & Pre-clean..."
ssh "${SSH_OPTS[@]}" "${TARGET_USER}@${TARGET_IP}" << EOF
    mkdir -p ${REMOTE_BASE_DIR}
    rm -rf ${REMOTE_BACKUP}
    rm -rf ${REMOTE_TMP}

    if [ -d "${REMOTE_CURRENT}" ]; then
        cp -r ${REMOTE_CURRENT} ${REMOTE_BACKUP}
    fi
EOF

echo "[3/5] Upload dashboard YAML (atomic swap)..."
scp -r "${SSH_OPTS[@]}" "${STAGING_DIR}" "${TARGET_USER}@${TARGET_IP}:${REMOTE_TMP}"

ssh "${SSH_OPTS[@]}" "${TARGET_USER}@${TARGET_IP}" << EOF
    rm -rf ${REMOTE_CURRENT}
    mv ${REMOTE_TMP} ${REMOTE_CURRENT}
EOF

echo "[4/5] Upload theme + wallpapers..."
ssh "${SSH_OPTS[@]}" "${TARGET_USER}@${TARGET_IP}" "mkdir -p ${REMOTE_THEMES_DIR} ${REMOTE_WWW_DIR}"
scp "${SSH_OPTS[@]}" "${STAGING_DIR}/themes"/*.yaml \
    "${TARGET_USER}@${TARGET_IP}:${REMOTE_THEMES_DIR}/"
scp "${SSH_OPTS[@]}" "${STAGING_DIR}/www/liquid_glass"/* \
    "${TARGET_USER}@${TARGET_IP}:${REMOTE_WWW_DIR}/"

echo "[5/5] Triggering HA Core Restart (once)..."
ssh "${SSH_OPTS[@]}" "${TARGET_USER}@${TARGET_IP}" "ha core restart" \
    || echo "WARNING: Could not trigger HA restart automatically."

echo "✅ DEPLOYMENT SUCCESSFUL (dashboard + theme + wallpapers, single restart)."
echo "   Dashboard: ${REMOTE_CURRENT}"
echo "   Themes:    ${REMOTE_THEMES_DIR}/"
echo "   Assets:    ${REMOTE_WWW_DIR}/"
echo "   Rollback state preserved at ${REMOTE_BACKUP}"
echo "   Hard-refresh Liquid Glass after core is back; Profile → Theme → liquid_glass_v1.0 if needed."
