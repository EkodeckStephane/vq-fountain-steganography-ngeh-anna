from pathlib import Path
import sys
import unittest

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from vq_fountain.tokenizer_adapter import (
    LearnedPatchVQTokenizer,
    PatchVQTokenizer,
    image_to_patch_matrix,
    stable_position_mask,
    token_match_rate,
)


class TokenizerAdapterTests(unittest.TestCase):
    def test_patch_tokenizer_shape(self) -> None:
        tokenizer = PatchVQTokenizer(image_size=64, patch_size=16, levels=4)
        image = Image.new("RGB", (80, 80), color=(128, 64, 32))
        grid = tokenizer.encode_image(image)
        self.assertEqual(grid.tokens.shape, (4, 4))
        self.assertTrue(np.all(grid.tokens == grid.tokens[0, 0]))

    def test_match_and_stable_mask(self) -> None:
        tokenizer = PatchVQTokenizer(image_size=64, patch_size=16, levels=4)
        first = tokenizer.encode_image(Image.new("RGB", (64, 64), color=(128, 64, 32)))
        second = tokenizer.encode_image(Image.new("RGB", (64, 64), color=(128, 64, 32)))
        self.assertEqual(token_match_rate(first, second), 1.0)
        self.assertTrue(stable_position_mask([first, second]).all())

    def test_learned_patch_tokenizer(self) -> None:
        image_size = 32
        patch_size = 16
        dim = patch_size * patch_size * 3
        codebook = np.zeros((2, dim), dtype=np.float32)
        codebook[1, :] = 1.0
        path = ROOT / "_tmp_test_codebook.npz"
        try:
            np.savez_compressed(
                path,
                codebook=codebook,
                image_size=np.array(image_size, dtype=np.int32),
                patch_size=np.array(patch_size, dtype=np.int32),
            )
            tokenizer = LearnedPatchVQTokenizer(path)
            dark = tokenizer.encode_image(Image.new("RGB", (32, 32), color=(0, 0, 0)))
            bright = tokenizer.encode_image(Image.new("RGB", (32, 32), color=(255, 255, 255)))
            self.assertTrue(np.all(dark.tokens == 0))
            self.assertTrue(np.all(bright.tokens == 1))
        finally:
            if path.exists():
                path.unlink()


if __name__ == "__main__":
    unittest.main()
