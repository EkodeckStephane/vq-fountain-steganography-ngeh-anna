from pathlib import Path
import sys
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from run_scale_quality_security_probe import (
    binary_auc,
    diagonal_frechet_distance,
    frechet_distance_scipy,
    frechet_distance_numpy,
    jensen_shannon_divergence,
    polynomial_mmd,
    sklearn_detection_metrics,
)


class ScaleQualitySecurityProbeTests(unittest.TestCase):
    def test_jensen_shannon_divergence_is_zero_for_equal_distributions(self) -> None:
        distribution = np.asarray([0.2, 0.3, 0.5], dtype=np.float64)
        self.assertAlmostEqual(jensen_shannon_divergence(distribution, distribution), 0.0)

    def test_diagonal_frechet_distance_is_zero_for_identical_features(self) -> None:
        features = np.asarray([[0.0, 1.0], [1.0, 2.0], [2.0, 3.0]], dtype=np.float64)
        self.assertAlmostEqual(diagonal_frechet_distance(features, features), 0.0)

    def test_numpy_fid_and_kid_are_zero_for_identical_features(self) -> None:
        features = np.asarray([[0.0, 1.0], [1.0, 2.0], [2.0, 3.0]], dtype=np.float64)
        self.assertAlmostEqual(frechet_distance_numpy(features, features), 0.0, places=8)
        self.assertAlmostEqual(frechet_distance_scipy(features, features), 0.0, places=8)
        self.assertAlmostEqual(polynomial_mmd(features, features), 0.0, places=8)

    def test_binary_auc_orders_separable_scores(self) -> None:
        labels = np.asarray([0, 0, 1, 1], dtype=np.float64)
        scores = np.asarray([0.1, 0.2, 0.8, 0.9], dtype=np.float64)
        self.assertAlmostEqual(binary_auc(labels, scores), 1.0)

    def test_sklearn_detector_runs_on_separable_features(self) -> None:
        cover = np.asarray([[0.0, 0.0], [0.1, 0.0], [0.0, 0.1], [0.1, 0.1]], dtype=np.float64)
        stego = np.asarray([[1.0, 1.0], [1.1, 1.0], [1.0, 1.1], [1.1, 1.1]], dtype=np.float64)
        result = sklearn_detection_metrics(cover, stego, seed="unit")
        self.assertGreaterEqual(result["auc"], 0.5)


if __name__ == "__main__":
    unittest.main()
