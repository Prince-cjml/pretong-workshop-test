#!/usr/bin/env bash
set -euo pipefail

COURSE_URL="${COURSE_URL:-https://github.com/Prince-cjml/pretong-workshop-test.git}"
ORIGIN_URL="$(git remote get-url origin)"

if [[ "$ORIGIN_URL" == "$COURSE_URL" ]]; then
    echo "ERROR: bootstrap must be run in a personal assignment repository."
    exit 1
fi

if git show-ref --verify --quiet refs/heads/submission; then
    echo "ERROR: submission already exists."
    exit 1
fi

if git remote get-url course >/dev/null 2>&1; then
    git remote set-url course "$COURSE_URL"
else
    git remote add course "$COURSE_URL"
fi

git fetch --force --prune course   "+refs/tags/course/*:refs/tags/course/*"   "+refs/heads/course/*:refs/remotes/course/*"

git switch --create submission course/broken-start-v3
git push --set-upstream origin submission

cat <<'EOF'
Bootstrap complete.

Current branch:
  submission

Next commands:
  bash scripts/doctor.sh bootstrap
  mamba create -y -n hybridml-rescue --file conda-linux-64.lock
  conda activate hybridml-rescue
  bash scripts/doctor.sh environment

Do not reset, rebase, or force-push submission.
EOF
