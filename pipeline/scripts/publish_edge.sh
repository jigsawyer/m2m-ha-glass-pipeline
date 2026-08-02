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

if [ ! -d "${STAGING_DIR}/views" ]; then
    echo "FATAL: ${STAGING_DIR}/views/ missing — refusing to publish broken dashboard."
    exit 1
fi

# Extract !include views/*.yaml paths from dashboard and require each file.
missing=0
while IFS= read -r rel; do
    [ -z "${rel}" ] && continue
    if [ ! -f "${STAGING_DIR}/${rel}" ]; then
        echo "FATAL: dashboard includes ${rel} but file missing under staging."
        missing=1
    fi
done < <(grep -E '^\s*-\s*!include\s+views/' "${STAGING_DIR}/dashboard.yaml" | sed -E 's/.*!include[[:space:]]+//')

VIEW_COUNT=$(find "${STAGING_DIR}/views" -maxdepth 1 -name '*.yaml' | wc -l | tr -d ' ')
if [ "${VIEW_COUNT}" -lt 1 ] || [ "${missing}" -ne 0 ]; then
    echo "FATAL: staging views invalid (count=${VIEW_COUNT}, missing_includes=${missing})."
    exit 1
fi

echo "[2/3] Initializing Ephemeral State..."
cd "${STAGING_DIR}"

# Зачищаємо старий гіт, якщо закешувався
rm -rf .git

# Isolate from parent-repo .gitignore (root has build/* which would skip staging).
git init
git checkout -b "${EDGE_BRANCH}"
# Do not inherit excludes from outside this work tree.
git -c core.excludesFile=/dev/null add -A

TRACKED_VIEWS=$(git ls-files 'views/*.yaml' | wc -l | tr -d ' ')
if [ "${TRACKED_VIEWS}" -lt 1 ]; then
    echo "FATAL: git staged 0 views/*.yaml (gitignore isolation failed)."
    git status --short | head -50
    exit 1
fi

git commit -m "chore(release): compile edge artifact $(date +%s)"

echo "[3/3] Executing Force Push to ${EDGE_BRANCH}..."
# CI supplies GITHUB_TOKEN + GITHUB_REPOSITORY (ADR-0057). Local/agent runs
# still use the parent-repo remote URL — agents must not invoke this script.
if [ -n "${GITHUB_TOKEN:-}" ] && [ -n "${GITHUB_REPOSITORY:-}" ]; then
    PUSH_URL="https://x-access-token:${GITHUB_TOKEN}@github.com/${GITHUB_REPOSITORY}.git"
else
    PUSH_URL="${REMOTE_URL}"
fi
git push --force "${PUSH_URL}" "${EDGE_BRANCH}"

rm -rf .git
echo "✅ State successfully published to branch: ${EDGE_BRANCH} (${TRACKED_VIEWS} views)"
