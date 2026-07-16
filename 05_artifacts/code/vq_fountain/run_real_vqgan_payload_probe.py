from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
from dataclasses import dataclass
from pathlib import Path
import sys

import numpy as np
from PIL import Image
import torch

ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
sys.path.insert(0, str(ROOT))

from vq_fountain.bitstream import PayloadDecodeError, pack_payload, unpack_payload
from vq_fountain.fountain import (
    FountainDecodeError,
    FountainSymbol,
    decode_symbols,
    encode_symbols,
    symbol_crc_valid,
)
from vq_fountain.image_attacks import apply_attack, should_drop_image
from vq_fountain.token_sampler import PriorBinCodec, bytes_to_values, values_to_bytes


@dataclass(frozen=True)
class CalibratedToken:
    token_id: int
    target_value: int
    received_value: int
    majority_fraction: float
    unique_received_tokens: int


def main() -> int:
    parser = argparse.ArgumentParser(description="Payload recovery probe through a converted real VQGAN VQModel.")
    parser.add_argument("--model-dir", default=str(REPO_ROOT / "05_artifacts" / "models" / "vqgan_f4_8192_diffusers_converted"))
    parser.add_argument("--model-subfolder", default=None)
    parser.add_argument("--allow-download", action="store_true")
    parser.add_argument("--payload-bytes", type=int, default=4)
    parser.add_argument("--bits-per-token", type=int, default=1)
    parser.add_argument("--block-size", type=int, default=2)
    parser.add_argument("--overhead", type=float, default=2.0)
    parser.add_argument("--latent-side", type=int, default=16)
    parser.add_argument("--macro-cell-size", type=int, default=4)
    parser.add_argument("--symbols-per-image", type=int, default=1)
    parser.add_argument("--calibration-count", type=int, default=256)
    parser.add_argument("--calibration-threshold", type=float, default=0.90)
    parser.add_argument("--calibration-batch-size", type=int, default=8)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--seed", default="real-vqgan-payload")
    parser.add_argument("--calibration-seed", default=None)
    parser.add_argument("--test-seeds", nargs="*", default=None)
    parser.add_argument("--attacks", nargs="+", default=["clean", "jpeg85", "resize075"])
    parser.add_argument("--device", default="cpu")
    parser.add_argument(
        "--out-csv",
        default=str(REPO_ROOT / "05_artifacts" / "results" / "tables" / "vq_fountain_real_vqgan_payload_probe.csv"),
    )
    parser.add_argument(
        "--out-json",
        default=str(REPO_ROOT / "05_artifacts" / "results" / "raw" / "vq_fountain_real_vqgan_payload_probe.json"),
    )
    parser.add_argument(
        "--sample-image",
        default=str(REPO_ROOT / "05_artifacts" / "results" / "raw" / "vq_fountain_real_vqgan_payload_sample.png"),
    )
    args = parser.parse_args()

    if args.bits_per_token != 1:
        raise SystemExit("the real VQGAN payload probe currently supports bits_per_token=1")
    if args.macro_cell_size <= 0 or args.latent_side % args.macro_cell_size != 0:
        raise SystemExit("macro_cell_size must divide latent_side")

    try:
        from diffusers import VQModel
    except Exception as exc:  # pragma: no cover - optional dependency
        raise SystemExit(f"diffusers VQModel is unavailable: {exc}") from exc

    device = torch.device(args.device)
    model = VQModel.from_pretrained(
        args.model_dir,
        subfolder=args.model_subfolder,
        local_files_only=not args.allow_download,
        use_safetensors=False,
    ).to(device)
    model.eval()
    calibration_seed = args.calibration_seed or f"{args.seed}:calibration"

    codebook = model.quantize.embedding.weight.detach().cpu().numpy()
    prior = np.ones(model.config.num_vq_embeddings, dtype=np.float64) / float(model.config.num_vq_embeddings)
    codec = PriorBinCodec(prior=prior, capacity_bits=args.bits_per_token, codebook=codebook, mode="projection")

    calibration = calibrate_tokens(
        model=model,
        codec=codec,
        latent_side=args.latent_side,
        count=args.calibration_count,
        threshold=args.calibration_threshold,
        batch_size=args.calibration_batch_size,
        seed=calibration_seed,
        device=device,
    )
    pools = {
        value: [item for item in calibration if item.received_value == value and item.majority_fraction >= args.calibration_threshold]
        for value in range(1 << args.bits_per_token)
    }
    missing = [value for value, items in pools.items() if not items]
    if missing:
        raise SystemExit(f"calibration found no stable tokens for values: {missing}")

    test_seeds = args.test_seeds or [args.seed]
    rows = []
    for seed_index, test_seed in enumerate(test_seeds):
        generated = generate_payload_images(
            model=model,
            codec=codec,
            pools=pools,
            payload_bytes=args.payload_bytes,
            bits_per_token=args.bits_per_token,
            block_size=args.block_size,
            overhead=args.overhead,
            latent_side=args.latent_side,
            macro_cell_size=args.macro_cell_size,
            symbols_per_image=args.symbols_per_image,
            batch_size=args.batch_size,
            seed=test_seed,
            device=device,
        )
        sample_path = sample_path_for_seed(Path(args.sample_image), seed_index, test_seed, len(test_seeds))
        sample_path.parent.mkdir(parents=True, exist_ok=True)
        generated["images"][0].save(sample_path)

        for attack in args.attacks:
            row = recover_payload(
                model=model,
                codec=codec,
                generated=generated,
                attack=attack,
                bits_per_token=args.bits_per_token,
                block_size=args.block_size,
                latent_side=args.latent_side,
                macro_cell_size=args.macro_cell_size,
                batch_size=args.batch_size,
                seed=test_seed,
                device=device,
            )
            row.update(
                {
                    "model_dir": model_reference(args.model_dir),
                    "model_subfolder": args.model_subfolder or "",
                    "payload_bytes": args.payload_bytes,
                    "packet_bytes": generated["packet_bytes"],
                    "bits_per_token": args.bits_per_token,
                    "block_size": args.block_size,
                    "overhead": args.overhead,
                    "latent_side": args.latent_side,
                    "macro_cell_size": args.macro_cell_size,
                    "macro_cells_per_image": generated["macro_cells_per_image"],
                    "symbols_per_image": args.symbols_per_image,
                    "source_symbols": generated["source_symbols"],
                    "encoded_symbols": generated["encoded_symbols"],
                    "image_count": len(generated["images"]),
                    "calibration_count": args.calibration_count,
                    "calibration_threshold": args.calibration_threshold,
                    "calibration_seed": calibration_seed,
                    "payload_seed": test_seed,
                    "stable_pool_0": len(pools[0]),
                    "stable_pool_1": len(pools[1]),
                    "sample_image": display_path(sample_path),
                }
            )
            rows.append(row)

    write_csv(Path(args.out_csv), rows)
    payload = {
        "rows": rows,
        "calibration_summary": {
            "count": len(calibration),
            "threshold": args.calibration_threshold,
            "calibration_seed": calibration_seed,
            "test_seeds": test_seeds,
            "stable_pool_0": len(pools[0]),
            "stable_pool_1": len(pools[1]),
            "best_by_value": {
                str(value): [
                    {
                        "token_id": item.token_id,
                        "target_value": item.target_value,
                        "received_value": item.received_value,
                        "majority_fraction": round(item.majority_fraction, 6),
                        "unique_received_tokens": item.unique_received_tokens,
                    }
                    for item in sorted(pools[value], key=lambda item: (-item.majority_fraction, item.token_id))[:20]
                ]
                for value in pools
            },
        },
    }
    write_json(Path(args.out_json), payload)
    print(json.dumps({"csv": display_path(Path(args.out_csv)), "json": display_path(Path(args.out_json)), "rows": len(rows)}, indent=2))
    return 0


