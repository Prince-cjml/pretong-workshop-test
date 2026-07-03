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
    samples = 1536
    input_dim = 12
    classes = 3
    centers = rng.normal(0.0, 1.2, size=(classes, input_dim)).astype(np.float32)
    labels = np.arange(samples, dtype=np.int64) % classes
    rng.shuffle(labels)
    features = centers[labels] + rng.normal(0.0, 0.35, size=(samples, input_dim))
    scale = rng.uniform(0.6, 1.4, size=(input_dim,)).astype(np.float32)
    bias = rng.normal(0.0, 0.2, size=(input_dim,)).astype(np.float32)
    features = features.astype(np.float32) * scale + bias
    return features.astype(np.float32), labels
