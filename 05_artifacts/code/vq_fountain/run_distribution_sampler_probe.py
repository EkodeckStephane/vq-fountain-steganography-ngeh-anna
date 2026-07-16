from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
sys.path.insert(0, str(ROOT))

from vq_fountain.bitstream import PayloadDecodeError, pack_payload, unpack_payload
from vq_fountain.fountain import (
    FountainDecodeError,
    FountainSymbol,
    decode_symbols,
    encode_repetition_symbols,
    encode_symbols,
    symbol_crc_valid,
)
from vq_fountain.image_attacks import apply_attack, should_drop_image
from vq_fountain.scheduler import keyed_order
from vq_fountain.token_sampler import PriorBinCodec, bytes_to_values, sample_prior_token, values_to_bytes
from vq_fountain.tokenizer_adapter import TokenGrid, build_tokenizer


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe distribution-aware token sampling through image round trips.")
    parser.add_argument("--tokenizer", default="learned-patch-vq")
    parser.add_argument("--codebook", default=str(REPO_ROOT / "05_artifacts" / "models" / "learned_patch_vq_stage1_k128.npz"))
    parser.add_argument("--payload-bytes", type=int, nargs="+", default=[8, 16, 32])
    parser.add_argument("--bits-per-token", type=int, nargs="+", default=[1, 2])
    parser.add_argument("--overheads", type=float, nargs="+", default=[0.5, 0.8, 1.2])
    parser.add_argument("--block-size", type=int, default=4)
    parser.add_argument("--coding", choices=["fountain", "repetition"], default="fountain")
    parser.add_argument("--image-copies", type=int, nargs="+", default=[2, 4, 8, 12])
    parser.add_argument("--attacks", nargs="+", default=["clean", "jpeg85", "resize075", "blur1", "noise002"])
    parser.add_argument("--binning", choices=["projection", "mass", "naive"], default="projection")
    parser.add_argument("--position-mode", choices=["raster", "center", "random"], default="raster")
    parser.add_argument("--margin", type=int, default=2)
    parser.add_argument("--geometry-search", choices=["none", "crop", "anchors", "anchors2d"], default="none")
    parser.add_argument("--crop-ratios", type=float, nargs="+", default=[1.0, 0.95, 0.92, 0.90, 0.88, 0.85])
    parser.add_argument("--crop-offsets", type=float, nargs="+", default=[0.0])
    parser.add_argument("--anchor-count", type=int, default=0)
    parser.add_argument("--anchor-scope", choices=["global", "block"], default="global")
    parser.add_argument("--token-block-size", type=int, default=4)
    parser.add_argument("--block-anchor-threshold", type=float, default=0.5)
    parser.add_argument("--seed", default="distribution-sampler")
    parser.add_argument(
        "--out-csv",
        default=str(REPO_ROOT / "05_artifacts" / "results" / "tables" / "vq_fountain_distribution_sampler_probe.csv"),
    )
    parser.add_argument(
        "--out-json",
        default=str(REPO_ROOT / "05_artifacts" / "results" / "raw" / "vq_fountain_distribution_sampler_probe.json"),
    )
    args = parser.parse_args()

    tokenizer = build_tokenizer(args.tokenizer, codebook_path=args.codebook)
    if not hasattr(tokenizer, "token_prior") or not hasattr(tokenizer, "codebook"):
        raise SystemExit("distribution sampler probe requires a tokenizer with token_prior and codebook")

    rows: list[dict[str, object]] = []
    raw: list[dict[str, object]] = []
    for payload_bytes in args.payload_bytes:
        for bits_per_token in args.bits_per_token:
            codec = PriorBinCodec(
                prior=tokenizer.token_prior,
                capacity_bits=bits_per_token,
                codebook=tokenizer.codebook,
                mode=args.binning,
            )
            for overhead in args.overheads:
                for image_copies in args.image_copies:
                    generated = generate_payload_images(
                        tokenizer=tokenizer,
                        codec=codec,
                        payload_bytes=payload_bytes,
                        bits_per_token=bits_per_token,
                        overhead=overhead,
                        block_size=args.block_size,
                        coding=args.coding,
                        image_copies=image_copies,
                        position_mode=args.position_mode,
                        margin=args.margin,
                        anchor_count=args.anchor_count,
                        anchor_scope=args.anchor_scope,
                        token_block_size=args.token_block_size,
                        seed=args.seed,
                    )
                    for attack in args.attacks:
                        result = recover_from_images(
                            tokenizer=tokenizer,
                            codec=codec,
                            generated=generated,
                            attack=attack,
                            bits_per_token=bits_per_token,
                            block_size=args.block_size,
                            geometry_search=args.geometry_search,
                            crop_ratios=args.crop_ratios,
                            crop_offsets=args.crop_offsets,
                            block_anchor_threshold=args.block_anchor_threshold,
                            seed=args.seed,
                        )
                        row = {
                            "payload_bytes": payload_bytes,
                            "packet_bytes": generated["packet_bytes"],
                            "block_size": args.block_size,
                            "coding": args.coding,
                            "bits_per_token": bits_per_token,
                            "overhead": overhead,
                            "image_copies": image_copies,
                            "attack": attack,
                            "binning": args.binning,
                            "position_mode": args.position_mode,
                            "margin": args.margin,
                            "geometry_search": args.geometry_search,
                            "crop_offsets": " ".join(str(value) for value in args.crop_offsets),
                            "anchor_count": args.anchor_count,
                            "anchor_scope": args.anchor_scope,
                            "token_block_size": args.token_block_size,
                            "block_anchor_threshold": args.block_anchor_threshold,
                            "source_symbols": generated["source_symbols"],
                            "encoded_symbols": generated["encoded_symbols"],
                            "used_token_slots": generated["used_token_slots"],
                            "payload_token_slots": generated["payload_token_slots"],
                            "anchor_token_slots": generated["anchor_token_slots"],
                            "mean_payload_leakage": generated["mean_payload_leakage"],
                            "mean_anchor_leakage": generated["mean_anchor_leakage"],
                            "payload_token_jsd_to_prior": generated["payload_token_jsd_to_prior"],
                            "anchor_token_jsd_to_prior": generated["anchor_token_jsd_to_prior"],
                            "raw_capacity_bits": generated["used_token_slots"] * bits_per_token,
                            **result,
                        }
                        rows.append(row)
                        raw.append(row)

    write_csv(Path(args.out_csv), rows)
    write_json(Path(args.out_json), raw)
    print(json.dumps({"csv": args.out_csv, "json": args.out_json, "rows": len(rows)}, indent=2))
    return 0


