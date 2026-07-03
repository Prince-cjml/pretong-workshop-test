from __future__ import annotations

import ctypes
from pathlib import Path

import numpy as np
from numpy.ctypeslib import ndpointer

ROOT = Path(__file__).resolve().parents[1]
LIBRARY_PATH = ROOT / "build" / "fastops.so"


class NativeError(RuntimeError):
    pass


def _load_library() -> ctypes.CDLL:
    if not LIBRARY_PATH.is_file():
        raise NativeError(
            f"Native library not found at {LIBRARY_PATH}. Run bash scripts/build.sh first."
        )
    library = ctypes.CDLL(str(LIBRARY_PATH))
    library.fastops_api_version.argtypes = []
    library.fastops_api_version.restype = ctypes.c_int
    library.standardize_features.argtypes = [
        ndpointer(dtype=np.float32, ndim=2, flags="C_CONTIGUOUS"),
        ndpointer(dtype=np.float32, ndim=2, flags="C_CONTIGUOUS"),
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_float,
    ]
    library.standardize_features.restype = ctypes.c_int
    return library


def api_version() -> int:
    return int(_load_library().fastops_api_version())


def standardize_features(values: np.ndarray, epsilon: float = 1e-6) -> np.ndarray:
    x = np.ascontiguousarray(values, dtype=np.float32)
    if x.ndim != 2:
        raise ValueError("Expected a two-dimensional feature matrix.")
    output = np.empty_like(x)
    status = _load_library().standardize_features(x, output, x.shape[0], x.shape[1], epsilon)
    if status != 0:
        raise NativeError(f"fastops failed with error code {status}.")
    return output
