import torch
import torch.nn.functional as F


def _luma(x):
    weights = x.new_tensor([0.299, 0.587, 0.114]).view(1, 3, 1, 1)
    return (x * weights).sum(dim=1, keepdim=True)


def _residuals(x):
    horizontal = x[:, :, :, 1:] - x[:, :, :, :-1]
    vertical = x[:, :, 1:, :] - x[:, :, :-1, :]
    diagonal = x[:, :, 1:, 1:] - x[:, :, :-1, :-1]
    anti_diagonal = x[:, :, 1:, :-1] - x[:, :, :-1, 1:]
    return horizontal, vertical, diagonal, anti_diagonal


def _feature_vector(x):
    streams = [x, _luma(x)]
    features = []
    for stream in streams:
        for residual in _residuals(stream):
            abs_residual = residual.abs()
            dims = tuple(range(2, residual.ndim))
            features.extend(
                [
                    abs_residual.mean(dim=dims),
                    abs_residual.std(dim=dims, unbiased=False),
                    residual.square().mean(dim=dims),
                ]
            )
    return torch.cat(features, dim=1)


def residual_statistics_loss(cover, stego):
    """Differentiable residual-statistics matching loss.

    This is a lightweight, trainable proxy for the residual/LSB sanity detector.
    It does not prove steganographic security; it only discourages obvious
    first- and second-order residual-statistic shifts.
    """

    cover_features = _feature_vector(cover).detach()
    stego_features = _feature_vector(stego)
    return F.l1_loss(stego_features, cover_features)