def generate_payload_images(
    tokenizer,
    codec: PriorBinCodec,
    payload_bytes: int,
    bits_per_token: int,
    overhead: float,
    block_size: int,
    coding: str,
    image_copies: int,
    position_mode: str,
    margin: int,
    anchor_count: int,
    anchor_scope: str,
    token_block_size: int,
    seed: int | str,
) -> dict[str, object]:
    payload = deterministic_payload(payload_bytes, seed=seed)
    packet = pack_payload(payload)
    if coding == "fountain":
        symbols = encode_symbols(packet, block_size=block_size, overhead=overhead, seed=seed)
    elif coding == "repetition":
        symbols = encode_repetition_symbols(packet, block_size=block_size, overhead=overhead)
    else:
        raise ValueError(f"unsupported coding mode: {coding}")
    token_count = tokenizer.tokens_per_side * tokenizer.tokens_per_side
    position_schedules = [
        scheduled_positions(tokenizer.tokens_per_side, mode=position_mode, margin=margin, seed=f"{seed}:{index}")
        for index in range(image_copies)
    ]
    if anchor_count < 0:
        raise ValueError("anchor_count must be non-negative")
    if anchor_scope not in {"global", "block"}:
        raise ValueError(f"unsupported anchor scope: {anchor_scope}")
    if anchor_scope == "block" and token_block_size <= 0:
        raise ValueError("token_block_size must be positive for block anchors")

    anchor_schedules: list[list[int]] = []
    payload_schedules: list[list[int]] = []
    anchor_block_schedules: list[list[int]] = []
    payload_block_schedules: list[list[int]] = []
    block_counts: list[int] = []
    if anchor_scope == "global":
        for positions in position_schedules:
            anchors = positions[: min(anchor_count, len(positions))]
            payload_positions = positions[len(anchors) :]
            anchor_schedules.append(anchors)
            payload_schedules.append(payload_positions)
            anchor_block_schedules.append([0 for _ in anchors])
            payload_block_schedules.append([0 for _ in payload_positions])
            block_counts.append(1)
    else:
        for image_index in range(image_copies):
            block_groups = token_block_groups(
                tokenizer.tokens_per_side,
                mode=position_mode,
                margin=margin,
                token_block_size=token_block_size,
                seed=f"{seed}:{image_index}",
            )
            image_anchors: list[int] = []
            image_payload: list[int] = []
            image_anchor_blocks: list[int] = []
            image_payload_blocks: list[int] = []
            for block_index, group in enumerate(block_groups):
                anchor_take = min(anchor_count, len(group))
                image_anchors.extend(group[:anchor_take])
                image_anchor_blocks.extend([block_index for _ in range(anchor_take)])
                payload_positions = group[anchor_take:]
                image_payload.extend(payload_positions)
                image_payload_blocks.extend([block_index for _ in payload_positions])
            anchor_schedules.append(image_anchors)
            payload_schedules.append(image_payload)
            anchor_block_schedules.append(image_anchor_blocks)
            payload_block_schedules.append(image_payload_blocks)
            block_counts.append(len(block_groups))

    anchor_value_schedules = [
        anchor_values(len(anchor_schedules[index]), bits_per_token=bits_per_token, seed=f"{seed}:{index}")
        for index in range(image_copies)
    ]
    total_slots = sum(len(positions) for positions in payload_schedules)

    symbol_values: list[list[int]] = [bytes_to_values(symbol.data, bits_per_token) for symbol in symbols]
    flat_values = [value for values in symbol_values for value in values]
    if len(flat_values) > total_slots:
        flat_values = flat_values[:total_slots]

    grids: list[TokenGrid] = []
    decisions: list[int] = []
    anchor_decisions: list[int] = []
    payload_decisions: list[int] = []
    anchor_leakages: list[float] = []
    payload_leakages: list[float] = []
    cursor = 0
    for image_index in range(image_copies):
        flat_tokens = np.empty(token_count, dtype=np.int32)
        for position in range(token_count):
            global_position = image_index * token_count + position
            flat_tokens[position] = sample_prior_token(tokenizer.token_prior, key=seed, position=global_position)
        for anchor_position, anchor_value in zip(anchor_schedules[image_index], anchor_value_schedules[image_index]):
            global_position = image_index * token_count + anchor_position
            sample = codec.sample_token(anchor_value, key=f"{seed}:anchor", position=global_position)
            flat_tokens[anchor_position] = sample.token_id
            decisions.append(sample.token_id)
            anchor_decisions.append(sample.token_id)
            anchor_leakages.append(sample.leakage_score)
        for position in payload_schedules[image_index]:
            global_position = image_index * token_count + position
            if cursor >= len(flat_values):
                break
            sample = codec.sample_token(flat_values[cursor], key=seed, position=global_position)
            flat_tokens[position] = sample.token_id
            decisions.append(sample.token_id)
            payload_decisions.append(sample.token_id)
            payload_leakages.append(sample.leakage_score)
            cursor += 1
        grids.append(
            TokenGrid(
                tokens=flat_tokens.reshape(tokenizer.tokens_per_side, tokenizer.tokens_per_side),
                image_size=tokenizer.image_size,
                patch_size=tokenizer.patch_size,
                levels=tokenizer.codebook_size,
            )
        )

    images = [tokenizer.decode_grid(grid) for grid in grids]
    return {
        "payload": payload,
        "packet_bytes": len(packet),
        "symbols": symbols,
        "symbol_value_counts": [len(values) for values in symbol_values],
        "images": images,
        "grids": grids,
        "position_schedules": payload_schedules,
        "anchor_schedules": anchor_schedules,
        "anchor_value_schedules": anchor_value_schedules,
        "anchor_block_schedules": anchor_block_schedules,
        "payload_block_schedules": payload_block_schedules,
        "block_counts": block_counts,
        "anchor_scope": anchor_scope,
        "used_token_slots": len(flat_values),
        "payload_token_slots": len(payload_decisions),
        "anchor_token_slots": len(anchor_decisions),
        "mean_payload_leakage": round(float(np.mean(payload_leakages)), 8) if payload_leakages else 0.0,
        "mean_anchor_leakage": round(float(np.mean(anchor_leakages)), 8) if anchor_leakages else 0.0,
        "payload_token_jsd_to_prior": round(token_jsd_to_prior(payload_decisions, tokenizer.token_prior), 8),
        "anchor_token_jsd_to_prior": round(token_jsd_to_prior(anchor_decisions, tokenizer.token_prior), 8),
        "source_symbols": symbols[0].source_count if symbols else 0,
        "encoded_symbols": len(symbols),
        "capacity_exhausted": len(flat_values) < sum(len(values) for values in symbol_values),
    }


