import argparse
import csv
import json
import random
from pathlib import Path

import numpy as np
import torch
from PIL import Image

from evaluate_v2_random import (
    IMAGE_EXTENSIONS,
    build_encoder,
    global_ssim,
    load_image,
    psnr,
    seed_everything,
    to_uint8_array,
)
from evaluate_v2_robustness import attack_image, pil_to_normalized_tensor
from models import DenseDecoder512
from packet_v3 import (
    PacketError,
    bits_to_bytes,
    byte_reliability_from_logits,
    bytes_to_bits,
    build_packet,
    capacity_plan,
    decode_packet,
)


TOTAL_BITS = 2 * 512 * 512


def collect_images(roots, max_images=None, max_images_per_root=None, offset_images=0):
    paths = []
    for root in roots:
        root_paths = sorted(p for p in Path(root).rglob("*") if p.suffix.lower() in IMAGE_EXTENSIONS)
        if max_images_per_root:
            root_paths = root_paths[:max_images_per_root]
        paths.extend(root_paths)
    paths = sorted(paths)
    if offset_images:
        paths = paths[offset_images:]
    if max_images:
        paths = paths[:max_images]
    if not paths:
        raise ValueError(f"No images found under {roots}")
    return paths


def make_payload(length, seed):
    return random.Random(int(seed)).randbytes(length)