def calibrate_tokens(
    model,
    codec: PriorBinCodec,
    latent_side: int,
    count: int,
    threshold: float,
    batch_size: int,
    seed: int | str,
    device: torch.device,
) -> list[CalibratedToken]:
    del threshold
    rng = np.random.default_rng(seed_to_int(f"{seed}:calibration"))
    candidates = rng.choice(model.config.num_vq_embeddings, size=count, replace=False)
    value_lookup = codec.bin_for_token
    rows: list[CalibratedToken] = []
    for start in range(0, len(candidates), batch_size):
        batch_tokens = candidates[start : start + batch_size]
        grids = np.repeat(batch_tokens[:, None], latent_side * latent_side, axis=1).astype(np.int64)
        received = decode_encode_token_grids(
            model=model,
            token_grids=grids.reshape(len(batch_tokens), latent_side, latent_side),
            batch_size=batch_size,
            device=device,
        )
        for token_id, received_grid in zip(batch_tokens.tolist(), received):
            values = value_lookup[received_grid.reshape(-1)]
            counts = np.bincount(values, minlength=codec.bin_count)
            received_value = int(counts.argmax())
            majority_fraction = float(counts[received_value] / values.size)
            rows.append(
                CalibratedToken(
                    token_id=int(token_id),
                    target_value=codec.decode_value(int(token_id)),
                    received_value=received_value,
                    majority_fraction=majority_fraction,
                    unique_received_tokens=int(np.unique(received_grid).size),
                )
            )
    return rows