def recover_from_images(
    tokenizer,
    codec: PriorBinCodec,
    generated: dict[str, object],
    attack: str,
    bits_per_token: int,
    block_size: int,
    geometry_search: str,
    crop_ratios: list[float],
    crop_offsets: list[float],
    block_anchor_threshold: float,
    seed: int | str,
) -> dict[str, object]:
    candidates = geometry_candidates(geometry_search, crop_ratios=crop_ratios, crop_offsets=crop_offsets)
    results = [
        recover_from_images_with_ratio(
            tokenizer=tokenizer,
            codec=codec,
            generated=generated,
            attack=attack,
            bits_per_token=bits_per_token,
            block_size=block_size,
            crop_ratio=ratio,
            row_offset=row_offset,
            col_offset=col_offset,
            block_anchor_threshold=block_anchor_threshold,
            seed=seed,
        )
        for ratio, row_offset, col_offset in candidates
    ]
    if geometry_search in {"anchors", "anchors2d"}:
        return max(
            results,
            key=lambda item: (
                float(item["anchor_match_rate"]),
                int(item["anchor_matches"]),
                float(item["value_match_rate"]),
            ),
        )
    exact = [result for result in results if result["exact_recovery"]]
    if exact:
        return exact[0]
    return max(
        results,
        key=lambda item: (
            int(item["crc_valid_symbols"]),
            float(item["value_match_rate"]),
            float(item["token_match_rate"]),
        ),
    )


