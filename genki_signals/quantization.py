import torch


QUANT_LEVELS = 257


def linear_quant_encode(x, num_levels=QUANT_LEVELS):
    """Linearly quantize a signal in [-1, 1] to `num_levels`

    Examples:
        >>> linear_quant_encode(torch.tensor([-1.0, 0.0, 1.0, 0.1, -0.9]), 21)
        tensor([ 0, 10, 20, 11,  1], dtype=torch.int32)
    """
    assert (
        num_levels % 2 == 1
    ), f"Expected odd (to make sure 0 maps to 0), got {num_levels=}"
    assert torch.max(x) <= 1.0
    assert torch.min(x) >= -1.0

    return torch.round((x + 1) / 2 * (num_levels - 1)).int()


def linear_quant_decode(sig, num_levels=QUANT_LEVELS):
    """Reconstruct a linearly quantized signal in from `num_levels` to [-1, 1]

    Examples:
        >>> linear_quant_decode(torch.tensor([0, 10, 20, 11, 1]), 21)
        tensor([-1.0000,  0.0000,  1.0000,  0.1000, -0.9000])
    """
    assert torch.max(sig) <= num_levels - 1
    sig = sig.float()
    return (sig / (num_levels - 1) - 1 / 2) * 2


def mu_law_encode(x, num_levels=QUANT_LEVELS):
    """Compress the dynamic range of a signal using mu law

    Examples:
        >>> mu_law_encode(torch.tensor([-1.0, -0.1, -0.01, 0.0, 0.01, 0.1, 1.0]))
        tensor([-1.0000, -0.5913, -0.2288,  0.0000,  0.2288,  0.5913,  1.0000])
    """
    mu = num_levels - 1
    assert torch.max(x) <= 1.0
    assert torch.min(x) >= -1.0

    device = x.get_device() if x.is_cuda else None

    mag = torch.log(1 + mu * torch.abs(x)) / torch.log(
        torch.tensor([1 + mu], device=device)
    )
    sig = torch.sign(x) * mag
    return sig


def mu_law_decode(y, num_levels=QUANT_LEVELS):
    """Decompress a signal that has been encoded using mu law

    Examples:
        >>> mu_law_decode(torch.tensor([-1.0000, -0.5913, -0.2288,  0.0000,  0.2288,  0.5913,  1.0000]))
        tensor([-1.0000, -0.1000, -0.0100,  0.0000,  0.0100,  0.1000,  1.0000])
    """
    mu = num_levels - 1
    return torch.sign(y) * ((mu + 1) ** torch.abs(y) - 1) / mu


def mu_law_and_quant_encode(x, num_levels=QUANT_LEVELS):
    y = mu_law_encode(x, num_levels)
    y = linear_quant_encode(y, num_levels)
    return y


def mu_law_and_quant_decode(y, num_levels=QUANT_LEVELS):
    y = linear_quant_decode(y, num_levels)
    x = mu_law_decode(y, num_levels)
    return x


def squish_encode(x, max_val, clamp=True):
    """Squish a signal from [-max_val, max_val] to [-1, 1], clamps values outside the range

    Examples:
        >>> squish_encode(torch.tensor([2.0, 10.0, -1.0, -9]), 8)
        tensor([ 0.2500,  1.0000, -0.1250, -1.0000])
    """
    assert max_val > 0.0
    y = torch.clamp(x, min=-max_val, max=max_val) if clamp else x
    y = y / max_val
    return y


def squish_decode(y, max_val):
    """Unsquish signal from [-1, 1] to [-max_val, max_val]

    Examples:
        >>> squish_decode(torch.tensor([ 0.25 ,  1.   , -0.125, -1.   ]), 8)
        tensor([ 2.,  8., -1., -8.])
    """
    return y * max_val
