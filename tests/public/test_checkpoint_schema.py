from pathlib import Path

from hybridml.checkpoint import validate_checkpoint


def test_checkpoint_schema_if_present():
    path = Path("artifacts/model.ckpt")
    if path.exists():
        validate_checkpoint(path)
