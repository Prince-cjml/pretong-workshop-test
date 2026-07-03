#!/usr/bin/env bash
set +euo pipefail
mode="${1:-bootstrap}"
failures=0

check() {
  label="$1"
  shift
  if "$@" >/dev/null 2>&1; then
    echo "[PASS] $label"
  else
    echo "[FAIL] $label"
    failures=$((failures + 1))
  fi
}

skip() {
  echo "[SKIP] $1"
}

if [[ "$mode" == "bootstrap" ]]; then
  check git command -v git
  if command -v mamba >/dev/null 2>&1 || command -v conda >/dev/null 2>&1; then
    echo "[PASS] conda or mamba"
  else
    echo "[FAIL] conda or mamba"
    failures=$((failures + 1))
  fi
  check "Linux x86_64" bash -c '[[ "$(uname -s)" == "Linux" && "$(uname -m)" == "x86_64" ]]'
elif [[ "$mode" == "environment" ]]; then
  if [[ -n "${CONDA_PREFIX:-}" ]]; then echo "[PASS] CONDA_PREFIX"; else echo "[FAIL] CONDA_PREFIX"; failures=$((failures + 1)); fi
  check "hybridml-rescue active" bash -c '[[ "${CONDA_DEFAULT_ENV:-}" == "hybridml-rescue" ]]'
  check "Python contract" python -m hybridml.environment
  check tomli python -c 'import tomli'
  check cmake command -v cmake
  check ninja command -v ninja
  if [[ -n "${CXX:-}" ]]; then echo "[PASS] CXX=$CXX"; else echo "[FAIL] CXX"; failures=$((failures + 1)); fi
  if [[ -n "${CONDA_PREFIX:-}" ]]; then
    check "Eigen CMake package" test -e "${CONDA_PREFIX}/share/eigen3/cmake/Eigen3Config.cmake"
  else
    skip "Eigen CMake package"
  fi
else
  echo "usage: bash scripts/doctor.sh [bootstrap|environment]"
  exit 2
fi

exit "$failures"
