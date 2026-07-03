from hybridml.environment import verify_environment


def test_environment_contract():
    info = verify_environment()
    assert info["torch_cuda"] is None
    assert info["environment_lock_sha256"]
