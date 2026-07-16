import argparse
import json
from pathlib import Path

import numpy as np
import torch
from PIL import Image

from evaluate_v2_random import build_encoder, load_image, to_uint8_array
from packet_v3 import bytes_to_bits, build_packet


TOTAL_BITS = 2 * 512 * 512


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cover", required=True)
    parser.add_argument("--payload", required=True)
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--payload-bpp", type=float, required=True)
    parser.add_argument("--ecc-bytes", type=int, default=64)
    parser.add_argument("--nsize", type=int, default=255)
    parser.add_argument("--packet-seed", type=int, default=0)
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    checkpoint = torch.load(args.checkpoint, map_location=device)
    encoder = build_encoder(checkpoint.get("config", {})).to(device).eval()
    encoder.load_state_dict(checkpoint["en"], strict=True)

    requested_useful_bits = int(round(512 * 512 * args.payload_bpp))
    payload_bytes = Path(args.payload).read_bytes()
    packet, plan = build_packet(
        payload_bytes,
        useful_bits=requested_useful_bits,
        ecc_bytes=args.ecc_bytes,
        nsize=args.nsize,
        seed=args.packet_seed,
    )
    packet_bits = bytes_to_bits(packet)
    full = np.zeros(TOTAL_BITS, dtype=np.float32)
    full[: len(packet_bits)] = packet_bits
    payload_tensor = torch.from_numpy(full).view(1, 2, 512, 512).to(device)

    _, cover_tensor = load_image(args.cover)
    cover_tensor = cover_tensor.unsqueeze(0).to(device)
    with torch.no_grad():
        stego = encoder(cover_tensor, payload_tensor)

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(to_uint8_array(stego)).save(args.output)
    metadata = {
        "output": args.output,
        "payload_bytes": len(payload_bytes),
        "payload_bpp_requested": args.payload_bpp,
        "nominal_bpp_used": plan.nominal_bpp_used,
        "effective_user_bpp": (len(payload_bytes) * 8) / float(512 * 512),
        "max_payload_bytes": plan.max_payload_bytes,
        "ecc_bytes": args.ecc_bytes,
        "rs_chunks": plan.rs_chunks,
        "packet_seed": args.packet_seed,
    }
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