def recover_from_images_with_ratio(
    tokenizer,
    codec: PriorBinCodec,
    generated: dict[str, object],
    attack: str,
    bits_per_token: int,
    block_size: int,
    crop_ratio: float,
    row_offset: float,
    col_offset: float,
    block_anchor_threshold: float,
    seed: int | str,
) -> dict[str, object]:
    images = generated["images"]
    grids = generated["grids"]
    symbols = generated["symbols"]
    symbol_value_counts = generated["symbol_value_counts"]
    position_schedules = generated["position_schedules"]
    anchor_schedules = generated["anchor_schedules"]
    anchor_value_schedules = generated["anchor_value_schedules"]
    anchor_block_schedules = generated.get("anchor_block_schedules")
    payload_block_schedules = generated.get("payload_block_schedules")
    block_counts = generated.get("block_counts")
    anchor_scope = str(generated.get("anchor_scope", "global"))
    if not isinstance(images, list) or not isinstance(grids, list) or not isinstance(symbols, list):
        raise ValueError("invalid generated payload")
    if not isinstance(position_schedules, list):
        raise ValueError("invalid position schedules")
    if not isinstance(anchor_schedules, list) or not isinstance(anchor_value_schedules, list):
        raise ValueError("invalid anchor schedules")
    if anchor_scope not in {"global", "block"}:
        raise ValueError(f"unsupported anchor scope: {anchor_scope}")
    if not isinstance(anchor_block_schedules, list) or not isinstance(payload_block_schedules, list):
        raise ValueError("invalid block schedules")
    if not isinstance(block_counts, list):
        raise ValueError("invalid block counts")
    if block_anchor_threshold < 0.0 or block_anchor_threshold > 1.0:
        raise ValueError("block_anchor_threshold must be in [0, 1]")

    extracted_values: list[int] = []
    anchor_matches = 0
    anchor_total = 0
    token_matches = 0
    token_total = 0
    value_matches = 0
    value_total = int(generated["used_token_slots"])
    accepted_blocks = 0
    total_blocks = 0
    erased_token_slots = 0
    dropped_images = 0

    expected_values: list[int] = []
    for symbol in symbols:
        expected_values.extend(bytes_to_values(symbol.data, bits_per_token))
    expected_values = expected_values[:value_total]

    cursor = 0
    for image_index, image in enumerate(images):
        reference_tokens = grids[image_index].flat
        image_block_count = int(block_counts[image_index]) if anchor_scope == "block" else 1
        if should_drop_image(attack, image_index=image_index, seed=seed):
            dropped_images += 1
            token_total += int(reference_tokens.size)
            anchor_total += len(anchor_schedules[image_index])
            if anchor_scope == "block":
                total_blocks += image_block_count
            for payload_index, _position in enumerate(position_schedules[image_index]):
                if cursor >= value_total:
                    break
                extracted_values.append(0)
                erased_token_slots += 1
                if expected_values[cursor] == 0:
                    value_matches += 1
                cursor += 1
            continue

        attacked = apply_attack(image, attack, seed=f"{seed}:{attack}:{image_index}")
        received_grid = tokenizer.encode_image(attacked)
        received_tokens = received_grid.flat
        token_matches += int((reference_tokens == received_tokens).sum())
        token_total += int(reference_tokens.size)
        block_anchor_hits = [0 for _ in range(image_block_count)]
        block_anchor_totals = [0 for _ in range(image_block_count)]
        for anchor_index, (anchor_position, expected_anchor) in enumerate(
            zip(anchor_schedules[image_index], anchor_value_schedules[image_index])
        ):
            block_id = int(anchor_block_schedules[image_index][anchor_index]) if anchor_scope == "block" else 0
            mapped_anchor = map_position_for_crop_transform(
                int(anchor_position),
                tokenizer.tokens_per_side,
                crop_ratio,
                row_offset=row_offset,
                col_offset=col_offset,
            )
            anchor_total += 1
            if anchor_scope == "block":
                block_anchor_totals[block_id] += 1
            if mapped_anchor is None:
                continue
            anchor_token = received_tokens[mapped_anchor]
            anchor_value = codec.decode_value(int(anchor_token))
            if anchor_value == expected_anchor:
                anchor_matches += 1
                if anchor_scope == "block":
                    block_anchor_hits[block_id] += 1

        block_accepted = [True for _ in range(image_block_count)]
        if anchor_scope == "block":
            total_blocks += image_block_count
            for block_id in range(image_block_count):
                total = block_anchor_totals[block_id]
                rate = block_anchor_hits[block_id] / total if total else 0.0
                block_accepted[block_id] = total > 0 and rate >= block_anchor_threshold
                if block_accepted[block_id]:
                    accepted_blocks += 1

        for payload_index, position in enumerate(position_schedules[image_index]):
            if cursor >= value_total:
                break
            block_id = int(payload_block_schedules[image_index][payload_index]) if anchor_scope == "block" else 0
            if anchor_scope == "block" and not block_accepted[block_id]:
                value = 0
                erased_token_slots += 1
            else:
                mapped_position = map_position_for_crop_transform(
                    int(position),
                    tokenizer.tokens_per_side,
                    crop_ratio,
                    row_offset=row_offset,
                    col_offset=col_offset,
                )
                if mapped_position is None:
                    value = 0
                else:
                    token = received_tokens[mapped_position]
                    value = codec.decode_value(int(token))
            extracted_values.append(value)
            if value == expected_values[cursor]:
                value_matches += 1
            cursor += 1

    recovered_symbols: list[FountainSymbol] = []
    cursor = 0
    exact_symbol_count = 0
    for symbol, value_count in zip(symbols, symbol_value_counts):
        if cursor + value_count > len(extracted_values):
            break
        values = extracted_values[cursor : cursor + value_count]
        cursor += value_count
        data = values_to_bytes(values, capacity_bits=bits_per_token, output_size=block_size)
        if data == symbol.data:
            exact_symbol_count += 1
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

    exact_recovery = False
    failure = ""
    crc_valid_symbol_count = sum(1 for symbol in recovered_symbols if symbol_crc_valid(symbol))
    try:
        recovered_payload = unpack_payload(decode_symbols(recovered_symbols))
        exact_recovery = recovered_payload == generated["payload"]
    except (FountainDecodeError, PayloadDecodeError) as exc:
        failure = str(exc)

    return {
        "recovered_symbols": len(recovered_symbols),
        "exact_symbols": exact_symbol_count,
        "crc_valid_symbols": crc_valid_symbol_count,
        "crc_rejected_symbols": len(recovered_symbols) - crc_valid_symbol_count,
        "anchor_matches": anchor_matches,
        "anchor_total": anchor_total,
        "anchor_match_rate": round(anchor_matches / anchor_total, 6) if anchor_total else 0.0,
        "accepted_blocks": accepted_blocks,
        "total_blocks": total_blocks,
        "block_acceptance_rate": round(accepted_blocks / total_blocks, 6) if total_blocks else 0.0,
        "erased_token_slots": erased_token_slots,
        "dropped_images": dropped_images,
        "token_match_rate": round(token_matches / token_total, 6) if token_total else 0.0,
        "value_match_rate": round(value_matches / value_total, 6) if value_total else 0.0,
        "exact_recovery": exact_recovery,
        "failure": failure,
        "capacity_exhausted": bool(generated["capacity_exhausted"]),
        "selected_crop_ratio": crop_ratio,
        "selected_row_offset": row_offset,
        "selected_col_offset": col_offset,
    }


