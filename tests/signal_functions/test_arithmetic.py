import pytest
import numpy as np
from genki_signals.functions.arithmetic import Sum, Difference, Scale, Integrate


@pytest.mark.parametrize(
    "input_data, scale_factor, expected",
    [
        (np.array([1, 2, 3]), 1.0, np.array([1, 2, 3])),
        (np.array([2.4]), 3.1, np.array([7.44])),
        (np.array([[1.0, 2.5], [-6.0, -1]]), 2.0, np.array([[2.0, 5.0], [-12.0, -2]])),
        (np.array([2.0, 1000.0]), 0, np.array([0, 0])),
    ],
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
            np.array([[0, 6.5], [-3.0, -1]]),
        ),
    ],
)
def test_sum(input_data, expected):
    func = Sum("input_data", name="output_data")
    result = func(*input_data)
    np.testing.assert_equal(result, expected)


@pytest.mark.parametrize(
    "input_data",
    [
        ((np.array([[1.0, 2.0, 4.0], [-6.0, -1, 0]]), np.array([8, 1]))),
    ],
)
def test_sum_shape_mismatch(input_data):
    func = Sum("input_data", name="output_data")
    with pytest.raises(Exception):
        func(*input_data)


@pytest.mark.parametrize(
    "input_a, input_b, expected",
    [
        (np.array([1]), np.array([2]), np.array([-1])),
        (np.array([[1.0, 2.5], [-6.0, -1]]), np.array([[-1.0, 4.0], [3.0, 0]]), np.array([[2, -1.5], [-9.0, -1]])),
    ],
)
def test_difference(input_a, input_b, expected):
    func = Difference("input_a", "input_b", name="output_data")
    result = func(*(input_a, input_b))
    np.testing.assert_equal(result, expected)


@pytest.mark.parametrize(
    "input_a, input_b",
    [
        (np.array([[1.0, 2.0, 4.0], [-6.0, -1, 0]]), np.array([8, 1])),
    ],
)
def test_difference_shape_mismatch(input_a, input_b):
    func = Difference("input_a", "input_b", name="output_data")
    with pytest.raises(Exception):
        func(*(input_a, input_b))


@pytest.mark.parametrize(
    "inputs, use_trapz, expected",
    [
        (
            (np.ones(100), np.arange(100)),
            True,
            np.arange(100),
        ),
        (
            (np.array([1, 2, 10]), np.array([0, 1, 2])),
            True,
            np.array([0, 1.5, 7.5]),
        ),
        (
            (np.array([1, 2, 3]), np.array([0, 1, 101])),
            False,
            np.array([0, 2, 302]),
        ),
        (
            (np.array([[1, 2, 3], [1, 2, 4], [1, 4, 9]]), np.array([0, 1, 2])),
            False,
            np.array([[0, 2, 5], [0, 2, 6], [0, 4, 13]]),
        ),
    ],
)
def test_integrate(inputs, use_trapz, expected):
    func = Integrate("input_a", "input_b", name="output_data", use_trapz=use_trapz)
    result = func(*(inputs))
    np.testing.assert_equal(result, expected)


@pytest.mark.parametrize(
    "use_trapz",
    [
        (True),
        (False),
    ],
)
def test_integrate_state(use_trapz):
    sample_count = 1000
    lmbda = 3
    attribute_count = 3

    input_a = np.random.rand(attribute_count, sample_count) * 1000
    input_b = np.sort(np.random.rand(attribute_count, sample_count)) * 1000

    func = Integrate("input_a", "input_b", name="output_data", use_trapz=use_trapz)
    result_batched = func(input_a, input_b)

    func = Integrate("input_a", "input_b", name="output_data", use_trapz=use_trapz)
    result_seq = []
    i = 0
    while i < sample_count:
        next_i = i + np.random.poisson(lam=lmbda) + 1
        if i < 2:
            print(next_i)
        result = func(input_a[..., i:next_i], input_b[..., i:next_i])
        if i < 2:
            print(result, func.last_b, func.state)
        result_seq.append(result)
        i = next_i

    result_seq = np.concatenate(result_seq, axis=-1)
    np.testing.assert_almost_equal(result_batched, result_seq)
