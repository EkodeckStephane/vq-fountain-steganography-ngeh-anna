import random
import struct
import zlib
from dataclasses import dataclass

import numpy as np
from reedsolo import RSCodec, ReedSolomonError


MAGIC = b"EV3P"
VERSION = 1
HEADER_STRUCT = struct.Struct(">4sBBHIIIIHHI")
HEADER_SIZE = HEADER_STRUCT.size


class PacketError(ValueError):
    pass


@dataclass(frozen=True)
class CapacityPlan:
    useful_bits_requested: int
    useful_bits_used: int
    useful_bytes: int
    rs_chunks: int
    rs_bytes: int
    data_bytes: int
    ecc_bytes: int
    nsize: int
    max_payload_bytes: int
    unused_tail_bytes: int

    @property
    def nominal_bpp_used(self):
        return self.useful_bits_used / float(512 * 512)

    @property
    def max_effective_user_bpp(self):
        return (self.max_payload_bytes * 8) / float(512 * 512)


def capacity_plan(useful_bits, ecc_bytes=64, nsize=255):
    if useful_bits < 8:
        raise PacketError("useful_bits must provide at least one byte")
    if ecc_bytes <= 0 or ecc_bytes >= nsize:
        raise PacketError("ecc_bytes must be in 1..nsize-1")
    useful_bytes = useful_bits // 8
    rs_chunks = useful_bytes // nsize
    data_per_chunk = nsize - ecc_bytes
    data_bytes = rs_chunks * data_per_chunk
    rs_bytes = rs_chunks * nsize
    max_payload_bytes = data_bytes - HEADER_SIZE
    if rs_chunks < 1 or max_payload_bytes < 1:
        raise PacketError(
            "capacity too small for header and Reed-Solomon payload: "
            f"useful_bits={useful_bits}, ecc_bytes={ecc_bytes}, nsize={nsize}"
        )
    return CapacityPlan(
        useful_bits_requested=useful_bits,
        useful_bits_used=useful_bytes * 8,
        useful_bytes=useful_bytes,
        rs_chunks=rs_chunks,
        rs_bytes=rs_bytes,
        data_bytes=data_bytes,
        ecc_bytes=ecc_bytes,
        nsize=nsize,
        max_payload_bytes=max_payload_bytes,
        unused_tail_bytes=useful_bytes - rs_bytes,
    )


def bytes_to_bits(data):
    bits = np.zeros(len(data) * 8, dtype=np.float32)
    for i, byte in enumerate(data):
        for bit in range(8):
            bits[i * 8 + bit] = (byte >> (7 - bit)) & 1
    return bits


def bits_to_bytes(bits):
    bits = np.asarray(bits).astype(np.uint8)
    output = bytearray()
    for offset in range(0, len(bits) - 7, 8):
        value = 0
        for bit in bits[offset : offset + 8]:
            value = (value << 1) | int(bit)
        output.append(value)
    return bytes(output)


