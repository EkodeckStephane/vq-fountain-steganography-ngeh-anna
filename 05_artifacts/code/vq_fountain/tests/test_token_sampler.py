from pathlib import Path
import sys
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from vq_fountain.token_sampler import PriorBinCodec, bytes_to_values, values_to_bytes


class TokenSamplerTests(unittest.TestCase):
    def test_values_roundtrip(self) -> None:
        data = b"\x03\xff\x80"
        values = bytes_to_values(data, capacity_bits=2)
        self.assertEqual(values_to_bytes(values, capacity_bits=2, output_size=len(data)), data)

    def test_prior_codec_decodes_sampled_token(self) -> None:
        prior = np.array([0.20, 0.20, 0.20, 0.20, 0.20], dtype=np.float64)
        codebook = np.linspace(0, 1, 5 * 12, dtype=np.float32).reshape(5, 12)
        codec = PriorBinCodec(prior=prior, capacity_bits=1, codebook=codebook)
        sample = codec.sample_token(value=1, key="unit", position=0)
        self.assertEqual(codec.decode_value(sample.token_id), 1)
        self.assertGreaterEqual(sample.leakage_score, 0.0)

    def test_naive_codec_uses_token_id_modulo_bins(self) -> None:
        prior = np.ones(8, dtype=np.float64)
        codec = PriorBinCodec(prior=prior, capacity_bits=2, mode="naive")
        for token_id in range(8):
            self.assertEqual(codec.decode_value(token_id), token_id % 4)


if __name__ == "__main__":
    unittest.main()
