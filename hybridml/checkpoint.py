from __future__ import annotations

import argparse
import math
from pathlib import Path

import torch

from hybridml.data import assignment_seed, repository_id
from hybridml.environment import REQUIRED_NUMPY, REQUIRED_TORCH
from hybridml.fingerprint import config_fingerprint, source_fingerprint, state_fingerprint
from hybridml.model import TinyClassifier
from hybridml.native import api_version

REQUIRED_KEYS = {
    "schema_version",
    "model_state_dict",
    "epoch",
    "metrics",
    "environment",
    "assignment",
    "native",
    "fingerprints",
}


def validate_checkpoint(path: Path, repository: str | None = None) -> dict:
    if not path.is_file():
        raise SystemExit(f"Checkpoint not found: {path}")
    if path.stat().st_size > 1_000_000:
        raise SystemExit("Checkpoint is larger than 1 MB.")
    checkpoint = torch.load(path, map_location="cpu")
    if not isinstance(checkpoint, dict):
        raise SystemExit("Checkpoint must be a dictionary.")
    missing = REQUIRED_KEYS - set(checkpoint)
    extra = set(checkpoint) - REQUIRED_KEYS
    if missing or extra:
        raise SystemExit(f"Invalid checkpoint keys. Missing={sorted(missing)} Extra={sorted(extra)}")
    if checkpoint["schema_version"] != 1:
        raise SystemExit("Unsupported checkpoint schema version.")

    metrics = checkpoint["metrics"]
    for key in ("train_loss", "validation_accuracy"):
        if not isinstance(metrics.get(key), float) or not math.isfinite(metrics[key]):
            raise SystemExit(f"Invalid metric {key}.")
    if not 0.0 <= metrics["validation_accuracy"] <= 1.0:
        raise SystemExit("Validation accuracy is outside [0, 1].")

    env = checkpoint["environment"]
    if not str(env.get("python_version", "")).startswith("3.10."):
        raise SystemExit("Checkpoint was not produced with Python 3.10.x.")
    if not str(env.get("torch_version", "")).startswith(REQUIRED_TORCH):
        raise SystemExit("Checkpoint PyTorch version does not match the contract.")
    if env.get("numpy_version") != REQUIRED_NUMPY or env.get("torch_cuda") is not None:
        raise SystemExit("Checkpoint environment footprint does not match the contract.")

    repo_id = repository_id(repository)
    if checkpoint["assignment"] != {"repository_id": repo_id, "seed": assignment_seed(repo_id)}:
        raise SystemExit("Checkpoint assignment identity is invalid.")
    if checkpoint["native"].get("api_version") != api_version():
        raise SystemExit("Checkpoint native API version is invalid.")

    model = TinyClassifier()
    model.load_state_dict(checkpoint["model_state_dict"], strict=True)
    for name, tensor in checkpoint["model_state_dict"].items():
        if tensor.device.type != "cpu":
            raise SystemExit(f"{name} is not on CPU.")
        if not torch.isfinite(tensor).all():
            raise SystemExit(f"{name} contains NaN or Inf.")

    expected_fingerprints = {
        "source_sha256": source_fingerprint(),
        "config_sha256": config_fingerprint(),
        "state_sha256": state_fingerprint(checkpoint["model_state_dict"]),
    }
    if checkpoint["fingerprints"] != expected_fingerprints:
        raise SystemExit("Checkpoint fingerprints do not match the current tree.")
    return checkpoint


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    validate = sub.add_parser("validate")
    validate.add_argument("checkpoint", type=Path)
    validate.add_argument("--repository-id")
    args = parser.parse_args(argv)
    if args.command == "validate":
        validate_checkpoint(args.checkpoint, args.repository_id)
        print("checkpoint valid")


if __name__ == "__main__":
    main()
