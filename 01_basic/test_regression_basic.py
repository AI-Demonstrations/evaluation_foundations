"""Regression test: fails, and says what dropped, when the model falls below the floor.

    python -m unittest -v test_regression_basic                                   # real model
    EVAL_MODEL=models/keywords_weakened.json python -m unittest -v test_regression_basic  # must fail

Floors are set a little under the current model's scores (macro F1 0.84), so ordinary
edits pass but a real regression does not. Raise them as the model improves.
"""

import json
import os
import unittest

from eval_basic import DEFAULT_SCHEMA, KeywordRouter, evaluate, load_dataset

HERE = os.path.dirname(os.path.abspath(__file__))
MODEL = os.environ.get("EVAL_MODEL", os.path.join(HERE, "models", "keywords.json"))
DATASET = os.path.join(HERE, "..", "data", "golden.jsonl")

MIN_MACRO_F1 = 0.80
MIN_CLASS_RECALL = 0.70   # no single queue may be starved
MIN_SCHEMA_VALID = 1.0    # every published message must honor the topic's contract

with open(DEFAULT_SCHEMA) as f:
    SCHEMA = json.load(f)


class TestRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = evaluate(KeywordRouter(MODEL), load_dataset(DATASET), SCHEMA)

    def test_macro_f1_floor(self):
        f1 = self.report["macro_f1"]
        self.assertGreaterEqual(
            f1, MIN_MACRO_F1,
            f"macro F1 dropped to {f1:.3f} (floor {MIN_MACRO_F1}) for model {self.report['model']}")

    def test_every_class_recall_floor(self):
        low = {l: c["recall"] for l, c in self.report["per_class"].items() if c["recall"] < MIN_CLASS_RECALL}
        self.assertFalse(
            low, f"recall below {MIN_CLASS_RECALL} for: "
                 + ", ".join(f"{l}={r:.3f}" for l, r in sorted(low.items())))

    def test_message_contract(self):
        c = self.report["contract"]
        first = "; ".join(f"{v['ticket_id']}: {v['errors'][0]}" for v in c["violations"][:3])
        self.assertGreaterEqual(
            c["schema_valid_rate"], MIN_SCHEMA_VALID,
            f"schema-valid rate dropped to {c['schema_valid_rate']:.3f} "
            f"({len(c['violations'])} of {c['n_messages']} messages break {c['schema']}), e.g. {first}")

    def test_deterministic(self):
        again = evaluate(KeywordRouter(MODEL), load_dataset(DATASET), SCHEMA)
        self.assertEqual(self.report, again, "two runs on the same inputs gave different results")


if __name__ == "__main__":
    unittest.main()
