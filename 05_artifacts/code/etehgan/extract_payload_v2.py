import argparse
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from reedsolo import RSCodec, ReedSolomonError

from models import DenseDecoder512


def pil_to_normalized_tensor(pil_image):
    arr = np.asarray(pil_image.convert("RGB"), dtype=np.float32) / 255.0
    tensor = torch.from_numpy(arr).permute(2, 0, 1)
    return (tensor - 0.5) / 0.5


def bits_to_bytes(bits):
    output = bytearray()
    for i in range(0, len(bits), 8):
        byte_bits = bits[i : i + 8]
        if len(byte_bits) < 8:
            break
        output.append(int("".join(str(int(bit)) for bit in byte_bits), 2))
    return bytes(output)


def decode_fixed_packet(encoded, useful_bits, ecc_bytes, nsize=255):
    useful_bytes = useful_bits // 8
    chunks = useful_bytes // nsize
    data_per_chunk = nsize - ecc_bytes
    codec = RSCodec(ecc_bytes, nsize=nsize)
    raw = bytearray()
    for offset in range(0, chunks * nsize, nsize):
        decoded_rs = codec.decode(encoded[offset : offset + nsize])
        chunk = decoded_rs[0] if isinstance(decoded_rs, (tuple, list)) else decoded_rs
        raw.extend(bytes(chunk[:data_per_chunk]))
    payload_len = int.from_bytes(raw[:4], "big")
    if payload_len < 0 or payload_len > len(raw) - 4:
        raise ValueError(f"invalid payload length: {payload_len}")
    return bytes(raw[4 : 4 + payload_len])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--stego", required=True)
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--payload-bpp", type=float, required=True)
    parser.add_argument("--ecc-bytes", type=int, default=64)
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    checkpoint = torch.load(args.checkpoint, map_location=device)
    decoder = DenseDecoder512().to(device).eval()
    decoder.load_state_dict(checkpoint["de"], strict=True)

    useful_bits = int(round(512 * 512 * args.payload_bpp))
    image = Image.open(args.stego).convert("RGB").resize((512, 512), Image.Resampling.BICUBIC)
    tensor = pil_to_normalized_tensor(image).unsqueeze(0).to(device)
    with torch.no_grad():
        decoded = decoder(tensor)
    bits = (decoded >= 0.0).int().cpu().numpy().flatten()[:useful_bits]
    encoded = bits_to_bytes(bits)

    try:
        payload = decode_fixed_packet(encoded, useful_bits, args.ecc_bytes)
    except (ReedSolomonError, UnicodeDecodeError, ValueError) as exc:
        raise SystemExit(f"[v2-extract] recovery failed: {exc}")

    Path(args.output).write_bytes(payload)
    print(f"[v2-extract] wrote {args.output}")
    print(f"[v2-extract] payload_bytes={len(payload)} useful_bits={useful_bits} ecc_bytes={args.ecc_bytes}")


if __name__ == "__main__":
    main()