def geometry_candidates(
    geometry_search: str,
    crop_ratios: list[float],
    crop_offsets: list[float],
) -> list[tuple[float, float, float]]:
    if geometry_search == "none":
        return [(1.0, 0.0, 0.0)]
    if geometry_search in {"crop", "anchors"}:
        return [(ratio, 0.0, 0.0) for ratio in crop_ratios]
    if geometry_search == "anchors2d":
        return [(ratio, row_offset, col_offset) for ratio in crop_ratios for row_offset in crop_offsets for col_offset in crop_offsets]
    raise ValueError(f"unsupported geometry search: {geometry_search}")


def scheduled_positions(tokens_per_side: int, mode: str, margin: int, seed: int | str) -> list[int]:
    if tokens_per_side <= 0:
        raise ValueError("tokens_per_side must be positive")
    if mode == "raster":
        return list(range(tokens_per_side * tokens_per_side))
    if mode == "random":
        return keyed_order(list(range(tokens_per_side * tokens_per_side)), key=seed, context="random-positions")
    if mode != "center":
        raise ValueError(f"unsupported position mode: {mode}")
    if margin < 0:
        raise ValueError("margin must be non-negative")
    if margin * 2 >= tokens_per_side:
        raise ValueError("margin leaves no center positions")

    positions: list[int] = []
    for row in range(margin, tokens_per_side - margin):
        for col in range(margin, tokens_per_side - margin):
            positions.append(row * tokens_per_side + col)
    return keyed_order(positions, key=seed, context="center-positions")


