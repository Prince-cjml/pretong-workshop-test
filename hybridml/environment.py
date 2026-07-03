from __future__ import annotations

import hashlib
import os
import platform
import subprocess
from pathlib import Path

import numpy as np
import torch
from packaging.version import Version

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_PYTHON = (3, 10)
REQUIRED_TORCH = "2.1.2"
REQUIRED_NUMPY = "1.26.4"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _command_line(command: list[str]) -> str:
    try:
        return subprocess.check_output(command, text=True, stderr=subprocess.STDOUT).splitlines()[0]
    except Exception:
        return "unavailable"


def verify_environment() -> dict[str, str | None]:
    python_version = platform.python_version()
    if tuple(map(int, python_version.split(".")[:2])) != REQUIRED_PYTHON:
        raise RuntimeError(
            f"Expected Python 3.10.x, found {python_version}. Activate hybridml-rescue."
        )
    if Version(torch.__version__).base_version != REQUIRED_TORCH:
        raise RuntimeError(f"Expected PyTorch {REQUIRED_TORCH}, found {torch.__version__}.")
    if torch.version.cuda is not None:
        raise RuntimeError("This project requires the CPU-only PyTorch build.")
    if np.__version__ != REQUIRED_NUMPY:
        raise RuntimeError(f"Expected NumPy {REQUIRED_NUMPY}, found {np.__version__}.")

    lock_path = ROOT / "conda-linux-64.lock"
    compiler = os.environ.get("CXX", "")
    return {
        "python_version": python_version,
        "torch_version": torch.__version__,
        "numpy_version": np.__version__,
        "torch_cuda": torch.version.cuda,
        "environment_lock_sha256": _sha256(lock_path),
        "compiler": compiler or None,
        "compiler_version": _command_line([compiler, "--version"]) if compiler else "unavailable",
        "cmake_version": _command_line(["cmake", "--version"]),
    }


def main() -> None:
    for key, value in verify_environment().items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
