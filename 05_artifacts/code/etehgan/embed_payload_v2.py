import argparse
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from reedsolo import RSCodec

from evaluate_v2_random import build_encoder, load_image, to_uint8_array


def bytes_to_bits(data):
    bits = []
    for byte in data:
        bits.extend(int(bit) for bit in f"{byte:08b}")
    return bits


def make_fixed_packet(payload_bytes, useful_bits, ecc_bytes, nsize=255):
    if useful_bits % 8 != 0:
        raise ValueError("useful_bits must be byte-aligned")
    useful_bytes = useful_bits // 8
    if ecc_bytes >= nsize:
        raise ValueError("ecc_bytes must be smaller than nsize")
    chunks = useful_bytes // nsize
    data_per_chunk = nsize - ecc_bytes
    raw_bytes = chunks * data_per_chunk
    encoded_bytes = chunks * nsize
    if chunks < 1 or raw_bytes <= 4:
        raise ValueError("capacity too small for header and ECC")
    if len(payload_bytes) > raw_bytes - 4:
        raise ValueError(
            f"payload too large: {len(payload_bytes)} bytes, max {raw_bytes - 4}"
        )
    header = len(payload_bytes).to_bytes(4, "big")
    raw = header + payload_bytes + bytes(raw_bytes - 4 - len(payload_bytes))
    codec = RSCodec(ecc_bytes, nsize=nsize)
    encoded = bytearray()
    for offset in range(0, len(raw), data_per_chunk):
        encoded.extend(codec.encode(raw[offset : offset + data_per_chunk]))
    if len(encoded) != encoded_bytes:
        raise ValueError(f"unexpected encoded length: {len(encoded)} != {encoded_bytes}")
    return bytes(encoded) + bytes(useful_bytes - encoded_bytes)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cover", required=True)
    parser.add_argument("--payload", required=True)
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--payload-bpp", type=float, required=True)
    parser.add_argument("--ecc-bytes", type=int, default=64)
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    checkpoint = torch.load(args.checkpoint, map_location=device)
    encoder = build_encoder(checkpoint.get("config", {})).to(device).eval()
    encoder.load_state_dict(checkpoint["en"], strict=True)

    payload_bytes = Path(args.payload).read_bytes()
    useful_bits = int(round(512 * 512 * args.payload_bpp))
    packet = make_fixed_packet(payload_bytes, useful_bits, args.ecc_bytes)
    flat_bits = bytes_to_bits(packet)
    full = np.zeros(2 * 512 * 512, dtype=np.float32)
    full[: len(flat_bits)] = flat_bits
    payload_tensor = torch.from_numpy(full).view(1, 2, 512, 512).to(device)

    _, cover_tensor = load_image(args.cover)
    cover_tensor = cover_tensor.unsqueeze(0).to(device)
    with torch.no_grad():
        stego = encoder(cover_tensor, payload_tensor)

    Image.fromarray(to_uint8_array(stego)).save(args.output)
    print(f"[v2-embed] wrote {args.output}")
    print(f"[v2-embed] payload_bytes={len(payload_bytes)} useful_bits={useful_bits} ecc_bytes={args.ecc_bytes}")


if __name__ == "__main__":
    main()
