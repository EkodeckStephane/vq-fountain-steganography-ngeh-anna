import argparse
import json
from pathlib import Path

import torch
from PIL import Image

from evaluate_v2_robustness import pil_to_normalized_tensor
from models import DenseDecoder512
from packet_v3 import (
    bits_to_bytes,
    byte_reliability_from_logits,
    decode_packet,
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--stego", required=True)
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--payload-bpp", type=float, required=True)
    parser.add_argument("--ecc-bytes", type=int, default=64)
    parser.add_argument("--nsize", type=int, default=255)
    parser.add_argument("--packet-seed", type=int, default=0)
    parser.add_argument("--max-erasures-per-chunk", type=int, default=0)
    parser.add_argument("--reliability-mode", choices=["min", "mean"], default="min")
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    checkpoint = torch.load(args.checkpoint, map_location=device)
    decoder = DenseDecoder512().to(device).eval()
    decoder.load_state_dict(checkpoint["de"], strict=True)

    requested_useful_bits = int(round(512 * 512 * args.payload_bpp))
    image = Image.open(args.stego).convert("RGB").resize((512, 512), Image.Resampling.BICUBIC)
    tensor = pil_to_normalized_tensor(image).unsqueeze(0).to(device)
    with torch.no_grad():
        logits_tensor = decoder(tensor)

    logits = logits_tensor.detach().cpu().numpy().reshape(-1)
    useful_bits_used = (requested_useful_bits // 8) * 8
    pred_bits = (logits[:useful_bits_used] >= 0.0).astype("uint8")
    encoded_bytes = bits_to_bytes(pred_bits)
    reliability = None
    if args.max_erasures_per_chunk > 0:
        reliability = byte_reliability_from_logits(
            logits,
            useful_bits_used,
            mode=args.reliability_mode,
        )

    payload, metadata = decode_packet(
        encoded_bytes,
        useful_bits=requested_useful_bits,
        ecc_bytes=args.ecc_bytes,
        nsize=args.nsize,
        seed=args.packet_seed,
        byte_reliability=reliability,
        max_erasures_per_chunk=args.max_erasures_per_chunk,
    )
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_bytes(payload)
    metadata.update(
        {
            "stego": args.stego,
            "output": args.output,
            "max_erasures_per_chunk": args.max_erasures_per_chunk,
            "reliability_mode": args.reliability_mode,
        }
    )
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