def token_block_groups(
    tokens_per_side: int,
    mode: str,
    margin: int,
    token_block_size: int,
    seed: int | str,
) -> list[list[int]]:
    if token_block_size <= 0:
        raise ValueError("token_block_size must be positive")
    if mode not in {"raster", "center", "random"}:
        raise ValueError(f"unsupported position mode: {mode}")
    if mode == "random":
        return [[position] for position in keyed_order(list(range(tokens_per_side * tokens_per_side)), key=seed, context="random-token-block-order")]
    if mode == "center" and margin * 2 >= tokens_per_side:
        raise ValueError("margin leaves no center positions")

    first = margin if mode == "center" else 0
    last = tokens_per_side - margin if mode == "center" else tokens_per_side
    blocks: list[list[int]] = []
    for row_start in range(first, last, token_block_size):
        for col_start in range(first, last, token_block_size):
            positions: list[int] = []
            for row in range(row_start, min(row_start + token_block_size, last)):
                for col in range(col_start, min(col_start + token_block_size, last)):
                    positions.append(row * tokens_per_side + col)
            if positions:
                block_seed = f"{seed}:{row_start}:{col_start}"
                blocks.append(keyed_order(positions, key=block_seed, context="token-block-positions"))
    order = keyed_order(list(range(len(blocks))), key=seed, context="token-block-order")
    return [blocks[index] for index in order]


