import pytest
import numpy as np

from genki_signals.functions.geometry import Norm


@pytest.mark.parametrize(
    "input_data, order, expected",
    [
        (np.array([1, 2, 3]), 1.0, np.array([1, 2, 3])),
        (np.array([[1.0, 2.5], [-6.0, -1]]), 1, np.array([7.0, 3.5])),
        (np.array([[1.0, 2.5], [-6.0, -1]]), 2, np.array([np.sqrt(37.0), np.sqrt(7.25)])),
        (np.array([[1.0, 2.5], [-6.0, -1]]), None, np.array([np.sqrt(37.0), np.sqrt(7.25)])),
        (np.array([[0.0, 3.0], [6.0, 1.0]]), 0, np.array([1, 2])),
        (np.array([[1.0, 2.5], [-6.0, -1]]), np.inf, np.array([6.0, 2.5])),
        (np.array([[1.0, 2.5], [-6.0, -1.5]]), -np.inf, np.array([1.0, 1.5])),
    ]
)
def test_norm(input_data, order, expected):
    func = Norm("input_data", name="output_data", order=order)
    result = func(*(input_data,))
    np.testing.assert_almost_equal(result, expected)



