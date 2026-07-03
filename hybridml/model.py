from __future__ import annotations

import torch
from torch import nn


class TinyClassifier(nn.Module):
    def __init__(self, input_dim: int = 12, hidden_dim: int = 24, classes: int = 3):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)
