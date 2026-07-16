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
from packet_v3 import bits_to_bytes, bytes_to_bits, build_packet, capacity_plan, decode_packet


TOTAL_BITS = 2 * 512 * 512


def collect_images(roots, max_images=None, offset_images=0):
    paths = []
    for root in roots:
        paths.extend(sorted(p for p in Path(root).rglob("*") if p.suffix.lower() in IMAGE_EXTENSIONS))
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


def decode_exact(encoded_bytes, useful_bits, ecc_bytes, nsize, seed, expected_payload):
    try:
        payload, _ = decode_packet(
            encoded_bytes,
            useful_bits=useful_bits,
            ecc_bytes=ecc_bytes,
            nsize=nsize,
            seed=seed,
        )
        return payload == expected_payload, ""
    except Exception as exc:  # PacketError plus reedsolo exceptions wrapped by PacketError.
        return False, str(exc)[:160]


def summarize(rows, ecc_values, attacks):
    by_attack = {}
    for attack in attacks:
        attack_rows = [r for r in rows if r["attack"] == attack]
        groups = {}
        for row in attack_rows:
            groups.setdefault((row["image_index"], row["trial"]), []).append(row)

        oracle_success = 0
        oracle_payload_bytes = []
        oracle_ecc = []
        fixed = {ecc: [] for ecc in ecc_values}
        for group_rows in groups.values():
            group_rows = sorted(group_rows, key=lambda r: int(r["ecc_bytes"]))
            chosen = None
            for row in group_rows:
                fixed[int(row["ecc_bytes"])].append(bool(row["exact_recovery"]))
                if chosen is None and row["exact_recovery"]:
                    chosen = row
            if chosen is not None:
                oracle_success += 1
                oracle_payload_bytes.append(int(chosen["payload_bytes"]))
                oracle_ecc.append(int(chosen["ecc_bytes"]))

        total = len(groups)
        by_attack[attack] = {
            "groups": total,
            "oracle_exact_rate": 0.0 if total == 0 else oracle_success / float(total),
            "oracle_mean_payload_bytes": 0.0 if not oracle_payload_bytes else float(np.mean(oracle_payload_bytes)),
            "oracle_mean_effective_bpp": 0.0
            if not oracle_payload_bytes
            else float(np.mean(oracle_payload_bytes) * 8.0 / (512 * 512)),
            "oracle_mean_ecc_bytes": 0.0 if not oracle_ecc else float(np.mean(oracle_ecc)),
            "fixed_exact_rate_by_ecc": {
                str(ecc): 0.0 if not fixed[ecc] else float(np.mean(fixed[ecc])) for ecc in ecc_values
            },
        }
    return by_attack


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--image-root", required=True, nargs="+")
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--payload-bpp", type=float, default=0.25)
    parser.add_argument("--ecc-candidates", type=int, nargs="+", default=[64, 96, 128])
    parser.add_argument("--nsize", type=int, default=255)
    parser.add_argument("--packet-seed", type=int, default=7)
    parser.add_argument("--trials-per-image", type=int, default=1)
    parser.add_argument("--attacks", nargs="+", default=["clean"])
    parser.add_argument("--max-images", type=int)
    parser.add_argument("--offset-images", type=int, default=0)
    parser.add_argument("--seed", type=int, default=4040)
    parser.add_argument("--out-csv", required=True)
    parser.add_argument("--out-json", required=True)
    args = parser.parse_args()

    seed_everything(args.seed)
    ecc_values = sorted(set(int(v) for v in args.ecc_candidates))
    useful_bits = int(round(512 * 512 * args.payload_bpp))

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    checkpoint = torch.load(args.checkpoint, map_location=device)
    encoder = build_encoder(checkpoint.get("config", {})).to(device).eval()
    decoder = DenseDecoder512().to(device).eval()
    encoder.load_state_dict(checkpoint["en"], strict=True)
    decoder.load_state_dict(checkpoint["de"], strict=True)

    paths = collect_images(args.image_root, max_images=args.max_images, offset_images=args.offset_images)
    rows = []
    with torch.no_grad():
        for image_index, path in enumerate(paths):
            cover_image, cover_tensor = load_image(path)
            cover_arr = np.asarray(cover_image.convert("RGB"))
            cover_tensor = cover_tensor.unsqueeze(0).to(device)
            for trial in range(args.trials_per_image):
                base_seed = args.seed + image_index * 1009 + trial * 9173
                for ecc_bytes in ecc_values:
                    plan = capacity_plan(useful_bits, ecc_bytes=ecc_bytes, nsize=args.nsize)
                    payload_bytes = plan.max_payload_bytes
                    payload = make_payload(payload_bytes, base_seed)
                    packet, packet_plan = build_packet(
                        payload,
                        useful_bits=useful_bits,
                        ecc_bytes=ecc_bytes,
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
                        exact, error = decode_exact(
                            encoded_bytes,
                            useful_bits=useful_bits,
                            ecc_bytes=ecc_bytes,
                            nsize=args.nsize,
                            seed=args.packet_seed,
                            expected_payload=payload,
                        )
                        abs_logits = np.abs(logits[: packet_plan.useful_bits_used])
                        rows.append(
                            {
                                "image": str(path),
                                "image_index": image_index,
                                "trial": trial,
                                "attack": attack,
                                "payload_bpp_requested": args.payload_bpp,
                                "nominal_bpp_used": packet_plan.nominal_bpp_used,
                                "ecc_bytes": ecc_bytes,
                                "payload_bytes": payload_bytes,
                                "effective_user_bpp": (payload_bytes * 8) / float(512 * 512),
                                "raw_bit_ber": raw_bit_ber,
                                "exact_recovery": exact,
                                "decode_error": error,
                                "mean_abs_logit": float(np.mean(abs_logits)),
                                "p01_abs_logit": float(np.percentile(abs_logits, 1)),
                                "p05_abs_logit": float(np.percentile(abs_logits, 5)),
                                "psnr_db": stego_psnr,
                                "global_ssim": stego_ssim,
                            }
                        )

    summary = {
        "checkpoint": args.checkpoint,
        "payload_bpp_requested": args.payload_bpp,
        "ecc_candidates": ecc_values,
        "attacks": args.attacks,
        "images": len(paths),
        "trials_per_image": args.trials_per_image,
        "summary_by_attack": summarize(rows, ecc_values, args.attacks),
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
