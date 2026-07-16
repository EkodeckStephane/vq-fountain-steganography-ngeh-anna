"""Deterministic image transformations for token-channel stability tests."""

from __future__ import annotations

from io import BytesIO
import hashlib
import random
import re

import numpy as np
from PIL import Image, ImageFilter


def apply_attack(image: Image.Image, attack: str, seed: int | str = 0) -> Image.Image:
    """Apply a named attack and return an RGB image with the original size."""

    image = image.convert("RGB")
    width, height = image.size
    name = attack.lower()

    if "+" in name:
        attacked = image.copy()
        for part in split_attack_chain(name):
            if part.startswith("drop"):
                continue
            attacked = apply_attack(attacked, part, seed=seed)
        return attacked.convert("RGB")
    if name == "clean":
        return image.copy()
    if name.startswith("drop"):
        return image.copy()
    if name.startswith("jpeg"):
        quality = int(name.replace("jpeg", ""))
        return jpeg_roundtrip(image, quality)
    if name.startswith("resize"):
        ratio_text = name.replace("resize", "")
        ratio = float(ratio_text) / 100.0 if ratio_text.isdigit() else float(ratio_text)
        return resize_roundtrip(image, ratio)
    if name.startswith("blur"):
        radius = float(name.replace("blur", ""))
        return image.filter(ImageFilter.GaussianBlur(radius=radius))
    if name.startswith("noise"):
        sigma_text = name.replace("noise", "")
        sigma = float(sigma_text) / 100.0 if sigma_text.isdigit() else float(sigma_text)
        return add_gaussian_noise(image, sigma=sigma, seed=f"{seed}:{attack}")
    if name.startswith("crop"):
        ratio, row_offset, col_offset = parse_crop_attack(name)
        return crop_resize(image, ratio=ratio, row_offset=row_offset, col_offset=col_offset)

    raise ValueError(f"unknown attack: {attack}")


def split_attack_chain(attack: str) -> list[str]:
    parts = [part.strip().lower() for part in attack.split("+") if part.strip()]
    if not parts:
        raise ValueError("attack chain is empty")
    return parts


def drop_probability(attack: str) -> float:
    probability = 0.0
    for part in split_attack_chain(attack):
        if part.startswith("drop"):
            text = part.replace("drop", "")
            probability = max(probability, parse_ratio(text))
    return probability


def should_drop_image(attack: str, image_index: int, seed: int | str) -> bool:
    probability = drop_probability(attack)
    if probability <= 0:
        return False
    rng = random.Random(_seed_to_uint64(f"{seed}:{attack}:drop:{image_index}"))
    return rng.random() < probability


def jpeg_roundtrip(image: Image.Image, quality: int) -> Image.Image:
    if quality < 1 or quality > 100:
        raise ValueError("jpeg quality must be in [1, 100]")
    buffer = BytesIO()
    image.save(buffer, format="JPEG", quality=quality)
    buffer.seek(0)
    return Image.open(buffer).convert("RGB")


def resize_roundtrip(image: Image.Image, ratio: float) -> Image.Image:
    if ratio <= 0 or ratio > 1:
        raise ValueError("resize ratio must be in (0, 1]")
    width, height = image.size
    small_size = (max(1, round(width * ratio)), max(1, round(height * ratio)))
    small = image.resize(small_size, Image.Resampling.BICUBIC)
    return small.resize((width, height), Image.Resampling.BICUBIC).convert("RGB")


def add_gaussian_noise(image: Image.Image, sigma: float, seed: int | str = 0) -> Image.Image:
    if sigma < 0:
        raise ValueError("sigma must be non-negative")
    array = np.asarray(image).astype(np.float32) / 255.0
    rng = np.random.default_rng(_seed_to_uint64(seed))
    noisy = np.clip(array + rng.normal(0.0, sigma, size=array.shape), 0.0, 1.0)
    return Image.fromarray((noisy * 255.0).round().astype(np.uint8), mode="RGB")


def center_crop_resize(image: Image.Image, ratio: float) -> Image.Image:
    return crop_resize(image, ratio=ratio, row_offset=0.0, col_offset=0.0)


def crop_resize(image: Image.Image, ratio: float, row_offset: float = 0.0, col_offset: float = 0.0) -> Image.Image:
    if ratio <= 0 or ratio > 1:
        raise ValueError("crop ratio must be in (0, 1]")
    width, height = image.size
    crop_width = max(1, round(width * ratio))
    crop_height = max(1, round(height * ratio))
    max_left = width - crop_width
    max_top = height - crop_height
    center_left = max_left / 2.0
    center_top = max_top / 2.0
    left = round(center_left + col_offset * width)
    top = round(center_top + row_offset * height)
    if left < 0 or left > max_left or top < 0 or top > max_top:
        raise ValueError("crop offset places crop outside image")
    cropped = image.crop((left, top, left + crop_width, top + crop_height))
    return cropped.resize((width, height), Image.Resampling.BICUBIC).convert("RGB")


def parse_crop_attack(name: str) -> tuple[float, float, float]:
    match = re.fullmatch(r"crop([^_]+)(?:_r([+-]?(?:\d+(?:\.\d+)?|\.\d+)))?(?:_c([+-]?(?:\d+(?:\.\d+)?|\.\d+)))?", name)
    if not match:
        raise ValueError(f"invalid crop attack: {name}")
    ratio = parse_ratio(match.group(1))
    row_offset = parse_offset(match.group(2) or "0")
    col_offset = parse_offset(match.group(3) or "0")
    return ratio, row_offset, col_offset


def parse_ratio(text: str) -> float:
    return float(text) / 100.0 if text.isdigit() else float(text)


def parse_offset(text: str) -> float:
    if "." in text:
        return float(text)
    return float(text) / 100.0


def _seed_to_uint64(seed: int | str) -> int:
    if isinstance(seed, int):
        return seed & ((1 << 64) - 1)
    digest = hashlib.sha256(str(seed).encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big")
