#!/usr/bin/env bash
set -euo pipefail
bash scripts/build.sh
python -m hybridml.train
