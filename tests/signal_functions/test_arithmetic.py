import pytest
import numpy as np
from genki_signals.functions.arithmetic import Sum, Difference, Scale


@pytest.mark.parametrize(
    "input_data, scale_factor, expected",
    [
        (np.array([1, 2, 3]), 1.0, np.array([1, 2, 3])),
        (np.array([2.4]), 3.1, np.array([7.44])),
        (
            np.array([[1.0, 2.5], [-6.0, -1]]),
            2.0,
            np.array([[2.0, 5.0], [-12.0, -2]])
        ),
        (np.array([2.0, 1000.0]), 0, np.array([0, 0]))
    ]
)
def test_scale(input_data, scale_factor, expected):
    func = Scale("input_data", name="output_data", scale_factor=scale_factor)
    result = func(input_data)
    np.testing.assert_almost_equal(result, expected)


@pytest.mark.parametrize(
    "input_data, expected",
    [
        ((np.array([1, 2, 3]),), np.array([1, 2, 3])),
        ((np.array([1]), np.array([2]), np.array([3])), np.array([6])),
        (
            (
                np.array([[1.0, 2.5], [-6.0, -1]]),
                np.array([[-1.0, 4.0], [3.0, 0]]),
            ),
            np.array([[0, 6.5], [-3.0, -1]])
        )
    ]
)
def test_sum(input_data, expected):
    func = Sum("input_data", name="output_data")
    result = func(*input_data)
    np.testing.assert_equal(result, expected)


@pytest.mark.parametrize(
    "input_data",
    [
        ((np.array([[1.0, 2.0, 4.0], [-6.0, -1, 0]]), np.array([8, 1]))),
    ]
)
def test_sum_shape_mismatch(input_data):
    func = Sum("input_data", name="output_data")
    with pytest.raises(Exception):
        func(*input_data)


@pytest.mark.parametrize(
    "input_a, input_b, expected",
    [
        (np.array([1]), np.array([2]), np.array([-1])),
        (
            np.array([[1.0, 2.5], [-6.0, -1]]),
            np.array([[-1.0, 4.0], [3.0, 0]]),
            np.array([[2, -1.5], [-9.0, -1]])
        )
    ]
)
def test_difference(input_a, input_b, expected):
    func = Difference("input_a", "input_b", name="output_data")
    result = func(*(input_a, input_b))
    np.testing.assert_equal(result, expected)


@pytest.mark.parametrize(
    "input_a, input_b",
    [
        (np.array([[1.0, 2.0, 4.0], [-6.0, -1, 0]]), np.array([8, 1])),
    ]
)
def test_difference_shape_mismatch(input_a, input_b):
    func = Difference("input_a", "input_b", name="output_data")
    with pytest.raises(Exception):
        func(*(input_a, input_b))