def byte_reliability_from_logits(logits, useful_bits, mode="min"):
    flat = np.asarray(logits).reshape(-1)[: (useful_bits // 8) * 8]
    bit_reliability = np.abs(flat).reshape(-1, 8)
    if mode == "mean":
        return bit_reliability.mean(axis=1)
    if mode == "min":
        return bit_reliability.min(axis=1)
    raise PacketError(f"unknown byte reliability mode: {mode}")


def _permutation(length, seed):
    positions = list(range(length))
    random.Random(int(seed)).shuffle(positions)
    return positions


def _interleave(data, seed):
    perm = _permutation(len(data), seed)
    out = bytearray(len(data))
    for src, dst in enumerate(perm):
        out[dst] = data[src]
    return bytes(out)


def _deinterleave(data, seed):
    perm = _permutation(len(data), seed)
    out = bytearray(len(data))
    for src, dst in enumerate(perm):
        out[src] = data[dst]
    return bytes(out)


def _deinterleave_reliability(values, seed):
    perm = _permutation(len(values), seed)
    out = np.zeros(len(values), dtype=np.float32)
    for src, dst in enumerate(perm):
        out[src] = values[dst]
    return out


def config_id(useful_bits, ecc_bytes, nsize, seed):
    text = f"etehgan-v3|{useful_bits}|{ecc_bytes}|{nsize}|{int(seed)}"
    return zlib.crc32(text.encode("ascii")) & 0xFFFFFFFF


def build_packet(payload_bytes, useful_bits, ecc_bytes=64, nsize=255, seed=0):
    plan = capacity_plan(useful_bits, ecc_bytes=ecc_bytes, nsize=nsize)
    if len(payload_bytes) > plan.max_payload_bytes:
        raise PacketError(
            f"payload too large: {len(payload_bytes)} bytes; "
            f"max={plan.max_payload_bytes} bytes for this plan"
        )

    payload_crc = zlib.crc32(payload_bytes) & 0xFFFFFFFF
    header = HEADER_STRUCT.pack(
        MAGIC,
        VERSION,
        0,
        HEADER_SIZE,
        config_id(plan.useful_bits_used, ecc_bytes, nsize, seed),
        len(payload_bytes),
        payload_crc,
        plan.useful_bits_used,
        ecc_bytes,
        nsize,
        int(seed) & 0xFFFFFFFF,
    )
    raw = header + payload_bytes + bytes(plan.data_bytes - HEADER_SIZE - len(payload_bytes))

    codec = RSCodec(ecc_bytes, nsize=nsize)
    encoded = bytearray()
    data_per_chunk = nsize - ecc_bytes
    for offset in range(0, len(raw), data_per_chunk):
        encoded.extend(codec.encode(raw[offset : offset + data_per_chunk]))
    if len(encoded) != plan.rs_bytes:
        raise PacketError(f"unexpected RS byte count: {len(encoded)} != {plan.rs_bytes}")

    packet = bytes(encoded) + bytes(plan.unused_tail_bytes)
    return _interleave(packet, seed), plan


def decode_packet(
    encoded_interleaved,
    useful_bits,
    ecc_bytes=64,
    nsize=255,
    seed=0,
    byte_reliability=None,
    max_erasures_per_chunk=0,
):
    plan = capacity_plan(useful_bits, ecc_bytes=ecc_bytes, nsize=nsize)
    encoded_interleaved = bytes(encoded_interleaved[: plan.useful_bytes])
    if len(encoded_interleaved) < plan.useful_bytes:
        raise PacketError("encoded data shorter than useful byte capacity")

    encoded = _deinterleave(encoded_interleaved, seed)
    reliability = None
    if byte_reliability is not None:
        reliability = _deinterleave_reliability(
            np.asarray(byte_reliability, dtype=np.float32)[: plan.useful_bytes], seed
        )

    codec = RSCodec(ecc_bytes, nsize=nsize)
    data_per_chunk = nsize - ecc_bytes
    raw = bytearray()
    erasures_used = []
    for chunk_index, offset in enumerate(range(0, plan.rs_bytes, nsize)):
        chunk = encoded[offset : offset + nsize]
        erase_pos = None
        if reliability is not None and max_erasures_per_chunk > 0:
            rel = reliability[offset : offset + nsize]
            count = min(int(max_erasures_per_chunk), ecc_bytes, len(rel))
            if count > 0:
                erase_pos = sorted(np.argsort(rel)[:count].astype(int).tolist())
        try:
            decoded_rs = codec.decode(chunk, erase_pos=erase_pos)
        except ReedSolomonError as exc:
            raise PacketError(f"RS decode failed in chunk {chunk_index}: {exc}") from exc
        decoded_chunk = decoded_rs[0] if isinstance(decoded_rs, (tuple, list)) else decoded_rs
        raw.extend(bytes(decoded_chunk[:data_per_chunk]))
        erasures_used.append(0 if erase_pos is None else len(erase_pos))

    if len(raw) < HEADER_SIZE:
        raise PacketError("decoded packet shorter than header")
    (
        magic,
        version,
        flags,
        header_size,
        actual_config_id,
        payload_len,
        payload_crc,
        useful_bits_header,
        ecc_header,
        nsize_header,
        seed_header,
    ) = HEADER_STRUCT.unpack(bytes(raw[:HEADER_SIZE]))

    expected_config_id = config_id(plan.useful_bits_used, ecc_bytes, nsize, seed)
    if magic != MAGIC:
        raise PacketError(f"bad magic: {magic!r}")
    if version != VERSION:
        raise PacketError(f"unsupported packet version: {version}")
    if flags != 0:
        raise PacketError(f"unsupported packet flags: {flags}")
    if header_size != HEADER_SIZE:
        raise PacketError(f"unexpected header size: {header_size}")
    if actual_config_id != expected_config_id:
        raise PacketError("packet config_id does not match decoder configuration")
    if useful_bits_header != plan.useful_bits_used:
        raise PacketError("packet useful_bits does not match decoder configuration")
    if ecc_header != ecc_bytes or nsize_header != nsize:
        raise PacketError("packet ECC parameters do not match decoder configuration")
    if seed_header != (int(seed) & 0xFFFFFFFF):
        raise PacketError("packet seed does not match decoder configuration")
    if payload_len > plan.max_payload_bytes:
        raise PacketError(f"invalid payload length: {payload_len}")

    payload = bytes(raw[HEADER_SIZE : HEADER_SIZE + payload_len])
    actual_crc = zlib.crc32(payload) & 0xFFFFFFFF
    if actual_crc != payload_crc:
        raise PacketError("payload CRC mismatch")

    metadata = {
        "payload_len": payload_len,
        "payload_crc32": f"{payload_crc:08x}",
        "useful_bits_used": plan.useful_bits_used,
        "ecc_bytes": ecc_bytes,
        "nsize": nsize,
        "rs_chunks": plan.rs_chunks,
        "max_payload_bytes": plan.max_payload_bytes,
        "erasures_used_per_chunk": erasures_used,
    }
    return payload, metadata
