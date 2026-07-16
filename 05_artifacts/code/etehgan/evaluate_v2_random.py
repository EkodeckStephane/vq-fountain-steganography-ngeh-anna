import argparse
import csv
import json
import math
import random
from pathlib import Path

import numpy as np
import torch
from PIL import Image

from models import DenseDecoder512, DenseEncoder512, ResidualDenseEncoder512


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
TOTAL_BITS = 2 * 512 * 512


def seed_everything(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def load_image(path):
    image = Image.open(path).convert("RGB")
    width, height = image.size
    side = min(width, height)
    left = (width - side) // 2
    top = (height - side) // 2
    image = image.crop((left, top, left + side, top + side))
    image = image.resize((512, 512), Image.Resampling.BICUBIC)
    arr = np.asarray(image, dtype=np.float32) / 255.0
    tensor = torch.from_numpy(arr).permute(2, 0, 1)
    return image, (tensor - 0.5) / 0.5


def make_payload(batch_size, bpp, device):
    useful_bits = int(round(512 * 512 * bpp))
    if useful_bits < 1 or useful_bits > TOTAL_BITS:
        raise ValueError(f"bpp must imply 1..{TOTAL_BITS} bits; got {bpp}")
    flat = torch.zeros(batch_size, TOTAL_BITS, device=device)
    flat[:, :useful_bits] = torch.randint(0, 2, (batch_size, useful_bits), device=device).float()
    return flat.view(batch_size, 2, 512, 512), useful_bits


def to_uint8_array(tensor):
    arr = ((tensor.squeeze(0) + 1.0) * 127.5).clamp(0, 255)
    return arr.byte().permute(1, 2, 0).cpu().numpy()


def psnr(cover, stego):
    mse = np.mean((cover.astype(np.float64) - stego.astype(np.float64)) ** 2)
    if mse == 0:
        return float("inf")
    return 20.0 * math.log10(255.0 / math.sqrt(mse))


def global_ssim(cover, stego):
    x = cover.astype(np.float64)
    y = stego.astype(np.float64)
    c1 = (0.01 * 255) ** 2
    c2 = (0.03 * 255) ** 2
    mux = x.mean()
    muy = y.mean()
    sigx = ((x - mux) ** 2).mean()
    sigy = ((y - muy) ** 2).mean()
    sigxy = ((x - mux) * (y - muy)).mean()
    return ((2 * mux * muy + c1) * (2 * sigxy + c2)) / (
        (mux**2 + muy**2 + c1) * (sigx + sigy + c2)
    )


def build_encoder(config):
    mode = config.get("encoder_mode", "absolute")
    if mode == "residual":
        return ResidualDenseEncoder512(config.get("residual_strength", 0.1))
    return DenseEncoder512()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--image-root", required=True, nargs="+")
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--payload-bpp", type=float, required=True)
    parser.add_argument("--trials-per-image", type=int, default=1)
    parser.add_argument("--out-csv", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--seed", type=int, default=123)
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
    if not paths:
        raise ValueError(f"No images found under {args.image_root}")

    rows = []
    with torch.no_grad():
        for path in paths:
            cover_image, cover_tensor = load_image(path)
            cover_arr = np.asarray(cover_image.convert("RGB"))
            cover_tensor = cover_tensor.unsqueeze(0).to(device)
            for trial in range(args.trials_per_image):
                payload, useful_bits = make_payload(1, args.payload_bpp, device)
                stego = encoder(cover_tensor, payload)
                decoded = decoder(stego)
                pred = (decoded >= 0.0).float().reshape(1, -1)
                target = payload.reshape(1, -1)
                useful_ber = (pred[:, :useful_bits] != target[:, :useful_bits]).float().mean()
                full_ber = (pred != target).float().mean()
                stego_arr = to_uint8_array(stego)
                rows.append(
                    {
                        "image": str(path),
                        "trial": trial,
                        "payload_bpp": args.payload_bpp,
                        "useful_bits": useful_bits,
                        "useful_ber": float(useful_ber.item()),
                        "full_ber": float(full_ber.item()),
                        "psnr_db": psnr(cover_arr, stego_arr),
                        "global_ssim": float(global_ssim(cover_arr, stego_arr)),
                    }
                )

    summary = {
        "checkpoint": args.checkpoint,
        "payload_bpp": args.payload_bpp,
        "num_rows": len(rows),
        "mean_useful_ber": float(np.mean([r["useful_ber"] for r in rows])),
        "mean_full_ber": float(np.mean([r["full_ber"] for r in rows])),
        "mean_psnr_db": float(np.mean([r["psnr_db"] for r in rows])),
        "mean_global_ssim": float(np.mean([r["global_ssim"] for r in rows])),
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
