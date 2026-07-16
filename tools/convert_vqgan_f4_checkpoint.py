"""Convert the old fusing/vqgan-f4-8192 checkpoint to modern diffusers keys."""

from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path

import torch
from diffusers import VQModel


def _rewrite_key(key: str) -> str | None:
    if ".attn_1.qkv." in key:
        return None

    replacements = {
        ".block_1.": ".resnets.0.",
        ".block_2.": ".resnets.1.",
        ".attn_1.norm.": ".attentions.0.group_norm.",
        ".attn_1.q.": ".attentions.0.to_q.",
        ".attn_1.k.": ".attentions.0.to_k.",
        ".attn_1.v.": ".attentions.0.to_v.",
        ".attn_1.proj_out.": ".attentions.0.to_out.0.",
        ".nin_shortcut.": ".conv_shortcut.",
    }
    for old, new in replacements.items():
        key = key.replace(old, new)

    key = key.replace("encoder.norm_out.", "encoder.conv_norm_out.")
    key = key.replace("decoder.norm_out.", "decoder.conv_norm_out.")
    key = key.replace("encoder.mid.", "encoder.mid_block.")
    key = key.replace("decoder.mid.", "decoder.mid_block.")

    match = re.match(r"encoder\.down\.(\d+)\.block\.(\d+)\.(.+)", key)
    if match:
        block, resnet, suffix = match.groups()
        return f"encoder.down_blocks.{block}.resnets.{resnet}.{suffix}"

    match = re.match(r"encoder\.down\.(\d+)\.downsample\.conv\.(.+)", key)
    if match:
        block, suffix = match.groups()
        return f"encoder.down_blocks.{block}.downsamplers.0.conv.{suffix}"

    match = re.match(r"decoder\.up\.(\d+)\.block\.(\d+)\.(.+)", key)
    if match:
        old_block, resnet, suffix = match.groups()
        new_block = 2 - int(old_block)
        return f"decoder.up_blocks.{new_block}.resnets.{resnet}.{suffix}"

    match = re.match(r"decoder\.up\.(\d+)\.upsample\.conv\.(.+)", key)
    if match:
        old_block, suffix = match.groups()
        new_block = 2 - int(old_block)
        return f"decoder.up_blocks.{new_block}.upsamplers.0.conv.{suffix}"

    return key


def convert_checkpoint(source_dir: Path, output_dir: Path) -> dict:
    source_config_path = source_dir / "config.json"
    source_weights_path = source_dir / "diffusion_pytorch_model.bin"
    output_dir.mkdir(parents=True, exist_ok=True)

    with source_config_path.open("r", encoding="utf-8") as handle:
        config = json.load(handle)
    config["mid_block_add_attention"] = True

    model = VQModel.from_config(config)
    target_state = model.state_dict()

    raw_state = torch.load(source_weights_path, map_location="cpu")
    if isinstance(raw_state, dict) and "state_dict" in raw_state:
        raw_state = raw_state["state_dict"]

    converted_state = {}
    dropped_keys = []
    shape_mismatches = []
    duplicate_targets = []

    for old_key, tensor in raw_state.items():
        new_key = _rewrite_key(old_key)
        if new_key is None:
            dropped_keys.append(old_key)
            continue
        if new_key not in target_state:
            dropped_keys.append(old_key)
            continue
        if len(tensor.shape) == 4 and tuple(tensor.shape[-2:]) == (1, 1):
            squeezed = tensor[:, :, 0, 0]
            if tuple(squeezed.shape) == tuple(target_state[new_key].shape):
                tensor = squeezed

        if tuple(tensor.shape) != tuple(target_state[new_key].shape):
            shape_mismatches.append(
                {
                    "source": old_key,
                    "target": new_key,
                    "source_shape": list(tensor.shape),
                    "target_shape": list(target_state[new_key].shape),
                }
            )
            continue
        if new_key in converted_state:
            duplicate_targets.append({"source": old_key, "target": new_key})
            continue
        converted_state[new_key] = tensor

    missing_keys = sorted(set(target_state) - set(converted_state))
    unexpected_targets = sorted(set(converted_state) - set(target_state))

    if missing_keys or unexpected_targets or shape_mismatches or duplicate_targets:
        raise RuntimeError(
            "Incomplete VQGAN conversion: "
            f"{len(missing_keys)} missing, "
            f"{len(unexpected_targets)} unexpected, "
            f"{len(shape_mismatches)} shape mismatches, "
            f"{len(duplicate_targets)} duplicate targets"
        )

    shutil.copyfile(source_config_path, output_dir / "source_config.json")
    with (output_dir / "config.json").open("w", encoding="utf-8") as handle:
        json.dump(config, handle, indent=2)
        handle.write("\n")
    torch.save(converted_state, output_dir / "diffusion_pytorch_model.bin")

    report = {
        "source_dir": source_dir.as_posix(),
        "output_dir": output_dir.as_posix(),
        "source_tensor_count": len(raw_state),
        "target_tensor_count": len(target_state),
        "converted_tensor_count": len(converted_state),
        "dropped_source_keys": dropped_keys,
        "missing_target_keys": missing_keys,
        "unexpected_targets": unexpected_targets,
        "shape_mismatches": shape_mismatches,
        "duplicate_targets": duplicate_targets,
        "mid_block_add_attention": True,
    }
    with (output_dir / "conversion_report.json").open("w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
        handle.write("\n")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source-dir",
        type=Path,
        default=Path("05_artifacts/models/vqgan_f4_8192_diffusers_compat"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("05_artifacts/models/vqgan_f4_8192_diffusers_converted"),
    )
    args = parser.parse_args()

    report = convert_checkpoint(args.source_dir, args.output_dir)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
