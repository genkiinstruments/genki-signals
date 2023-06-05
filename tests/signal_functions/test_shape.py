import pytest
import numpy as np

import genki_signals.functions as sf
from genki_signals.functions.shape import *
from genki_signals.buffers import DataBuffer


@pytest.mark.parametrize(
    "dim, input_data, expected",
    [
        (0, np.array([[1, 2], [3, 4]]), np.array([1, 2])),
        (1, np.array([[1, 2], [3, 4]]), np.array([3, 4])),
        (0, np.array([[[1, 2], [3, 4]], [[5, 6], [7, 8]]]), np.array([[1, 2], [3, 4]])),
        ((0, 0), np.array([[[1, 2], [3, 4]], [[5, 6], [7, 8]]]), np.array([1, 2])),
    ],
)
def test_extract_dimension(input_data, dim, expected):
    extract_dim = ExtractDimension("input_signal", name="ExtractDimension", dim=dim)
    result = extract_dim(input_data)
    np.testing.assert_array_equal(result, expected)


@pytest.mark.parametrize(
    "dim, input_data",
    [
        (0, np.array([1, 2])),
        ((0, 0), np.array([[1, 2]])),
    ],
)
def test_extract_dimension_shape_mismatch(dim, input_data):
    extract_dim = ExtractDimension("input_signal", name="ExtractDimension", dim=dim)
    with pytest.raises(ValueError):
        extract_dim(input_data)


@pytest.mark.parametrize(
    "axis, input_data, expected",
    [
        (0, [np.array([1, 2]), np.array([3, 4])], np.array([[1, 2], [3, 4]])),
        (0, [np.array([[1, 2]]), np.array([[3, 4]])], np.array([[1, 2], [3, 4]])),
        (0, [np.array([[1, 2], [3, 4]]), np.array([[5, 6]])], np.array([[1, 2], [3, 4], [5, 6]])),
    ],
)
def test_concatenate(axis, input_data, expected):
    concatenate = Concatenate("input_signal", name="Concatenate", axis=axis)
    result = concatenate(*input_data)
    np.testing.assert_array_equal(result, expected)


@pytest.mark.parametrize(
    "axis, input_data",
    [
        (0, [np.array([[1, 2, 3]]), np.array([[4, 5]])]),
        (0, [np.array([[1, 2], [3, 4]]), np.array([[5, 6, 7]])]),
        (1, [np.array([1, 2]), np.array([3, 4])]),
        (1, [np.array([[1, 2]]), np.array([[3, 4]])]),
    ],
)
def test_concatenate_shape_mismatch(axis, input_data):
    concatenate = Concatenate("input_signal", name="Concatenate", axis=axis)
    with pytest.raises(ValueError):
        concatenate(*input_data)


@pytest.mark.parametrize(
    "axis, input_data, expected",
    [
        (0, [np.array([1, 2]), np.array([3, 4])], np.array([[1, 2], [3, 4]])),
        (0, [np.array([[1], [2]]), np.array([[3], [4]])], np.array([[[1], [2]], [[3], [4]]])),
        (1, [np.array([[1], [2]]), np.array([[3], [4]])], np.array([[[1], [3]], [[2], [4]]])),
        (0, [np.array([[1, 2]]), np.array([[3, 4]])], np.array([[[1, 2]], [[3, 4]]])),
        (1, [np.array([[1, 2]]), np.array([[3, 4]])], np.array([[[1, 2], [3, 4]]])),
    ],
)
def test_stack(axis, input_data, expected):
    stack = Stack("input_signal", name="Stack", axis=axis)
    result = stack(*input_data)
    np.testing.assert_array_equal(result, expected)


@pytest.mark.parametrize(
    "axis, input_data",
    [
        (1, [np.array([1, 2]), np.array([3, 4])]),
        (-1, [np.array([1, 2]), np.array([3, 4])]),
        (2, [np.array([[1, 2]]), np.array([[3, 4]])]),
    ],
)
def test_stack_time_axis(axis, input_data):
    stack = Stack("input_signal", name="Stack", axis=axis)
    with pytest.raises(ValueError):
        stack(*input_data)


@pytest.mark.parametrize(
    "shape, input_data, expected",
    [
        ((2, 2), np.arange(40).reshape((4, 10)), np.arange(40).reshape((2, 2, 10))),
        ((4,), np.arange(40).reshape((4, 10)), np.arange(40).reshape((4, 10))),
        ((4,), np.arange(40).reshape((2, 2, 10)), np.arange(40).reshape((4, 10))),
        ((-1,), np.arange(40).reshape((2, 2, 10)), np.arange(40).reshape((4, 10))),
    ],
)
def test_reshape(shape, input_data, expected):
    reshape = Reshape("input_signal", name="Reshape", shape=shape)
    result = reshape(input_data)
    np.testing.assert_array_equal(result, expected)


@pytest.mark.parametrize(
    "shape, input_data",
    [
        ((5,), np.arange(40).reshape((4, 10))),
        ((4, 2), np.arange(40).reshape((2, 2, 10))),
    ],
)
def test_reshape_shape_mismatch(shape, input_data):
    reshape = Reshape("input_signal", name="Reshape", shape=shape)
    with pytest.raises(ValueError):
        reshape(input_data)


def test_combine():
    signal_fns = [
        sf.Differentiate("a", input_b="timestamp", name="a_prime"),
        sf.Sum("a_prime", "b", name="sum_a_b"),
        sf.Norm("sum_a_b", name="normed"),
        Combine(
            [
                sf.Differentiate("a", input_b="timestamp", name="a_prime_internal"),
                sf.Sum("a_prime", "b", name="sum_a_b_internal"),
                sf.Norm("sum_a_b", name="normed_internal"),
            ],
            name="combined",
        ),
    ]
    data = DataBuffer(data={"a": np.array([10, 20, 40]), "b": np.array([40, 50, 60]), "timestamp": np.array([1, 2, 3])})
    result = sf.compute_signal_functions(data, signal_fns)
    assert np.allclose(result["normed"], result["combined"])
