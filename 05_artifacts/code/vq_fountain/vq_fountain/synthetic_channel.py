"""Synthetic channel used before connecting real image/token models."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import random

from .fountain import FountainSymbol


@dataclass(frozen=True)
class SyntheticChannelConfig:
    symbol_erasure_rate: float = 0.0
    bit_flip_rate: float = 0.0
    seed: int | str = 0


def transmit_symbols(symbols: list[FountainSymbol], config: SyntheticChannelConfig) -> list[FountainSymbol]:
    """Apply symbol erasures and byte-level bit flips."""

    _validate_rate(config.symbol_erasure_rate, "symbol_erasure_rate")
    _validate_rate(config.bit_flip_rate, "bit_flip_rate")

    delivered: list[FountainSymbol] = []
    for symbol in symbols:
        rng = _symbol_rng(config.seed, symbol.symbol_id)
        if rng.random() < config.symbol_erasure_rate:
            continue
        delivered.append(_maybe_flip_bits(symbol, rng, config.bit_flip_rate))
    return delivered


def _maybe_flip_bits(symbol: FountainSymbol, rng: random.Random, bit_flip_rate: float) -> FountainSymbol:
    if bit_flip_rate == 0:
        return symbol

    data = bytearray(symbol.data)
    for index, value in enumerate(data):
        new_value = value
        for bit in range(8):
            if rng.random() < bit_flip_rate:
                new_value ^= 1 << bit
        data[index] = new_value

    return FountainSymbol(
        symbol_id=symbol.symbol_id,
        source_count=symbol.source_count,
        block_size=symbol.block_size,
        original_size=symbol.original_size,
        block_ids=symbol.block_ids,
        data=bytes(data),
        data_crc=symbol.data_crc,
    )


def _symbol_rng(seed: int | str, symbol_id: int) -> random.Random:
    digest = hashlib.sha256(f"{seed}:channel:{symbol_id}".encode("utf-8")).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def _validate_rate(value: float, name: str) -> None:
    if value < 0 or value > 1:
        raise ValueError(f"{name} must be in [0, 1]")
