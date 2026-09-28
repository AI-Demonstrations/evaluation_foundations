"""Regression test for the ML router: fails, and says what dropped, on a weakened model.

    python -m unittest -v test_regression_ml                                          # real model
    EVAL_MODEL=models/router_weakened.joblib python -m unittest -v test_regression_ml  # must fail

Floors sit just under the current model (macro F1 0.85, lowest class recall 0.80).
Train first: python train.py --out models/router.joblib
"""

import os
import unittest

from eval_ml import evaluate, load_model
from eval_basic import load_dataset
from message_api import load_contract

HERE = os.path.dirname(os.path.abspath(__file__))
MODEL = os.environ.get("EVAL_MODEL", os.path.join(HERE, "models", "router.joblib"))
DATASET = os.path.join(HERE, "..", "data", "golden.jsonl")

MIN_MACRO_F1 = 0.80
MIN_CLASS_RECALL = 0.70
MAX_ECE = 0.25            # confidence must stay roughly honest if we route on it
MIN_API_VALID = 1.0       # every message must honor the component's messaging API

CONTRACT = load_contract()


class TestRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        model, meta = load_model(MODEL)
        cls.report = evaluate(model, meta, load_dataset(DATASET), CONTRACT)

    def test_macro_f1_floor(self):
        f1 = self.report["macro_f1"]
        self.assertGreaterEqual(
            f1, MIN_MACRO_F1,
            f"macro F1 dropped to {f1:.3f} (floor {MIN_MACRO_F1}) for model {self.report['model']}")

    def test_every_class_recall_floor(self):
        low = {l: c["recall"] for l, c in self.report["per_class"].items() if c["recall"] < MIN_CLASS_RECALL}
        self.assertFalse(low, f"recall below {MIN_CLASS_RECALL} for: "
                              + ", ".join(f"{l}={r:.3f}" for l, r in sorted(low.items())))

    def test_calibration_ceiling(self):
        ece = self.report["calibration"]["ece"]
        self.assertLessEqual(ece, MAX_ECE, f"expected calibration error rose to {ece:.3f} (ceiling {MAX_ECE})")

    def test_message_api(self):
        api = self.report["message_api"]
        failing = {k: v for k, v in api["checks"].items() if v < 1.0}
        first = "; ".join(f"{v['ticket_id']}: {v['failed'][0]}" for v in api["violations"][:3])
        self.assertGreaterEqual(
            api["api_valid_rate"], MIN_API_VALID,
            f"message API valid rate dropped to {api['api_valid_rate']:.3f}; failing checks "
            f"{failing}; e.g. {first}")

    def test_malformed_input_rejected(self):
        bad = [r["case"] for r in self.report["message_api"]["robustness"] if not r["rejected"]]
        self.assertFalse(bad, f"component accepted or crashed on malformed input: {bad}")

    def test_deterministic(self):
        model, meta = load_model(MODEL)
        again = evaluate(model, meta, load_dataset(DATASET), CONTRACT)
        self.assertEqual(self.report, again, "two runs on the same inputs gave different results")


if __name__ == "__main__":
    unittest.main()
