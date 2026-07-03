#!/usr/bin/env bash
set -euo pipefail

echo "[1/7] Environment"
python -m hybridml.environment

echo "[2/7] Native build"
bash scripts/build.sh

echo "[3/7] Public tests"
pytest -q tests/public

echo "[4/7] Checkpoint"
if [[ -f artifacts/model.ckpt ]]; then
  python -m hybridml.checkpoint validate artifacts/model.ckpt
else
  echo "artifacts/model.ckpt not present yet; train before final submission."
fi

echo "[5/7] Protected paths"
python .course/local_check.py protected

echo "[6/7] Repository hygiene"
python .course/local_check.py hygiene

echo "[7/7] Git history"
python .course/local_check.py history

echo "All public checks passed."
