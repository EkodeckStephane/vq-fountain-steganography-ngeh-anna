"""XOR fountain code used by the VQ-Fountain prototype."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import math
import random
import zlib


class FountainDecodeError(ValueError):
    """Raised when the fountain decoder cannot solve enough source blocks."""


@dataclass(frozen=True)
class FountainSymbol:
    """One sparse XOR equation over source blocks."""

    symbol_id: int
    source_count: int
    block_size: int
    original_size: int
    block_ids: tuple[int, ...]
    data: bytes
    data_crc: int | None = None


def _xor_bytes(chunks: list[bytes], block_size: int) -> bytes:
    out = bytearray(block_size)
    for chunk in chunks:
        if len(chunk) != block_size:
            raise ValueError("all chunks must match block_size")
        for index, value in enumerate(chunk):
            out[index] ^= value
    return bytes(out)


def _split_blocks(data: bytes, block_size: int) -> list[bytes]:
    if block_size <= 0:
        raise ValueError("block_size must be positive")
    if not data:
        data = b"\x00"

    blocks: list[bytes] = []
    for offset in range(0, len(data), block_size):
        block = data[offset : offset + block_size]
        if len(block) < block_size:
            block = block + bytes(block_size - len(block))
        blocks.append(block)
    return blocks


def _seeded_rng(seed: int | str, symbol_id: int) -> random.Random:
    digest = hashlib.sha256(f"{seed}:{symbol_id}".encode("utf-8")).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def _choose_degree(rng: random.Random, source_count: int) -> int:
    if source_count <= 1:
        return 1

    # Dense-enough parity symbols make the Stage 0 erasure channel much more
    # reliable than a pure peeling-oriented LT distribution at small block
    # counts. Later work can replace this with a tuned robust-soliton/RLNC mix.
    low = max(1, source_count // 3)
    high = max(low, min(source_count, (2 * source_count) // 3))
    return rng.randint(low, high)


def make_symbol(blocks: list[bytes], original_size: int, symbol_id: int, seed: int | str) -> FountainSymbol:
    """Create one deterministic symbol from source blocks."""

    source_count = len(blocks)
    if source_count == 0:
        raise ValueError("at least one source block is required")
    block_size = len(blocks[0])

    if symbol_id < source_count:
        block_ids = (symbol_id,)
    else:
        rng = _seeded_rng(seed, symbol_id)
        degree = _choose_degree(rng, source_count)
        block_ids = tuple(sorted(rng.sample(range(source_count), degree)))

    data = _xor_bytes([blocks[index] for index in block_ids], block_size)
    return FountainSymbol(
        symbol_id=symbol_id,
        source_count=source_count,
        block_size=block_size,
        original_size=original_size,
        block_ids=block_ids,
        data=data,
        data_crc=symbol_crc(data),
    )


def recommended_symbol_count(source_count: int, overhead: float) -> int:
    """Return a conservative number of symbols for a requested overhead."""

    if source_count <= 0:
        raise ValueError("source_count must be positive")
    if overhead < 0:
        raise ValueError("overhead must be non-negative")
    return source_count + int(math.ceil(source_count * overhead))


def encode_symbols(
    data: bytes,
    block_size: int = 32,
    overhead: float = 0.5,
    seed: int | str = 0,
    symbol_count: int | None = None,
) -> list[FountainSymbol]:
    """Encode data into deterministic rateless symbols."""

    blocks = _split_blocks(data, block_size)
    count = symbol_count
    if count is None:
        count = recommended_symbol_count(len(blocks), overhead)
    if count < len(blocks):
        raise ValueError("symbol_count must be at least the source block count")

    return [make_symbol(blocks, len(data), symbol_id, seed) for symbol_id in range(count)]


def make_repetition_symbol(blocks: list[bytes], original_size: int, symbol_id: int) -> FountainSymbol:
    source_count = len(blocks)
    if source_count == 0:
        raise ValueError("at least one source block is required")
    block_id = symbol_id % source_count
    data = blocks[block_id]
    return FountainSymbol(
        symbol_id=symbol_id,
        source_count=source_count,
        block_size=len(data),
        original_size=original_size,
        block_ids=(block_id,),
        data=data,
        data_crc=symbol_crc(data),
    )


def encode_repetition_symbols(
    data: bytes,
    block_size: int = 32,
    overhead: float = 0.5,
    symbol_count: int | None = None,
) -> list[FountainSymbol]:
    """Encode data as repeated systematic source blocks.

    This is a fixed-redundancy baseline for ablations, not the proposed
    rateless fountain layer.
    """

    blocks = _split_blocks(data, block_size)
    count = symbol_count
    if count is None:
        count = recommended_symbol_count(len(blocks), overhead)
    if count < len(blocks):
        raise ValueError("symbol_count must be at least the source block count")
    return [make_repetition_symbol(blocks, len(data), symbol_id) for symbol_id in range(count)]


def decode_symbols(symbols: list[FountainSymbol], validate_symbol_crc: bool = True) -> bytes:
    """Recover the original byte string with GF(2) elimination."""

    if not symbols:
        raise FountainDecodeError("no symbols available")

    if validate_symbol_crc:
        symbols = [symbol for symbol in symbols if symbol_crc_valid(symbol)]
        if not symbols:
            raise FountainDecodeError("no CRC-valid symbols available")

    source_count = symbols[0].source_count
    block_size = symbols[0].block_size
    original_size = symbols[0].original_size
    for symbol in symbols:
        if symbol.source_count != source_count:
            raise FountainDecodeError("inconsistent source_count")
        if symbol.block_size != block_size:
            raise FountainDecodeError("inconsistent block_size")
        if symbol.original_size != original_size:
            raise FountainDecodeError("inconsistent original_size")

    pivots: dict[int, tuple[set[int], bytearray]] = {}
    for symbol in sorted(symbols, key=lambda item: item.symbol_id):
        ids = set(symbol.block_ids)
        data = bytearray(symbol.data)

        while ids:
            pivot = min(ids)
            if pivot not in pivots:
                pivots[pivot] = (set(ids), data)
                break

            pivot_ids, pivot_data = pivots[pivot]
            ids.symmetric_difference_update(pivot_ids)
            _xor_in_place(data, pivot_data)

        if not ids and any(data):
            raise FountainDecodeError("inconsistent equations; symbol data may be corrupted")

    if len(pivots) != source_count:
        missing = source_count - len(pivots)
        raise FountainDecodeError(f"decoder stopped with {missing} missing source blocks")

    solved: dict[int, bytes] = {}
    for pivot in sorted(pivots, reverse=True):
        ids, data = pivots[pivot]
        block = bytearray(data)
        for block_id in ids:
            if block_id == pivot:
                continue
            if block_id not in solved:
                raise FountainDecodeError("rank-complete system is not triangular")
            _xor_in_place(block, solved[block_id])
        solved[pivot] = bytes(block)

    recovered = b"".join(solved[index] for index in range(source_count))
    return recovered[:original_size]


def _xor_in_place(left: bytearray, right: bytes | bytearray) -> None:
    if len(left) != len(right):
        raise ValueError("xor operands must have the same length")
    for index, value in enumerate(right):
        left[index] ^= value


def symbol_crc(data: bytes) -> int:
    """CRC32 used to turn corrupted fountain symbols into erasures."""

    return zlib.crc32(data) & 0xFFFFFFFF


def symbol_crc_valid(symbol: FountainSymbol) -> bool:
    """Return true when the symbol has no CRC or its CRC matches its data."""

    if symbol.data_crc is None:
        return True
    return symbol_crc(symbol.data) == symbol.data_crc