def generate_payload_images(
    model,
    codec: PriorBinCodec,
    pools: dict[int, list[CalibratedToken]],
    payload_bytes: int,
    bits_per_token: int,
    block_size: int,
    overhead: float,
    latent_side: int,
    macro_cell_size: int,
    symbols_per_image: int,
    batch_size: int,
    seed: int | str,
    device: torch.device,
) -> dict[str, object]:
    payload = deterministic_payload(payload_bytes, seed)
    packet = pack_payload(payload)
    symbols = encode_symbols(packet, block_size=block_size, overhead=overhead, seed=seed)
    macro_cells = macro_cell_positions(latent_side, macro_cell_size)
    if symbols_per_image <= 0:
        raise ValueError("symbols_per_image must be positive")
    if block_size * 8 % bits_per_token != 0:
        raise ValueError("block_size bits must be divisible by bits_per_token")
    values_per_symbol = block_size * 8 // bits_per_token
    if values_per_symbol * symbols_per_image > len(macro_cells):
        raise ValueError("symbols_per_image does not fit inside one macro-cell image")

    token_grids = []
    symbol_values = []
    image_symbols = []
    image_symbol_values = []
    for image_index, start in enumerate(range(0, len(symbols), symbols_per_image)):
        symbol_group = symbols[start : start + symbols_per_image]
        value_group = []
        grid = np.zeros((latent_side, latent_side), dtype=np.int64)
        used_cells = 0
        for local_symbol_index, symbol in enumerate(symbol_group):
            values = bytes_to_values(symbol.data, bits_per_token)
            values = values[:values_per_symbol]
            symbol_values.append(values)
            value_group.append(values)
            cell_offset = local_symbol_index * values_per_symbol
            for value_index, value in enumerate(values):
                cell_index = cell_offset + value_index
                row_start, col_start = macro_cells[cell_index]
                token = select_calibrated_token(
                    pools[int(value)],
                    key=f"{seed}:symbol:{symbol.symbol_id}:cell:{cell_index}",
                )
                grid[row_start : row_start + macro_cell_size, col_start : col_start + macro_cell_size] = token
            used_cells = max(used_cells, cell_offset + len(values))
        for cell_index, (row_start, col_start) in enumerate(macro_cells):
            if cell_index < used_cells:
                continue
            value = int(stable_random(f"{seed}:filler:{image_index}:{cell_index}") % codec.bin_count)
            token = select_calibrated_token(pools[value], key=f"{seed}:filler:{image_index}:cell:{cell_index}")
            grid[row_start : row_start + macro_cell_size, col_start : col_start + macro_cell_size] = token
        token_grids.append(grid)
        image_symbols.append(symbol_group)
        image_symbol_values.append(value_group)

    images = decode_token_grids_to_images(
        model=model,
        token_grids=np.asarray(token_grids, dtype=np.int64),
        batch_size=batch_size,
        device=device,
    )
    return {
        "payload": payload,
        "packet_bytes": len(packet),
        "symbols": symbols,
        "symbol_values": symbol_values,
        "image_symbols": image_symbols,
        "image_symbol_values": image_symbol_values,
        "token_grids": token_grids,
        "images": images,
        "macro_cells_per_image": len(macro_cells),
        "symbols_per_image": symbols_per_image,
        "values_per_symbol": values_per_symbol,
        "source_symbols": symbols[0].source_count if symbols else 0,
        "encoded_symbols": len(symbols),
    }


