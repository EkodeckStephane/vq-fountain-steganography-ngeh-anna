from __future__ import annotations

import argparse
import csv
import json
import pickle
import random
import sys
import types
from pathlib import Path

import numpy as np
from PIL import Image
import torch

ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
DEFAULT_BASELINE = REPO_ROOT / "05_artifacts" / "baselines" / "HiDDeN"


def main() -> int:
    parser = argparse.ArgumentParser(description="Executable HiDDeN public-checkpoint baseline smoke.")
    parser.add_argument("--baseline-dir", default=str(DEFAULT_BASELINE))
    parser.add_argument(
        "--checkpoint",
        default=str(DEFAULT_BASELINE / "experiments" / "combined-noise" / "checkpoints" / "combined-noise--epoch-400.pyt"),
    )
    parser.add_argument(
        "--options-file",
        default=str(DEFAULT_BASELINE / "experiments" / "combined-noise" / "options-and-config.pickle"),
    )
    parser.add_argument(
        "--source-image",
        default=str(REPO_ROOT / "05_artifacts" / "results" / "raw" / "vq_fountain_real_vqgan_payload_sample_128px.png"),
    )
    parser.add_argument("--trials", type=int, default=5)
    parser.add_argument("--seed", default="hidden-baseline-smoke")
    parser.add_argument(
        "--out-csv",
        default=str(REPO_ROOT / "05_artifacts" / "results" / "tables" / "hidden_baseline_smoke.csv"),
    )
    parser.add_argument(
        "--out-json",
        default=str(REPO_ROOT / "05_artifacts" / "results" / "raw" / "hidden_baseline_smoke.json"),
    )
    args = parser.parse_args()

    baseline_dir = Path(args.baseline_dir)
    install_torchvision_stub()
    sys.path.insert(0, str(baseline_dir))

    from model.hidden import Hidden
    from noise_layers.noiser import Noiser

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    train_options, noise_config, hidden_config = load_options(Path(args.options_file))
    noiser = Noiser(noise_config, device)
    hidden_net = Hidden(hidden_config, device, noiser, None)
    checkpoint = torch.load(args.checkpoint, map_location=device, weights_only=False)
    hidden_net.encoder_decoder.load_state_dict(checkpoint["enc-dec-model"])
    hidden_net.discriminator.load_state_dict(checkpoint["discrim-model"])

    image_tensor = load_image(Path(args.source_image), hidden_config.H, hidden_config.W).to(device)
    rng = random.Random(args.seed)
    rows = []
    mse_loss = torch.nn.MSELoss()
    for trial in range(args.trials):
        bits = [rng.randrange(2) for _ in range(hidden_config.message_length)]
        message = torch.tensor([bits], dtype=torch.float32, device=device)
        hidden_net.encoder_decoder.eval()
        with torch.no_grad():
            encoded_images, _noised_images, decoded_messages = hidden_net.encoder_decoder(image_tensor, message)
        decoded = decoded_messages.detach().cpu().numpy().round().clip(0, 1).astype(np.int32)[0].tolist()
        errors = sum(int(left != right) for left, right in zip(bits, decoded))
        encoder_mse = float(mse_loss(encoded_images, image_tensor).item())
        decoder_mse = float(mse_loss(decoded_messages, message).item())
        rows.append(
            {
                "baseline": "HiDDeN",
                "checkpoint": display_path(Path(args.checkpoint)),
                "source_image": display_path(Path(args.source_image)),
                "trial": trial,
                "message_bits": hidden_config.message_length,
                "bit_errors": errors,
                "bit_error_rate": round(errors / hidden_config.message_length, 8),
                "exact_recovery": errors == 0,
                "encoder_mse": round(encoder_mse, 8),
                "decoder_mse": round(decoder_mse, 8),
                "reported_bitwise_error": round(errors / hidden_config.message_length, 8),
            }
        )

    summary = {
        "baseline": "HiDDeN",
        "checkpoint": display_path(Path(args.checkpoint)),
        "options_file": display_path(Path(args.options_file)),
        "source_image": display_path(Path(args.source_image)),
        "trials": args.trials,
        "message_bits": hidden_config.message_length,
        "exact_trials": sum(1 for row in rows if row["exact_recovery"]),
        "mean_bit_error_rate": round(float(np.mean([row["bit_error_rate"] for row in rows])), 8),
        "rows": rows,
    }
    write_csv(Path(args.out_csv), rows)
    write_json(Path(args.out_json), summary)
    print(json.dumps({"csv": display_path(Path(args.out_csv)), "json": display_path(Path(args.out_json)), **summary}, indent=2))
    return 0


def install_torchvision_stub() -> None:
    if "torchvision" in sys.modules:
        return
    torchvision = types.ModuleType("torchvision")
    torchvision.models = types.SimpleNamespace()
    sys.modules["torchvision"] = torchvision


def load_options(path: Path):
    with path.open("rb") as handle:
        train_options = pickle.load(handle)
        noise_config = pickle.load(handle)
        hidden_config = pickle.load(handle)
        if not hasattr(hidden_config, "enable_fp16"):
            setattr(hidden_config, "enable_fp16", False)
    return train_options, noise_config, hidden_config


def load_image(path: Path, height: int, width: int) -> torch.Tensor:
    image = Image.open(path).convert("RGB")
    if image.width < width or image.height < height:
        image = image.resize((max(width, image.width), max(height, image.height)), Image.Resampling.BICUBIC)
    left = (image.width - width) // 2
    top = (image.height - height) // 2
    image = image.crop((left, top, left + width, top + height))
    array = np.asarray(image, dtype=np.float32)
    tensor = torch.from_numpy(array).permute(2, 0, 1).unsqueeze(0)
    return tensor / 127.5 - 1.0


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


if __name__ == "__main__":
    raise SystemExit(main())
