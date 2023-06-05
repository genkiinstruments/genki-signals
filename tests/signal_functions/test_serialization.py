import pytest
import numpy as np

from genki_signals.functions import FourierTransform, Stack
from genki_signals.functions.serialization import encode_signal_fn, decode_signal_fn


@pytest.mark.parametrize(
    "input_class",
    [
        (
            FourierTransform(
                "audio",
                name="fourier",
                window_size=256,
                window_overlap=0,
                detrend_type="linear",
                window_type="hann",
            )
        ),
        (
            Stack(
                "signal1",
                "signal2",
                "signal3",
                name="out",
                axis=3,
            )
        ),
    ],
)
def test_serialization(input_class):
    encoded_class = encode_signal_fn(input_class)
    output_class = decode_signal_fn(encoded_class)
    np.testing.assert_equal(input_class.input_signals, output_class.input_signals)
    np.testing.assert_equal(input_class.name, output_class.name)
    np.testing.assert_equal(input_class.params, output_class.params)
