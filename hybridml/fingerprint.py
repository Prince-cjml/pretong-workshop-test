from __future__ import annotations

import hashlib
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATHS = [
    "CMakeLists.txt",
    "cpp/include/fastops.h",
    "cpp/src/fastops.cpp",
    "hybridml/environment.py",
    "hybridml/native.py",
    "hybridml/data.py",
    "hybridml/model.py",
    "hybridml/train.py",
    "config/train.toml",
    "environment.yml",
    "conda-linux-64.lock",
]


def _append_blob(hasher: "hashlib._Hash", label: bytes, payload: bytes) -> None:
    hasher.update(str(len(label)).encode("ascii"))
    hasher.update(b":")
    hasher.update(label)
    hasher.update(str(len(payload)).encode("ascii"))
    hasher.update(b":")
    hasher.update(payload)


def source_fingerprint(root: Path = ROOT) -> str:
    hasher = hashlib.sha256()
    for rel in sorted(SOURCE_PATHS):
        _append_blob(hasher, rel.encode("utf-8"), (root / rel).read_bytes())
    return hasher.hexdigest()


def config_fingerprint(root: Path = ROOT) -> str:
    return hashlib.sha256((root / "config" / "train.toml").read_bytes()).hexdigest()


def state_fingerprint(state_dict: dict[str, torch.Tensor]) -> str:
    hasher = hashlib.sha256()
    for name in sorted(state_dict):
        tensor = state_dict[name].detach().cpu().contiguous()
        meta = f"{name}|{tensor.dtype}|{tuple(tensor.shape)}".encode("utf-8")
        _append_blob(hasher, meta, tensor.numpy().tobytes())
    return hasher.hexdigest()
