#!/usr/bin/env bash
# Publish this prepared repository to GitHub.
#
# Usage:
#   ./scripts/push-to-github.sh                 # uses OWNER=Akash0747
#   OWNER=your-name ./scripts/push-to-github.sh
#
# You must be authenticated first. Pick ONE:
#   A) GitHub CLI:  gh auth login
#   B) Credential helper: git config --global credential.helper store
#   C) Push over HTTPS with a Personal Access Token in the URL
#      (do NOT hard-code the token in this file).
#
# The repository must already exist on GitHub and be EMPTY
# (no README, no licence, no .gitignore) to avoid a merge conflict.

set -euo pipefail

OWNER="${OWNER:-Akash0747}"
REPO="${REPO:-edusphere-website}"
BRANCH="${BRANCH:-main}"
REMOTE="https://github.com/${OWNER}/${REPO}.git"

cd "$(dirname "$0")/.."

echo "→ Repository : ${OWNER}/${REPO}"
echo "→ Remote     : ${REMOTE}"
echo

if ! git rev-parse --git-dir > /dev/null 2>&1; then
  git init -b "${BRANCH}"
fi

git add -A
if ! git diff --cached --quiet; then
  git commit -m "Initial commit: EduSphere — frontend, backend, SQL database and docs"
else
  echo "→ Nothing new to commit."
fi

git branch -M "${BRANCH}"

if git remote get-url origin > /dev/null 2>&1; then
  git remote set-url origin "${REMOTE}"
else
  git remote add origin "${REMOTE}"
fi

echo "→ Pushing to ${REMOTE} …"
git push -u origin "${BRANCH}"

echo
echo "✅ Done. Set the description, topics and website URL from REPO_METADATA.md"
echo "   on https://github.com/${OWNER}/${REPO}/settings"
