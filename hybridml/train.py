from __future__ import annotations

import os
import random
from pathlib import Path

import numpy as np
import torch
import tomli

from hybridml.data import assignment_seed, make_dataset, repository_id
from hybridml.environment import verify_environment
from hybridml.fingerprint import config_fingerprint, source_fingerprint, state_fingerprint
from hybridml.model import TinyClassifier
from hybridml.native import api_version, standardize_features

ROOT = Path(__file__).resolve().parents[1]


def train(checkpoint_path: Path = ROOT / "artifacts" / "model.ckpt") -> dict:
    config = tomli.loads((ROOT / "config" / "train.toml").read_text(encoding="utf-8"))
    repo_id = repository_id()
    seed = assignment_seed(repo_id)
    os.environ["OMP_NUM_THREADS"] = "1"
    os.environ["MKL_NUM_THREADS"] = "1"
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.set_num_threads(int(config["execution"]["num_threads"]))
    torch.use_deterministic_algorithms(bool(config["execution"]["deterministic"]))

    x_np, y_np = make_dataset(seed)
    x_np = standardize_features(x_np)
    split = int(0.8 * len(y_np))
    x = torch.tensor(x_np, dtype=torch.float32)
    y = torch.tensor(y_np, dtype=torch.long)
    train_x, val_x = x[:split], x[split:]
    train_y, val_y = y[:split], y[split:]

    model = TinyClassifier()
    optimizer = torch.optim.SGD(model.parameters(), lr=float(config["training"]["learning_rate"]))
    epochs = int(config["training"]["epochs"])
    train_loss = torch.tensor(float("nan"))
    for _ in range(epochs):
        optimizer.zero_grad()
        logits = model(train_x)
        train_loss = torch.nn.functional.cross_entropy(logits, train_y)
        train_loss.backward()
        optimizer.step()

    with torch.no_grad():
        validation_accuracy = (model(val_x).argmax(dim=1) == val_y).float().mean().item()

    state = {name: tensor.detach().cpu() for name, tensor in model.state_dict().items()}
    checkpoint = {
        "schema_version": 1,
        "model_state_dict": state,
        "epoch": epochs,
        "metrics": {
            "train_loss": float(train_loss.item()),
            "validation_accuracy": float(validation_accuracy),
        },
        "environment": verify_environment(),
        "assignment": {"repository_id": repo_id, "seed": seed},
        "native": {"api_version": api_version()},
        "fingerprints": {
            "source_sha256": source_fingerprint(),
            "config_sha256": config_fingerprint(),
            "state_sha256": state_fingerprint(state),
        },
    }
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(checkpoint, checkpoint_path)
    return checkpoint


def main() -> None:
    checkpoint = train()
    print("wrote artifacts/model.ckpt")
    print(f"validation_accuracy={checkpoint['metrics']['validation_accuracy']:.4f}")


if __name__ == "__main__":
    main()
