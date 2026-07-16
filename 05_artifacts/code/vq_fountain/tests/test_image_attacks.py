from pathlib import Path
import sys
import unittest

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from vq_fountain.image_attacks import apply_attack, drop_probability, parse_crop_attack, should_drop_image


class ImageAttackTests(unittest.TestCase):
    def test_attacks_preserve_size(self) -> None:
        image = Image.new("RGB", (64, 48), color=(120, 80, 40))
        for attack in [
            "clean",
            "jpeg85",
            "resize075",
            "blur1",
            "noise002",
            "crop090",
            "crop090_r02_c-02",
            "crop090+jpeg85",
        ]:
            attacked = apply_attack(image, attack, seed="unit")
            self.assertEqual(attacked.size, image.size)
            self.assertEqual(attacked.mode, "RGB")

    def test_crop_attack_parser_supports_offsets(self) -> None:
        self.assertEqual(parse_crop_attack("crop090"), (0.9, 0.0, 0.0))
        self.assertEqual(parse_crop_attack("crop090_r02_c-02"), (0.9, 0.02, -0.02))
        self.assertEqual(parse_crop_attack("crop0.9_r0.02_c-0.02"), (0.9, 0.02, -0.02))

    def test_drop_probability_is_parsed_from_attack_chain(self) -> None:
        self.assertEqual(drop_probability("drop25"), 0.25)
        self.assertEqual(drop_probability("crop090+jpeg85+drop0.25"), 0.25)
        self.assertEqual(should_drop_image("drop100", image_index=0, seed="unit"), True)
        self.assertEqual(should_drop_image("drop0", image_index=0, seed="unit"), False)


if __name__ == "__main__":
    unittest.main()
