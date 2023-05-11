import pytest
import numpy as np

from genki_signals.signal_functions.shape import *


@pytest.mark.parametrize(
    "input_data, dim, expected",
    [
        (np.array([[1,2], [3,4]]), 0, np.array([[1,2]])),
        (np.array([[1,2], [3,4]]), 1, np.array([[3,4]])),
        (np.array([[[1,2], [3,4]], [[5,6], [7,8]]]), 0, np.array([[1,2], [3,4]])),
    ]
)
def test_extract_dimension(input_data, dim, expected):
    extract_dim = ExtractDimension("input_signal", name="ExtractDimension", dim=dim)
    result = extract_dim(input_data)
    np.testing.assert_array_equal(result, expected)