def recover_payload(
    model,
    codec: PriorBinCodec,
    generated: dict[str, object],
    attack: str,
    bits_per_token: int,
    block_size: int,
    latent_side: int,
    macro_cell_size: int,
    batch_size: int,
    seed: int | str,
    device: torch.device,
) -> dict[str, object]:
    attacked = []
    attacked_indices = []
    dropped_images = 0
    for index, image in enumerate(generated["images"]):
        if should_drop_image(attack, image_index=index, seed=seed):
            dropped_images += 1
            continue
        attacked_indices.append(index)
        attacked.append(apply_attack(image, attack, seed=f"{seed}:{attack}:{index}"))

    received_by_index: dict[int, np.ndarray] = {}
    if attacked:
        received_grids = encode_images_to_token_grids(
            model=model,
            images=attacked,
            latent_side=latent_side,
            batch_size=batch_size,
            device=device,
        )
        received_by_index = {index: grid for index, grid in zip(attacked_indices, received_grids)}
    value_lookup = codec.bin_for_token
    macro_cells = macro_cell_positions(latent_side, macro_cell_size)
    image_symbols = generated["image_symbols"]
    image_symbol_values = generated["image_symbol_values"]
    values_per_symbol = int(generated["values_per_symbol"])
    recovered_symbols: list[FountainSymbol] = []
    value_matches = 0
    value_total = 0
    exact_symbols = 0
    token_matches = 0
    token_total = 0

    for image_index, (symbol_group, value_group, sent_grid) in enumerate(
        zip(image_symbols, image_symbol_values, generated["token_grids"])
    ):
        if image_index not in received_by_index:
            continue
        received_grid = received_by_index[image_index]
        token_matches += int((np.asarray(sent_grid).reshape(-1) == received_grid.reshape(-1)).sum())
        token_total += int(received_grid.size)
        for local_symbol_index, (symbol, expected_values) in enumerate(zip(symbol_group, value_group)):
            recovered_values = []
            cell_offset = local_symbol_index * values_per_symbol
            for value_index, expected_value in enumerate(expected_values):
                row_start, col_start = macro_cells[cell_offset + value_index]
                cell = received_grid[row_start : row_start + macro_cell_size, col_start : col_start + macro_cell_size]
                values = value_lookup[cell.reshape(-1)]
                counts = np.bincount(values, minlength=codec.bin_count)
                value = int(counts.argmax())
                recovered_values.append(value)
                if value == expected_value:
                    value_matches += 1
                value_total += 1
            data = values_to_bytes(recovered_values, capacity_bits=bits_per_token, output_size=block_size)
            if data == symbol.data:
                exact_symbols += 1
            recovered_symbols.append(
                FountainSymbol(
                    symbol_id=symbol.symbol_id,
                    source_count=symbol.source_count,
                    block_size=symbol.block_size,
                    original_size=symbol.original_size,
                    block_ids=symbol.block_ids,
                    data=data,
                    data_crc=symbol.data_crc,
                )
            )

    crc_valid_symbols = sum(1 for symbol in recovered_symbols if symbol_crc_valid(symbol))
    exact_recovery = False
    failure = ""
    try:
        recovered_payload = unpack_payload(decode_symbols(recovered_symbols))
        exact_recovery = recovered_payload == generated["payload"]
    except (FountainDecodeError, PayloadDecodeError) as exc:
        failure = str(exc)

    return {
        "attack": attack,
        "recovered_symbols": len(recovered_symbols),
        "exact_symbols": exact_symbols,
        "crc_valid_symbols": crc_valid_symbols,
        "crc_rejected_symbols": len(recovered_symbols) - crc_valid_symbols,
        "dropped_images": dropped_images,
        "erased_symbols": int(sum(len(group) for index, group in enumerate(image_symbols) if index not in received_by_index)),
        "token_match_rate": round(token_matches / token_total, 6) if token_total else 0.0,
        "value_match_rate": round(value_matches / value_total, 6) if value_total else 0.0,
        "exact_recovery": exact_recovery,
        "failure": failure,
    }


def decode_encode_token_grids(model, token_grids: np.ndarray, batch_size: int, device: torch.device) -> np.ndarray:
    images = decode_token_grids_to_tensors(model, token_grids=token_grids, batch_size=batch_size, device=device)
    pil_images = [tensor_to_image(image) for image in images]
    return encode_images_to_token_grids(
        model=model,
        images=pil_images,
        latent_side=int(token_grids.shape[1]),
        batch_size=batch_size,
        device=device,
    )


