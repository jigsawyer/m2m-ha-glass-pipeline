#!/bin/bash
# Path: pipeline/scripts/publish_edge.sh
set -euo pipefail

# Constraints
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
STAGING_DIR="${PROJECT_ROOT}/build/staging"
EDGE_BRANCH="edge-state"
REMOTE_URL=$(git config --get remote.origin.url)

echo "[1/3] Pre-flight Validation..."
if [ ! -f "${STAGING_DIR}/dashboard.yaml" ]; then
    echo "FATAL: ${STAGING_DIR}/dashboard.yaml not found."
    echo "Run python pipeline/scripts/build_engine.py first."
    exit 1
fi

echo "[2/3] Initializing Ephemeral State..."
cd "${STAGING_DIR}"

# Зачищаємо старий гіт, якщо закешувався
rm -rf .git 

git init
git checkout -b "${EDGE_BRANCH}"
git add .
git commit -m "chore(release): compile edge artifact $(date +%s)"

echo "[3/3] Executing Force Push to ${EDGE_BRANCH}..."
# Пушимо в основний репозиторій, перезаписуючи історію артефактів
git push --force "${REMOTE_URL}" "${EDGE_BRANCH}"

rm -rf .git
echo "✅ State successfully published to branch: ${EDGE_BRANCH}"