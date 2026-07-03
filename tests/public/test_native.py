import numpy as np
import pytest

from hybridml.native import NativeError, api_version, standardize_features


def test_api_version():
    assert api_version() == 1


def test_standardize_features_matches_numpy():
    x = np.array([[1, 2], [3, 2], [5, 2]], dtype=np.float32)
    y = standardize_features(x)
    expected = (x - x.mean(axis=0)) / np.maximum(x.std(axis=0), 1e-6)
    np.testing.assert_allclose(y, expected, rtol=1e-5, atol=1e-6)


def test_noncontiguous_input_is_accepted():
    x = np.arange(12, dtype=np.float32).reshape(3, 4)[:, ::2]
    y = standardize_features(x)
    assert y.flags.c_contiguous


def test_non_2d_rejected():
    with pytest.raises(ValueError):
        standardize_features(np.array([1, 2, 3], dtype=np.float32))


def test_invalid_epsilon_raises_native_error():
    with pytest.raises(NativeError):
        standardize_features(np.ones((2, 2), dtype=np.float32), epsilon=0.0)
    with pytest.raises(NativeError):
        standardize_features(np.ones((2, 2), dtype=np.float32), epsilon=float('nan'))
