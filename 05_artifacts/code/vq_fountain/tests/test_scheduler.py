from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from vq_fountain.scheduler import TokenCandidate, choose_token, entropy, select_positions


class SchedulerTests(unittest.TestCase):
    def test_entropy(self) -> None:
        self.assertAlmostEqual(entropy([0.5, 0.5]), 1.0)

    def test_select_positions_is_deterministic(self) -> None:
        entropies = [0.1, 1.2, 1.4, 0.9, 1.8]
        stabilities = [1.0, 0.95, 0.40, 0.99, 0.98]
        first = select_positions(entropies, stabilities, key="k", min_entropy=1.0, min_stability=0.9)
        second = select_positions(entropies, stabilities, key="k", min_entropy=1.0, min_stability=0.9)
        self.assertEqual(first, second)
        self.assertEqual(set(first), {1, 4})

    def test_choose_token_reports_leakage(self) -> None:
        candidates = [
            TokenCandidate(token_id=0, probability=0.35),
            TokenCandidate(token_id=1, probability=0.25),
            TokenCandidate(token_id=2, probability=0.20),
            TokenCandidate(token_id=3, probability=0.20),
        ]
        decision = choose_token(candidates, payload_value=1, capacity_bits=1, key="k", position=3)
        self.assertIn(decision.token_id, {1, 2})
        self.assertGreaterEqual(decision.leakage_score, 0.0)


if __name__ == "__main__":
    unittest.main()
