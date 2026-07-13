#!/bin/bash
set -euo pipefail

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

REMOTE_BASE_DIR="/root/config/dashboards/liquid_glass_theme"
REMOTE_CURRENT="${REMOTE_BASE_DIR}/current_build"
REMOTE_BACKUP="${REMOTE_BASE_DIR}/backup"

echo "🚨 INITIATING EMERGENCY ROLLBACK..."

ssh "${SSH_OPTS[@]}" "${TARGET_USER}@${TARGET_IP}" << EOF
    if [ ! -d "${REMOTE_BACKUP}" ] || [ -z "\$(ls -A ${REMOTE_BACKUP})" ]; then
        echo "FATAL EXCEPTION: No valid backup found in ${REMOTE_BACKUP}"
        exit 1
    fi

    echo "Restoring previous state from ${REMOTE_BACKUP}..."
    rm -rf ${REMOTE_CURRENT}
    cp -r ${REMOTE_BACKUP} ${REMOTE_CURRENT}
EOF

echo "Triggering HA Core Restart..."
ssh "${SSH_OPTS[@]}" "${TARGET_USER}@${TARGET_IP}" "ha core restart" \
    || echo "WARNING: Could not trigger HA restart automatically."

echo "✅ ROLLBACK COMPLETE. System restored to previous stable state."