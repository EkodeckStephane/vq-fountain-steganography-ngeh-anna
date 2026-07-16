"""Tokenizer adapters for Stage 1 token-channel experiments."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image


@dataclass(frozen=True)
class TokenGrid:
    tokens: np.ndarray
    image_size: int
    patch_size: int
    levels: int

    @property
    def shape(self) -> tuple[int, int]:
        return tuple(self.tokens.shape)  # type: ignore[return-value]

    @property
    def flat(self) -> np.ndarray:
        return self.tokens.reshape(-1)


class PatchVQTokenizer:
    """Fixed patch vector quantizer used as a dependency-light Stage 1 baseline.

    This is not a learned VQGAN tokenizer. It quantizes mean RGB patch colors
    into a fixed codebook so the stability pipeline can run locally before a
    learned tokenizer is introduced.
    """

    name = "patch-vq"

    def __init__(self, image_size: int = 256, patch_size: int = 16, levels: int = 8) -> None:
        if image_size <= 0:
            raise ValueError("image_size must be positive")
        if patch_size <= 0:
            raise ValueError("patch_size must be positive")
        if image_size % patch_size != 0:
            raise ValueError("image_size must be divisible by patch_size")
        if levels < 2 or levels > 256:
            raise ValueError("levels must be in [2, 256]")
        self.image_size = image_size
        self.patch_size = patch_size
        self.levels = levels
        self.tokens_per_side = image_size // patch_size

    @property
    def codebook_size(self) -> int:
        return self.levels ** 3

    def encode_path(self, path: str | Path) -> TokenGrid:
        with Image.open(path) as image:
            return self.encode_image(image)

    def encode_image(self, image: Image.Image) -> TokenGrid:
        resized = image.convert("RGB").resize(
            (self.image_size, self.image_size),
            Image.Resampling.BICUBIC,
        )
        array = np.asarray(resized).astype(np.float32) / 255.0
        side = self.tokens_per_side
        patch = self.patch_size
        patches = array.reshape(side, patch, side, patch, 3).mean(axis=(1, 3))
        quantized = np.clip(np.floor(patches * self.levels), 0, self.levels - 1).astype(np.int32)
        tokens = (
            quantized[:, :, 0] * self.levels * self.levels
            + quantized[:, :, 1] * self.levels
            + quantized[:, :, 2]
        )
        return TokenGrid(
            tokens=tokens.astype(np.int32),
            image_size=self.image_size,
            patch_size=self.patch_size,
            levels=self.levels,
        )

    def decode_grid(self, grid: TokenGrid) -> Image.Image:
        rgb = self.tokens_to_rgb(grid.tokens)
        patch = grid.patch_size
        image_array = np.repeat(np.repeat(rgb, patch, axis=0), patch, axis=1)
        return Image.fromarray(np.clip(image_array * 255.0, 0, 255).astype(np.uint8), mode="RGB")

    def tokens_to_rgb(self, tokens: np.ndarray) -> np.ndarray:
        tokens = tokens.astype(np.int32)
        red = tokens // (self.levels * self.levels)
        green = (tokens // self.levels) % self.levels
        blue = tokens % self.levels
        rgb = np.stack([red, green, blue], axis=-1).astype(np.float32)
        return (rgb + 0.5) / self.levels


class LearnedPatchVQTokenizer:
    """Patch vector quantizer backed by a learned NumPy codebook."""

    name = "learned-patch-vq"

    def __init__(self, codebook_path: str | Path) -> None:
        data = np.load(codebook_path, allow_pickle=False)
        self.codebook = data["codebook"].astype(np.float32)
        self.image_size = int(data["image_size"])
        self.patch_size = int(data["patch_size"])
        if "token_prior" in data:
            prior = data["token_prior"].astype(np.float64)
            prior_sum = float(prior.sum())
            if prior_sum <= 0:
                raise ValueError("token_prior has no mass")
            self.token_prior = (prior / prior_sum).astype(np.float64)
        else:
            self.token_prior = np.full(self.codebook.shape[0], 1.0 / self.codebook.shape[0], dtype=np.float64)
        self.tokens_per_side = self.image_size // self.patch_size
        expected_dim = self.patch_size * self.patch_size * 3
        if self.codebook.ndim != 2 or self.codebook.shape[1] != expected_dim:
            raise ValueError("codebook shape does not match patch dimensions")
        if self.token_prior.shape != (self.codebook.shape[0],):
            raise ValueError("token_prior length does not match codebook size")

    @property
    def codebook_size(self) -> int:
        return int(self.codebook.shape[0])

    def encode_path(self, path: str | Path) -> TokenGrid:
        with Image.open(path) as image:
            return self.encode_image(image)

    def encode_image(self, image: Image.Image) -> TokenGrid:
        patches = image_to_patch_matrix(image, image_size=self.image_size, patch_size=self.patch_size)
        tokens = nearest_codebook_indices(patches, self.codebook, chunk_size=2048)
        return TokenGrid(
            tokens=tokens.reshape(self.tokens_per_side, self.tokens_per_side).astype(np.int32),
            image_size=self.image_size,
            patch_size=self.patch_size,
            levels=self.codebook_size,
        )

    def decode_grid(self, grid: TokenGrid) -> Image.Image:
        flat_tokens = grid.tokens.reshape(-1).astype(np.int32)
        patches = self.codebook[flat_tokens]
        return patch_matrix_to_image(patches, image_size=self.image_size, patch_size=self.patch_size)


def build_tokenizer(
    name: str,
    image_size: int = 256,
    patch_size: int = 16,
    levels: int = 8,
    codebook_path: str | Path | None = None,
) -> PatchVQTokenizer | LearnedPatchVQTokenizer:
    if name != "patch-vq":
        if name == "learned-patch-vq":
            if codebook_path is None:
                raise ValueError("learned-patch-vq requires codebook_path")
            return LearnedPatchVQTokenizer(codebook_path)
        raise ValueError(f"unsupported tokenizer {name!r}")
    return PatchVQTokenizer(image_size=image_size, patch_size=patch_size, levels=levels)


def token_match_rate(reference: TokenGrid, candidate: TokenGrid) -> float:
    if reference.tokens.shape != candidate.tokens.shape:
        raise ValueError("token grids must have the same shape")
    return float((reference.tokens == candidate.tokens).mean())


def stable_position_mask(grids: list[TokenGrid]) -> np.ndarray:
    if not grids:
        raise ValueError("at least one grid is required")
    first = grids[0].tokens
    for grid in grids[1:]:
        if grid.tokens.shape != first.shape:
            raise ValueError("all token grids must have the same shape")
    mask = np.ones(first.shape, dtype=bool)
    for grid in grids[1:]:
        mask &= grid.tokens == first
    return mask


def image_to_patch_matrix(image: Image.Image, image_size: int, patch_size: int) -> np.ndarray:
    if image_size % patch_size != 0:
        raise ValueError("image_size must be divisible by patch_size")
    resized = image.convert("RGB").resize((image_size, image_size), Image.Resampling.BICUBIC)
    array = np.asarray(resized).astype(np.float32) / 255.0
    side = image_size // patch_size
    patches = array.reshape(side, patch_size, side, patch_size, 3).transpose(0, 2, 1, 3, 4)
    return patches.reshape(side * side, patch_size * patch_size * 3).astype(np.float32)


def patch_matrix_to_image(patches: np.ndarray, image_size: int, patch_size: int) -> Image.Image:
    side = image_size // patch_size
    if patches.shape != (side * side, patch_size * patch_size * 3):
        raise ValueError("patch matrix shape does not match image dimensions")
    patch_grid = patches.reshape(side, side, patch_size, patch_size, 3).transpose(0, 2, 1, 3, 4)
    array = patch_grid.reshape(image_size, image_size, 3)
    return Image.fromarray(np.clip(array * 255.0, 0, 255).astype(np.uint8), mode="RGB")


def nearest_codebook_indices(patches: np.ndarray, codebook: np.ndarray, chunk_size: int = 2048) -> np.ndarray:
    if patches.ndim != 2 or codebook.ndim != 2:
        raise ValueError("patches and codebook must be matrices")
    if patches.shape[1] != codebook.shape[1]:
        raise ValueError("patch and codebook dimensions differ")

    codebook_norm = np.sum(codebook * codebook, axis=1)
    indices = np.empty(patches.shape[0], dtype=np.int32)
    for start in range(0, patches.shape[0], chunk_size):
        chunk = patches[start : start + chunk_size]
        distances = np.sum(chunk * chunk, axis=1, keepdims=True) + codebook_norm[None, :]
        distances -= 2.0 * chunk @ codebook.T
        indices[start : start + len(chunk)] = np.argmin(distances, axis=1)
    return indices
