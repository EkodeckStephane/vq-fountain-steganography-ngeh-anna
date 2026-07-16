from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image
import torch

ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke test for a real diffusers VQModel encoder/decoder.")
    parser.add_argument("--model-id", default="fusing/vqgan-dummy")
    parser.add_argument("--image-size", type=int, default=64)
    parser.add_argument("--seed", type=int, default=1234)
    parser.add_argument("--device", default="cpu")
    parser.add_argument(
        "--out-image",
        default=str(REPO_ROOT / "05_artifacts" / "results" / "raw" / "vq_fountain_real_vqmodel_smoke.png"),
    )
    parser.add_argument(
        "--out-json",
        default=str(REPO_ROOT / "05_artifacts" / "results" / "raw" / "vq_fountain_real_vqmodel_smoke.json"),
    )
    args = parser.parse_args()

    try:
        from diffusers import VQModel
    except Exception as exc:  # pragma: no cover - optional dependency
        raise SystemExit(f"diffusers VQModel is unavailable: {exc}") from exc

    image = synthetic_image(args.image_size, args.seed)
    tensor = image_to_tensor(image).to(args.device)
    model = VQModel.from_pretrained(args.model_id).to(args.device)
    model.eval()
    with torch.no_grad():
        encoded = model.encode(tensor)
        latents = encoded.latents
        decoded = model.decode(latents).sample
    out_image = tensor_to_image(decoded)
    out_path = Path(args.out_image)
    json_path = Path(args.out_json)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    out_image.save(out_path)
    payload = {
        "model_id": args.model_id,
        "device": args.device,
        "seed": args.seed,
        "input_size": image.size,
        "latent_shape": list(latents.shape),
        "out_image": display_path(out_path),
    }
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def synthetic_image(size: int, seed: int) -> Image.Image:
    rng = np.random.default_rng(seed)
    base = np.linspace(0, 1, size, dtype=np.float32)
    x, y = np.meshgrid(base, base)
    array = np.stack(
        [
            x,
            y,
            0.5 * x + 0.5 * y,
        ],
        axis=-1,
    )
    array += rng.normal(0.0, 0.02, size=array.shape).astype(np.float32)
    return Image.fromarray(np.clip(array * 255.0, 0, 255).astype(np.uint8), mode="RGB")


def image_to_tensor(image: Image.Image) -> torch.Tensor:
    array = np.asarray(image.convert("RGB")).astype(np.float32) / 127.5 - 1.0
    return torch.from_numpy(array).permute(2, 0, 1).unsqueeze(0)


def tensor_to_image(tensor: torch.Tensor) -> Image.Image:
    array = tensor.detach().cpu().clamp(-1.0, 1.0).squeeze(0).permute(1, 2, 0).numpy()
    array = (array + 1.0) * 127.5
    return Image.fromarray(np.clip(array, 0, 255).astype(np.uint8), mode="RGB")


def display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


if __name__ == "__main__":
    raise SystemExit(main())
