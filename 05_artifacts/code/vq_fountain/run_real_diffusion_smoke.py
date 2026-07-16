from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import torch

ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke test for a real diffusers text-to-image generator.")
    parser.add_argument("--model-id", default="diffusers/tiny-stable-diffusion-torch")
    parser.add_argument("--prompt", default="a clean geometric test image")
    parser.add_argument("--steps", type=int, default=2)
    parser.add_argument("--seed", type=int, default=1234)
    parser.add_argument("--device", default="cpu")
    parser.add_argument(
        "--out-image",
        default=str(REPO_ROOT / "05_artifacts" / "results" / "raw" / "vq_fountain_real_diffusion_smoke.png"),
    )
    parser.add_argument(
        "--out-json",
        default=str(REPO_ROOT / "05_artifacts" / "results" / "raw" / "vq_fountain_real_diffusion_smoke.json"),
    )
    args = parser.parse_args()

    try:
        from diffusers import StableDiffusionPipeline
    except Exception as exc:  # pragma: no cover - depends on optional packages
        raise SystemExit(f"diffusers StableDiffusionPipeline is unavailable: {exc}") from exc

    generator = torch.Generator(device=args.device).manual_seed(args.seed)
    pipe = StableDiffusionPipeline.from_pretrained(args.model_id, safety_checker=None)
    pipe = pipe.to(args.device)
    image = pipe(args.prompt, num_inference_steps=args.steps, generator=generator).images[0]

    out_image = Path(args.out_image)
    out_json = Path(args.out_json)
    out_image.parent.mkdir(parents=True, exist_ok=True)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    image.save(out_image)
    payload = {
        "model_id": args.model_id,
        "prompt": args.prompt,
        "steps": args.steps,
        "seed": args.seed,
        "device": args.device,
        "image_size": image.size,
        "out_image": display_path(out_image),
    }
    out_json.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


if __name__ == "__main__":
    raise SystemExit(main())