def try_decode(encoded_bytes, useful_bits, ecc_bytes, nsize, seed, reliability=None, max_erasures=0):
    try:
        payload, metadata = decode_packet(
            encoded_bytes,
            useful_bits=useful_bits,
            ecc_bytes=ecc_bytes,
            nsize=nsize,
            seed=seed,
            byte_reliability=reliability,
            max_erasures_per_chunk=max_erasures,
        )
        return payload, metadata, ""
    except PacketError as exc:
        return None, {}, str(exc)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--image-root", required=True, nargs="+")
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--payload-bpp", type=float, required=True)
    parser.add_argument("--payload-bytes", type=int)
    parser.add_argument("--payload-fraction", type=float, default=1.0)
    parser.add_argument("--ecc-bytes", type=int, default=64)
    parser.add_argument("--nsize", type=int, default=255)
    parser.add_argument("--packet-seed", type=int, default=0)
    parser.add_argument("--trials-per-image", type=int, default=1)
    parser.add_argument("--attacks", nargs="+", default=["clean"])
    parser.add_argument("--max-erasures-per-chunk", type=int, default=0)
    parser.add_argument("--reliability-mode", choices=["min", "mean"], default="min")
    parser.add_argument("--out-csv", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--seed", type=int, default=789)
    parser.add_argument("--max-images", type=int)
    parser.add_argument("--max-images-per-root", type=int)
    parser.add_argument("--offset-images", type=int, default=0)
    args = parser.parse_args()

    seed_everything(args.seed)
    requested_useful_bits = int(round(512 * 512 * args.payload_bpp))
    plan = capacity_plan(requested_useful_bits, ecc_bytes=args.ecc_bytes, nsize=args.nsize)
    if args.payload_bytes is None:
        payload_bytes = max(1, int(plan.max_payload_bytes * args.payload_fraction))
    else:
        payload_bytes = args.payload_bytes
    if payload_bytes > plan.max_payload_bytes:
        raise ValueError(f"payload_bytes={payload_bytes} exceeds max_payload_bytes={plan.max_payload_bytes}")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    checkpoint = torch.load(args.checkpoint, map_location=device)
    encoder = build_encoder(checkpoint.get("config", {})).to(device).eval()
    decoder = DenseDecoder512().to(device).eval()
    encoder.load_state_dict(checkpoint["en"], strict=True)
    decoder.load_state_dict(checkpoint["de"], strict=True)

    paths = collect_images(
        args.image_root,
        max_images=args.max_images,
        max_images_per_root=args.max_images_per_root,
        offset_images=args.offset_images,
    )

    rows = []
    with torch.no_grad():
        for image_index, path in enumerate(paths):
            cover_image, cover_tensor = load_image(path)
            cover_arr = np.asarray(cover_image.convert("RGB"))
            cover_tensor = cover_tensor.unsqueeze(0).to(device)

            for trial in range(args.trials_per_image):
                trial_seed = args.seed + image_index * 1009 + trial * 9173
                payload = make_payload(payload_bytes, trial_seed)
                packet, packet_plan = build_packet(
                    payload,
                    useful_bits=requested_useful_bits,
                    ecc_bytes=args.ecc_bytes,
                    nsize=args.nsize,
                    seed=args.packet_seed,
                )
                packet_bits = bytes_to_bits(packet)
                full = np.zeros(TOTAL_BITS, dtype=np.float32)
                full[: len(packet_bits)] = packet_bits
                payload_tensor = torch.from_numpy(full).view(1, 2, 512, 512).to(device)

                stego = encoder(cover_tensor, payload_tensor)
                stego_arr = to_uint8_array(stego)
                stego_image = Image.fromarray(stego_arr)
                stego_psnr = psnr(cover_arr, stego_arr)
                stego_ssim = float(global_ssim(cover_arr, stego_arr))

                for attack in args.attacks:
                    attacked = attack_image(stego_image, attack)
                    attacked_tensor = pil_to_normalized_tensor(attacked).unsqueeze(0).to(device)
                    logits = decoder(attacked_tensor).detach().cpu().numpy().reshape(-1)
                    pred_bits = (logits[: packet_plan.useful_bits_used] >= 0.0).astype(np.uint8)
                    target_bits = packet_bits[: packet_plan.useful_bits_used].astype(np.uint8)
                    raw_bit_ber = float(np.mean(pred_bits != target_bits))
                    encoded_bytes = bits_to_bytes(pred_bits)
                    reliability = byte_reliability_from_logits(
                        logits,
                        packet_plan.useful_bits_used,
                        mode=args.reliability_mode,
                    )

                    hard_payload, hard_metadata, hard_error = try_decode(
                        encoded_bytes,
                        useful_bits=requested_useful_bits,
                        ecc_bytes=args.ecc_bytes,
                        nsize=args.nsize,
                        seed=args.packet_seed,
                    )
                    erasure_payload, erasure_metadata, erasure_error = try_decode(
                        encoded_bytes,
                        useful_bits=requested_useful_bits,
                        ecc_bytes=args.ecc_bytes,
                        nsize=args.nsize,
                        seed=args.packet_seed,
                        reliability=reliability,
                        max_erasures=args.max_erasures_per_chunk,
                    )

                    rows.append(
                        {
                            "image": str(path),
                            "trial": trial,
                            "attack": attack,
                            "payload_bpp_requested": args.payload_bpp,
                            "nominal_bpp_used": packet_plan.nominal_bpp_used,
                            "effective_user_bpp": (payload_bytes * 8) / float(512 * 512),
                            "payload_bytes": payload_bytes,
                            "max_payload_bytes": packet_plan.max_payload_bytes,
                            "ecc_bytes": args.ecc_bytes,
                            "rs_chunks": packet_plan.rs_chunks,
                            "packet_seed": args.packet_seed,
                            "raw_bit_ber": raw_bit_ber,
                            "hard_exact": hard_payload == payload,
                            "hard_error": hard_error[:160],
                            "erasure_exact": erasure_payload == payload,
                            "erasure_error": erasure_error[:160],
                            "max_erasures_per_chunk": args.max_erasures_per_chunk,
                            "psnr_db": stego_psnr,
                            "global_ssim": stego_ssim,
                        }
                    )

    summary_by_attack = {}
    for attack in args.attacks:
        attack_rows = [r for r in rows if r["attack"] == attack]
        summary_by_attack[attack] = {
            "n": len(attack_rows),
            "hard_exact_rate": float(np.mean([r["hard_exact"] for r in attack_rows])),
            "erasure_exact_rate": float(np.mean([r["erasure_exact"] for r in attack_rows])),
            "mean_raw_bit_ber": float(np.mean([r["raw_bit_ber"] for r in attack_rows])),
            "max_raw_bit_ber": float(np.max([r["raw_bit_ber"] for r in attack_rows])),
            "mean_psnr_db": float(np.mean([r["psnr_db"] for r in attack_rows])),
            "mean_global_ssim": float(np.mean([r["global_ssim"] for r in attack_rows])),
        }

    summary = {
        "checkpoint": args.checkpoint,
        "payload_bpp_requested": args.payload_bpp,
        "nominal_bpp_used": plan.nominal_bpp_used,
        "payload_bytes": payload_bytes,
        "max_payload_bytes": plan.max_payload_bytes,
        "max_effective_user_bpp": plan.max_effective_user_bpp,
        "effective_user_bpp": (payload_bytes * 8) / float(512 * 512),
        "ecc_bytes": args.ecc_bytes,
        "nsize": args.nsize,
        "rs_chunks": plan.rs_chunks,
        "unused_tail_bytes": plan.unused_tail_bytes,
        "summary_by_attack": summary_by_attack,
    }

    Path(args.out_csv).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    Path(args.out_json).write_text(json.dumps({"summary": summary, "rows": rows}, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
