"""Regression test for the ML router: fails, and says what dropped, on a weakened model.

    python -m unittest -v test_regression_ml                                          # real model
    EVAL_MODEL=models/router_weakened.joblib python -m unittest -v test_regression_ml  # must fail

Floors sit just under the current model (macro F1 0.85, lowest class recall 0.80).
Train first: python train.py --out models/router.joblib
"""

import json
import os
import unittest

from eval_ml import evaluate, load_model
from eval_basic import DEFAULT_SCHEMA, load_dataset

HERE = os.path.dirname(os.path.abspath(__file__))
MODEL = os.environ.get("EVAL_MODEL", os.path.join(HERE, "models", "router.joblib"))
DATASET = os.path.join(HERE, "..", "data", "golden.jsonl")

MIN_MACRO_F1 = 0.80
MIN_CLASS_RECALL = 0.70
MAX_ECE = 0.25            # confidence must stay roughly honest if we route on it
MIN_SCHEMA_VALID = 1.0    # every published message must honor the topic's contract

with open(DEFAULT_SCHEMA) as f:
    SCHEMA = json.load(f)


class TestRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        model, meta = load_model(MODEL)
        cls.report = evaluate(model, meta, load_dataset(DATASET), SCHEMA)

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

    def test_message_contract(self):
        c = self.report["contract"]
        first = "; ".join(f"{v['ticket_id']}: {v['errors'][0]}" for v in c["violations"][:3])
        self.assertGreaterEqual(
            c["schema_valid_rate"], MIN_SCHEMA_VALID,
            f"schema-valid rate dropped to {c['schema_valid_rate']:.3f} "
            f"({len(c['violations'])} of {c['n_messages']} messages break {c['schema']}), e.g. {first}")

    def test_deterministic(self):
        model, meta = load_model(MODEL)
        again = evaluate(model, meta, load_dataset(DATASET), SCHEMA)
        self.assertEqual(self.report, again, "two runs on the same inputs gave different results")


if __name__ == "__main__":
    unittest.main()
