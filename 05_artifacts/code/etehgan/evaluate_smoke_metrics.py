import argparse
import csv
import json
import math
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from reedsolo import RSCodec

from models import DenseDecoder512


TOTAL_BITS = 524_288
ECC_BYTES = 32


def pil_to_normalized_tensor(pil_image):
    arr = np.asarray(pil_image.convert("RGB"), dtype=np.float32) / 255.0
    tensor = torch.from_numpy(arr).permute(2, 0, 1)
    return (tensor - 0.5) / 0.5


def bytes_to_bits(payload):
    bits = []
    for byte in payload:
        bits.extend(int(bit) for bit in f"{byte:08b}")
    return np.asarray(bits, dtype=np.uint8)


def psnr(cover, stego):
    mse = np.mean((cover.astype(np.float64) - stego.astype(np.float64)) ** 2)
    if mse == 0:
        return float("inf")
    return 20.0 * math.log10(255.0 / math.sqrt(mse))


def global_ssim(cover, stego):
    # Publication experiments should use a standard windowed SSIM library.
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


def decode_raw_bits(stego_path, weights_path, device):
    decoder = DenseDecoder512().to(device).eval()
    checkpoint = torch.load(weights_path, map_location=device)
    decoder.load_state_dict(checkpoint["de"])
    image = Image.open(stego_path).convert("RGB").resize((512, 512), Image.Resampling.BICUBIC)
    tensor = pil_to_normalized_tensor(image).unsqueeze(0).to(device)
    with torch.no_grad():
        decoded = decoder(tensor)
    return (decoded >= 0.0).int().cpu().numpy().astype(np.uint8).flatten()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cover", required=True)
    parser.add_argument("--stego", required=True)
    parser.add_argument("--payload", required=True)
    parser.add_argument("--recovered", required=True)
    parser.add_argument("--weights", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-csv", required=True)
    args = parser.parse_args()

    cover_img = Image.open(args.cover).convert("RGB").resize((512, 512), Image.Resampling.BICUBIC)
    stego_img = Image.open(args.stego).convert("RGB").resize((512, 512), Image.Resampling.BICUBIC)
    cover_arr = np.asarray(cover_img)
    stego_arr = np.asarray(stego_img)

    payload_bytes = Path(args.payload).read_bytes()
    recovered_bytes = Path(args.recovered).read_bytes()

    ecc_engine = RSCodec(ECC_BYTES)
    ecc_payload = bytes(ecc_engine.encode(payload_bytes))
    expected_prefix_bits = np.concatenate(
        [bytes_to_bits(ecc_payload), np.zeros(16, dtype=np.uint8)]
    )
    decoded_bits = decode_raw_bits(args.stego, args.weights, torch.device("cuda" if torch.cuda.is_available() else "cpu"))
    prefix = decoded_bits[: len(expected_prefix_bits)]
    raw_bit_errors = int(np.count_nonzero(prefix != expected_prefix_bits))

    height, width = cover_arr.shape[:2]
    pixels = height * width
    payload_bits = len(payload_bytes) * 8
    ecc_payload_bits = len(ecc_payload) * 8
    pre_padding_bits = ecc_payload_bits + 16

    metrics = {
        "cover": args.cover,
        "stego": args.stego,
        "payload": args.payload,
        "recovered": args.recovered,
        "width": width,
        "height": height,
        "pixels": pixels,
        "payload_bytes": len(payload_bytes),
        "payload_bits": payload_bits,
        "ecc_bytes": ECC_BYTES,
        "ecc_encoded_bytes": len(ecc_payload),
        "ecc_payload_bits": ecc_payload_bits,
        "delimiter_bits": 16,
        "pre_padding_bits": pre_padding_bits,
        "random_padding_bits": TOTAL_BITS - pre_padding_bits,
        "total_bitstream_capacity": TOTAL_BITS,
        "nominal_bpp": TOTAL_BITS / pixels,
        "effective_user_bpp": payload_bits / pixels,
        "ecc_inclusive_bpp": pre_padding_bits / pixels,
        "psnr_db": psnr(cover_arr, stego_arr),
        "global_ssim": float(global_ssim(cover_arr, stego_arr)),
        "raw_prefix_bits_compared": int(len(expected_prefix_bits)),
        "raw_prefix_bit_errors_before_ecc": raw_bit_errors,
        "raw_prefix_ber_before_ecc": raw_bit_errors / len(expected_prefix_bits),
        "exact_recovery": payload_bytes == recovered_bytes,
        "recovered_bytes": len(recovered_bytes),
        "corrected_byte_errors": 0 if payload_bytes == recovered_bytes else None,
    }

    Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out_csv).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out_json).write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    with open(args.out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(metrics.keys()))
        writer.writeheader()
        writer.writerow(metrics)

    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()

