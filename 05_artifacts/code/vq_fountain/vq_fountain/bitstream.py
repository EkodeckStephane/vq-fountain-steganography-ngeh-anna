"""Payload packing utilities for VQ-Fountain Stega."""

from __future__ import annotations

import struct
import zlib

MAGIC = b"VQF1"
HEADER_STRUCT = struct.Struct(">4sII")
HEADER_SIZE = HEADER_STRUCT.size


class PayloadDecodeError(ValueError):
    """Raised when a recovered payload packet fails structural checks."""


def bytes_to_bits(data: bytes) -> list[int]:
    """Return a most-significant-bit-first bit list."""

    bits: list[int] = []
    for byte in data:
        for shift in range(7, -1, -1):
            bits.append((byte >> shift) & 1)
    return bits


def bits_to_bytes(bits: list[int] | tuple[int, ...], trim_to_bytes: int | None = None) -> bytes:
    """Convert a most-significant-bit-first bit list to bytes.

    If the number of bits is not a multiple of eight, zero bits are appended.
    """

    for bit in bits:
        if bit not in (0, 1):
            raise ValueError(f"invalid bit value: {bit!r}")

    padded = list(bits)
    remainder = len(padded) % 8
    if remainder:
        padded.extend([0] * (8 - remainder))

    out = bytearray()
    for offset in range(0, len(padded), 8):
        value = 0
        for bit in padded[offset : offset + 8]:
            value = (value << 1) | bit
        out.append(value)

    data = bytes(out)
    if trim_to_bytes is not None:
        return data[:trim_to_bytes]
    return data


def pack_payload(payload: bytes) -> bytes:
    """Add a small self-contained header to a payload."""

    crc = zlib.crc32(payload) & 0xFFFFFFFF
    header = HEADER_STRUCT.pack(MAGIC, len(payload), crc)
    return header + payload


def unpack_payload(packet: bytes) -> bytes:
    """Validate and return the payload from a packed byte sequence."""

    if len(packet) < HEADER_SIZE:
        raise PayloadDecodeError("packet shorter than header")

    magic, payload_len, expected_crc = HEADER_STRUCT.unpack(packet[:HEADER_SIZE])
    if magic != MAGIC:
        raise PayloadDecodeError("invalid packet magic")

    end = HEADER_SIZE + payload_len
    if len(packet) < end:
        raise PayloadDecodeError("packet shorter than declared payload length")

    payload = packet[HEADER_SIZE:end]
    actual_crc = zlib.crc32(payload) & 0xFFFFFFFF
    if actual_crc != expected_crc:
        raise PayloadDecodeError("payload CRC mismatch")

    return payload