def decode_token_grids_to_images(model, token_grids: np.ndarray, batch_size: int, device: torch.device) -> list[Image.Image]:
    tensors = decode_token_grids_to_tensors(model, token_grids=token_grids, batch_size=batch_size, device=device)
    return [tensor_to_image(tensor) for tensor in tensors]


def decode_token_grids_to_tensors(model, token_grids: np.ndarray, batch_size: int, device: torch.device) -> list[torch.Tensor]:
    out: list[torch.Tensor] = []
    latent_side = int(token_grids.shape[1])
    with torch.no_grad():
        for start in range(0, token_grids.shape[0], batch_size):
            batch = token_grids[start : start + batch_size]
            indices = torch.from_numpy(batch.reshape(-1).astype(np.int64)).to(device)
            z = model.quantize.get_codebook_entry(
                indices,
                shape=(batch.shape[0], latent_side, latent_side, vq_embed_dim(model)),
            )
            decoded = model.decode(z).sample.detach().cpu()
            out.extend(decoded[index] for index in range(decoded.shape[0]))
    return out


def encode_images_to_token_grids(
    model,
    images: list[Image.Image],
    latent_side: int,
    batch_size: int,
    device: torch.device,
) -> list[np.ndarray]:
    grids: list[np.ndarray] = []
    with torch.no_grad():
        for start in range(0, len(images), batch_size):
            batch_images = images[start : start + batch_size]
            tensor = torch.stack([image_to_tensor(image) for image in batch_images], dim=0).to(device)
            encoded = model.encode(tensor).latents
            quant = model.quant_conv(encoded)
            indices = model.quantize(quant)[2][2].detach().cpu().numpy()
            grids.extend(indices.reshape(len(batch_images), latent_side, latent_side))
    return grids


def macro_cell_positions(latent_side: int, macro_cell_size: int) -> list[tuple[int, int]]:
    return [
        (row, col)
        for row in range(0, latent_side, macro_cell_size)
        for col in range(0, latent_side, macro_cell_size)
    ]


def select_calibrated_token(pool: list[CalibratedToken], key: str) -> int:
    index = stable_random(key) % len(pool)
    ordered = sorted(pool, key=lambda item: (-item.majority_fraction, item.token_id))
    return ordered[index].token_id


def deterministic_payload(size: int, seed: int | str) -> bytes:
    rng = random.Random(f"{seed}:{size}")
    return bytes(rng.randrange(0, 256) for _ in range(size))


def image_to_tensor(image: Image.Image) -> torch.Tensor:
    array = np.asarray(image.convert("RGB")).astype(np.float32) / 127.5 - 1.0
    return torch.from_numpy(array).permute(2, 0, 1)


def tensor_to_image(tensor: torch.Tensor) -> Image.Image:
    array = tensor.detach().cpu().clamp(-1.0, 1.0).permute(1, 2, 0).numpy()
    array = (array + 1.0) * 127.5
    return Image.fromarray(np.clip(array, 0, 255).astype(np.uint8), mode="RGB")


def stable_random(value: str) -> int:
    return int.from_bytes(hashlib.sha256(value.encode("utf-8")).digest()[:8], "big")


def seed_to_int(value: str) -> int:
    return int.from_bytes(hashlib.sha256(value.encode("utf-8")).digest()[:16], "big")


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


def model_reference(model_dir: str) -> str:
    path = Path(model_dir)
    if path.exists() or "\\" in model_dir or "/" in model_dir and model_dir.startswith("."):
        return display_path(path)
    return model_dir


def sample_path_for_seed(base_path: Path, seed_index: int, seed: str, total_seeds: int) -> Path:
    if total_seeds <= 1:
        return base_path
    slug = "".join(char if char.isalnum() or char in {"-", "_"} else "_" for char in str(seed))
    return base_path.with_name(f"{base_path.stem}_{seed_index:02d}_{slug}{base_path.suffix}")


def vq_embed_dim(model) -> int:
    value = getattr(model.config, "vq_embed_dim", None)
    if value is not None:
        return int(value)
    return int(model.quantize.embedding.weight.shape[1])


if __name__ == "__main__":
    raise SystemExit(main())
