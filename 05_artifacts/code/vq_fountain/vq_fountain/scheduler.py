"""Token scheduling helpers for the VQ-Fountain prototype."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import math
import random


@dataclass(frozen=True)
class TokenCandidate:
    token_id: int
    probability: float
    stability: float = 1.0


@dataclass(frozen=True)
class TokenBin:
    bin_id: int
    candidates: tuple[TokenCandidate, ...]
    mass: float


@dataclass(frozen=True)
class TokenDecision:
    token_id: int
    payload_value: int
    capacity_bits: int
    bin_mass: float
    target_mass: float
    leakage_score: float


def entropy(probs: list[float] | tuple[float, ...]) -> float:
    """Shannon entropy in bits."""

    total = sum(probs)
    if total <= 0:
        raise ValueError("probability mass must be positive")
    value = 0.0
    for probability in probs:
        if probability < 0:
            raise ValueError("probabilities must be non-negative")
        if probability == 0:
            continue
        normalized = probability / total
        value -= normalized * math.log2(normalized)
    return value


def keyed_order(items: list[int], key: int | str, context: str) -> list[int]:
    """Return a deterministic pseudo-random ordering for schedule positions."""

    def score(item: int) -> bytes:
        return hashlib.sha256(f"{key}:{context}:{item}".encode("utf-8")).digest()

    return sorted(items, key=score)


def select_positions(
    entropies: list[float],
    stabilities: list[float],
    key: int | str,
    min_entropy: float,
    min_stability: float,
    limit: int | None = None,
) -> list[int]:
    """Select token positions that are both high-entropy and stable."""

    if len(entropies) != len(stabilities):
        raise ValueError("entropies and stabilities must have the same length")

    candidates = [
        index
        for index, (item_entropy, stability) in enumerate(zip(entropies, stabilities))
        if item_entropy >= min_entropy and stability >= min_stability
    ]
    ordered = keyed_order(candidates, key=key, context="positions")
    if limit is None:
        return ordered
    return ordered[:limit]


def partition_candidates(candidates: list[TokenCandidate], capacity_bits: int) -> list[TokenBin]:
    """Partition candidates into probability-balanced bins."""

    if capacity_bits <= 0:
        raise ValueError("capacity_bits must be positive")
    bin_count = 1 << capacity_bits
    if len(candidates) < bin_count:
        raise ValueError("not enough candidates for requested capacity")

    normalized = _normalize_candidates(candidates)
    bins: list[list[TokenCandidate]] = [[] for _ in range(bin_count)]
    masses = [0.0 for _ in range(bin_count)]

    for candidate in sorted(normalized, key=lambda item: item.probability, reverse=True):
        target = min(range(bin_count), key=lambda index: masses[index])
        bins[target].append(candidate)
        masses[target] += candidate.probability

    return [
        TokenBin(bin_id=index, candidates=tuple(items), mass=masses[index])
        for index, items in enumerate(bins)
    ]


def choose_token(
    candidates: list[TokenCandidate],
    payload_value: int,
    capacity_bits: int,
    key: int | str,
    position: int,
) -> TokenDecision:
    """Choose a token from the payload-selected bin with weighted sampling."""

    bin_count = 1 << capacity_bits
    if payload_value < 0 or payload_value >= bin_count:
        raise ValueError("payload_value outside representable range")

    bins = partition_candidates(candidates, capacity_bits)
    selected_bin = bins[payload_value]
    if not selected_bin.candidates:
        raise ValueError("selected bin is empty")

    rng = _rng_for_decision(key=key, position=position, payload_value=payload_value)
    token_id = _weighted_choice(selected_bin.candidates, rng)
    target_mass = 1.0 / bin_count
    leakage_score = abs(selected_bin.mass - target_mass)
    return TokenDecision(
        token_id=token_id,
        payload_value=payload_value,
        capacity_bits=capacity_bits,
        bin_mass=selected_bin.mass,
        target_mass=target_mass,
        leakage_score=leakage_score,
    )


def _normalize_candidates(candidates: list[TokenCandidate]) -> list[TokenCandidate]:
    if not candidates:
        raise ValueError("candidates must not be empty")
    total = sum(candidate.probability for candidate in candidates)
    if total <= 0:
        raise ValueError("candidate probability mass must be positive")
    normalized: list[TokenCandidate] = []
    for candidate in candidates:
        if candidate.probability < 0:
            raise ValueError("candidate probabilities must be non-negative")
        normalized.append(
            TokenCandidate(
                token_id=candidate.token_id,
                probability=candidate.probability / total,
                stability=candidate.stability,
            )
        )
    return normalized


def _rng_for_decision(key: int | str, position: int, payload_value: int) -> random.Random:
    digest = hashlib.sha256(f"{key}:token:{position}:{payload_value}".encode("utf-8")).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def _weighted_choice(candidates: tuple[TokenCandidate, ...], rng: random.Random) -> int:
    total = sum(candidate.probability for candidate in candidates)
    draw = rng.random() * total
    cumulative = 0.0
    for candidate in candidates:
        cumulative += candidate.probability
        if draw <= cumulative:
            return candidate.token_id
    return candidates[-1].token_id
