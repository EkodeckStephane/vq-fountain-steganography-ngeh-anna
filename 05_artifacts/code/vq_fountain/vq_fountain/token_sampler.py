"""Distribution-aware token sampling primitives."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import math
import random

import numpy as np


@dataclass(frozen=True)
class TokenSample:
    token_id: int
    value: int
    bin_mass: float
    target_mass: float
    leakage_score: float


class PriorBinCodec:
    """Map bit values to global codebook bins with balanced prior mass."""

    def __init__(
        self,
        prior: np.ndarray,
        capacity_bits: int,
        codebook: np.ndarray | None = None,
        mode: str = "projection",
    ) -> None:
        if capacity_bits <= 0:
            raise ValueError("capacity_bits must be positive")
        if capacity_bits > 8:
            raise ValueError("capacity_bits above 8 is not supported in this prototype")

        prior = np.asarray(prior, dtype=np.float64)
        if prior.ndim != 1:
            raise ValueError("prior must be a vector")
        if np.any(prior < 0):
            raise ValueError("prior must be non-negative")
        total = float(prior.sum())
        if total <= 0:
            raise ValueError("prior has no mass")

        self.prior = prior / total
        self.capacity_bits = capacity_bits
        self.bin_count = 1 << capacity_bits
        self.target_mass = 1.0 / self.bin_count
        self.mode = mode
        self.bin_for_token = np.full(self.prior.shape[0], -1, dtype=np.int32)
        self.tokens_by_bin: list[np.ndarray] = []
        self.mass_by_bin: list[float] = []

        if mode == "naive":
            self._build_naive_bins()
        else:
            order = self._token_order(codebook=codebook, mode=mode)
            self._build_bins(order)

    def sample_token(self, value: int, key: int | str, position: int) -> TokenSample:
        if value < 0 or value >= self.bin_count:
            raise ValueError("value outside bin range")
        tokens = self.tokens_by_bin[value]
        if tokens.size == 0:
            raise ValueError("selected bin has no tokens")
        weights = self.prior[tokens]
        weights = weights / weights.sum()
        rng = random.Random(_seed_to_int(f"{key}:sample:{position}:{value}"))
        draw = rng.random()
        cumulative = 0.0
        selected = int(tokens[-1])
        for token_id, weight in zip(tokens.tolist(), weights.tolist()):
            cumulative += weight
            if draw <= cumulative:
                selected = int(token_id)
                break

        bin_mass = self.mass_by_bin[value]
        return TokenSample(
            token_id=selected,
            value=value,
            bin_mass=bin_mass,
            target_mass=self.target_mass,
            leakage_score=abs(bin_mass - self.target_mass),
        )

    def decode_value(self, token_id: int) -> int:
        if token_id < 0 or token_id >= self.bin_for_token.shape[0]:
            raise ValueError("token_id outside codebook range")
        value = int(self.bin_for_token[token_id])
        if value < 0:
            raise ValueError("token_id is not assigned to a bin")
        return value

    def _token_order(self, codebook: np.ndarray | None, mode: str) -> np.ndarray:
        token_count = self.prior.shape[0]
        if mode == "mass":
            return np.argsort(-self.prior)
        if mode != "projection":
            raise ValueError(f"unsupported binning mode: {mode}")
        if codebook is None:
            return np.arange(token_count, dtype=np.int32)
        if codebook.shape[0] != token_count:
            raise ValueError("codebook size does not match prior length")
        patch_means = codebook.reshape(token_count, -1, 3).mean(axis=1)
        luminance = 0.2126 * patch_means[:, 0] + 0.7152 * patch_means[:, 1] + 0.0722 * patch_means[:, 2]
        return np.argsort(luminance)

    def _build_bins(self, order: np.ndarray) -> None:
        bins: list[list[int]] = [[] for _ in range(self.bin_count)]
        masses = [0.0 for _ in range(self.bin_count)]
        current = 0
        for token_id in order.tolist():
            token_id = int(token_id)
            if current < self.bin_count - 1 and masses[current] >= self.target_mass and bins[current]:
                current += 1
            bins[current].append(token_id)
            masses[current] += float(self.prior[token_id])

        for bin_id, token_ids in enumerate(bins):
            tokens = np.asarray(token_ids, dtype=np.int32)
            self.tokens_by_bin.append(tokens)
            self.mass_by_bin.append(float(masses[bin_id]))
            for token_id in token_ids:
                self.bin_for_token[token_id] = bin_id

    def _build_naive_bins(self) -> None:
        bins: list[list[int]] = [[] for _ in range(self.bin_count)]
        masses = [0.0 for _ in range(self.bin_count)]
        for token_id in range(self.prior.shape[0]):
            bin_id = token_id % self.bin_count
            bins[bin_id].append(token_id)
            masses[bin_id] += float(self.prior[token_id])

        for bin_id, token_ids in enumerate(bins):
            tokens = np.asarray(token_ids, dtype=np.int32)
            self.tokens_by_bin.append(tokens)
            self.mass_by_bin.append(float(masses[bin_id]))
            for token_id in token_ids:
                self.bin_for_token[token_id] = bin_id


def bytes_to_values(data: bytes, capacity_bits: int) -> list[int]:
    if capacity_bits <= 0:
        raise ValueError("capacity_bits must be positive")
    bits = []
    for byte in data:
        for shift in range(7, -1, -1):
            bits.append((byte >> shift) & 1)
    values: list[int] = []
    for start in range(0, len(bits), capacity_bits):
        chunk = bits[start : start + capacity_bits]
        if len(chunk) < capacity_bits:
            chunk.extend([0] * (capacity_bits - len(chunk)))
        value = 0
        for bit in chunk:
            value = (value << 1) | bit
        values.append(value)
    return values


def values_to_bytes(values: list[int], capacity_bits: int, output_size: int) -> bytes:
    bits: list[int] = []
    max_value = 1 << capacity_bits
    for value in values:
        if value < 0 or value >= max_value:
            raise ValueError("value outside representable range")
        for shift in range(capacity_bits - 1, -1, -1):
            bits.append((value >> shift) & 1)

    output_bits = output_size * 8
    bits = bits[:output_bits]
    if len(bits) < output_bits:
        bits.extend([0] * (output_bits - len(bits)))

    out = bytearray()
    for start in range(0, output_bits, 8):
        byte = 0
        for bit in bits[start : start + 8]:
            byte = (byte << 1) | bit
        out.append(byte)
    return bytes(out)


def sample_prior_token(prior: np.ndarray, key: int | str, position: int) -> int:
    weights = np.asarray(prior, dtype=np.float64)
    weights = weights / weights.sum()
    rng = random.Random(_seed_to_int(f"{key}:prior:{position}"))
    draw = rng.random()
    cumulative = 0.0
    selected = int(weights.shape[0] - 1)
    for token_id, weight in enumerate(weights.tolist()):
        cumulative += weight
        if draw <= cumulative:
            selected = token_id
            break
    return selected


def mean_entropy_per_token(capacity_bits: int) -> float:
    return math.log2(1 << capacity_bits)


def _seed_to_int(value: str) -> int:
    digest = hashlib.sha256(value.encode("utf-8")).digest()
    return int.from_bytes(digest[:16], "big")
