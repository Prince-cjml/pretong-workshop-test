from __future__ import annotations

import hashlib
import os
import subprocess

import numpy as np


def repository_id(explicit: str | None = None) -> str:
    if explicit:
        return explicit
    env_value = os.environ.get("HYBRIDML_REPOSITORY_ID")
    if env_value:
        return env_value
    try:
        remote = subprocess.check_output(["git", "config", "--get", "remote.origin.url"], text=True).strip()
    except subprocess.CalledProcessError as exc:
        raise RuntimeError("Repository identity is unavailable. Set HYBRIDML_REPOSITORY_ID.") from exc
    name = remote.rstrip("/").rsplit("/", 1)[-1]
    return name.removesuffix(".git")


def assignment_seed(repo_id: str) -> int:
    digest = hashlib.sha256(repo_id.encode("utf-8")).digest()
    return int.from_bytes(digest[:4], "big")


def make_dataset(seed: int) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    features = rng.normal(0.0, 1.0, size=(1536, 12)).astype(np.float32)
    weights = rng.normal(0.0, 1.0, size=(12, 3)).astype(np.float32)
    logits = features @ weights
    labels = np.argmax(logits + 0.08 * rng.normal(size=logits.shape), axis=1)
    return features, labels.astype(np.int64)