def anchor_values(count: int, bits_per_token: int, seed: int | str) -> list[int]:
    if count < 0:
        raise ValueError("count must be non-negative")
    if bits_per_token <= 0:
        raise ValueError("bits_per_token must be positive")
    import random

    rng = random.Random(f"{seed}:anchors:{bits_per_token}:{count}")
    max_value = 1 << bits_per_token
    return [rng.randrange(max_value) for _ in range(count)]


def map_position_for_crop(position: int, tokens_per_side: int, crop_ratio: float) -> int | None:
    return map_position_for_crop_transform(
        position,
        tokens_per_side,
        crop_ratio,
        row_offset=0.0,
        col_offset=0.0,
    )


def map_position_for_crop_transform(
    position: int,
    tokens_per_side: int,
    crop_ratio: float,
    row_offset: float,
    col_offset: float,
) -> int | None:
    if crop_ratio <= 0 or crop_ratio > 1:
        raise ValueError("crop_ratio must be in (0, 1]")
    row, col = divmod(position, tokens_per_side)
    if crop_ratio == 1.0:
        return position

    center_offset = (1.0 - crop_ratio) / 2.0
    top_offset = center_offset + row_offset
    left_offset = center_offset + col_offset
    max_offset = 1.0 - crop_ratio
    if top_offset < 0.0 or top_offset > max_offset or left_offset < 0.0 or left_offset > max_offset:
        return None

    mapped_row = _map_axis_for_crop(row, tokens_per_side, top_offset, crop_ratio)
    mapped_col = _map_axis_for_crop(col, tokens_per_side, left_offset, crop_ratio)
    if mapped_row is None or mapped_col is None:
        return None
    return mapped_row * tokens_per_side + mapped_col


def _map_axis_for_crop(index: int, side: int, offset: float, crop_ratio: float) -> int | None:
    original_center = (index + 0.5) / side
    if original_center < offset or original_center > offset + crop_ratio:
        return None
    received_center = (original_center - offset) / crop_ratio
    mapped = round(received_center * side - 0.5)
    if mapped < 0 or mapped >= side:
        return None
    return int(mapped)


def deterministic_payload(size: int, seed: int | str) -> bytes:
    import random

    rng = random.Random(f"{seed}:{size}")
    return bytes(rng.randrange(0, 256) for _ in range(size))


def token_jsd_to_prior(token_ids: list[int], prior: np.ndarray) -> float:
    if not token_ids:
        return 0.0
    counts = np.bincount(np.asarray(token_ids, dtype=np.int32), minlength=len(prior)).astype(np.float64)
    observed = counts / counts.sum()
    expected = np.asarray(prior, dtype=np.float64)
    expected = expected / expected.sum()
    midpoint = 0.5 * (observed + expected)
    return 0.5 * kl_divergence(observed, midpoint) + 0.5 * kl_divergence(expected, midpoint)


def kl_divergence(left: np.ndarray, right: np.ndarray) -> float:
    mask = left > 0
    return float(np.sum(left[mask] * np.log2(left[mask] / np.maximum(right[mask], 1e-15))))


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(rows, handle, indent=2, sort_keys=True)


if __name__ == "__main__":
    raise SystemExit(main())
