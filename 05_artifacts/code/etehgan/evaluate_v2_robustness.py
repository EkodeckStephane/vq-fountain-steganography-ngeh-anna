import argparse
import csv
import io
import json
import random
from pathlib import Path

import numpy as np
import torch
from PIL import Image, ImageFilter

from evaluate_v2_random import (
    IMAGE_EXTENSIONS,
    build_encoder,
    load_image,
    make_payload,
    seed_everything,
    to_uint8_array,
)
from models import DenseDecoder512


def pil_to_normalized_tensor(pil_image):
    arr = np.asarray(pil_image.convert("RGB"), dtype=np.float32) / 255.0
    tensor = torch.from_numpy(arr).permute(2, 0, 1)
    return (tensor - 0.5) / 0.5


def attack_image(image, attack):
    if attack == "clean":
        return image
    if attack.startswith("jpeg"):
        quality = int(attack.replace("jpeg", ""))
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=quality)
        buffer.seek(0)
        return Image.open(buffer).convert("RGB")
    if attack.startswith("noise"):
        sigma = float(attack.replace("noise", "")) / 255.0
        arr = np.asarray(image, dtype=np.float32) / 255.0
        noisy = np.clip(arr + np.random.normal(0, sigma, arr.shape), 0, 1)
        return Image.fromarray((noisy * 255).astype(np.uint8))
    if attack.startswith("blur"):
        radius = float(attack.replace("blur", ""))
        return image.filter(ImageFilter.GaussianBlur(radius=radius))
    if attack.startswith("resize"):
        scale = float(attack.replace("resize", ""))
        w, h = image.size
        small = image.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.Resampling.BICUBIC)
        return small.resize((w, h), Image.Resampling.BICUBIC)
    raise ValueError(f"Unknown attack: {attack}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--image-root", required=True, nargs="+")
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--payload-bpp", type=float, required=True)
    parser.add_argument("--trials-per-image", type=int, default=1)
    parser.add_argument("--attacks", nargs="+", default=["clean", "jpeg95", "jpeg90", "jpeg80", "noise2", "blur1", "resize0.75"])
    parser.add_argument("--out-csv", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--seed", type=int, default=456)
    parser.add_argument("--max-images", type=int)
    parser.add_argument("--max-images-per-root", type=int)
    parser.add_argument("--offset-images", type=int, default=0)
    args = parser.parse_args()

    seed_everything(args.seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    checkpoint = torch.load(args.checkpoint, map_location=device)
    config = checkpoint.get("config", {})

    encoder = build_encoder(config).to(device).eval()
    decoder = DenseDecoder512().to(device).eval()
    encoder.load_state_dict(checkpoint["en"], strict=True)
    decoder.load_state_dict(checkpoint["de"], strict=True)

    paths = []
    for root in args.image_root:
        root_paths = sorted(p for p in Path(root).rglob("*") if p.suffix.lower() in IMAGE_EXTENSIONS)
        if args.max_images_per_root:
            root_paths = root_paths[: args.max_images_per_root]
        paths.extend(root_paths)
    paths = sorted(paths)
    if args.offset_images:
        paths = paths[args.offset_images:]
    if args.max_images:
        paths = paths[: args.max_images]
    rows = []

    with torch.no_grad():
        for path in paths:
            _, cover_tensor = load_image(path)
            cover_tensor = cover_tensor.unsqueeze(0).to(device)
            for trial in range(args.trials_per_image):
                payload, useful_bits = make_payload(1, args.payload_bpp, device)
                stego = encoder(cover_tensor, payload)
                stego_image = Image.fromarray(to_uint8_array(stego))
                target = payload.reshape(1, -1)
                for attack in args.attacks:
                    attacked = attack_image(stego_image, attack)
                    attacked_tensor = pil_to_normalized_tensor(attacked).unsqueeze(0).to(device)
                    decoded = decoder(attacked_tensor)
                    pred = (decoded >= 0.0).float().reshape(1, -1)
                    useful_ber = (pred[:, :useful_bits] != target[:, :useful_bits]).float().mean()
                    rows.append(
                        {
                            "image": str(path),
                            "trial": trial,
                            "attack": attack,
                            "payload_bpp": args.payload_bpp,
                            "useful_bits": useful_bits,
                            "useful_ber": float(useful_ber.item()),
                        }
                    )

    grouped = {}
    for row in rows:
        grouped.setdefault(row["attack"], []).append(row["useful_ber"])
    summary = {
        attack: {
            "mean_useful_ber": float(np.mean(values)),
            "max_useful_ber": float(np.max(values)),
            "n": len(values),
        }
        for attack, values in grouped.items()
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
