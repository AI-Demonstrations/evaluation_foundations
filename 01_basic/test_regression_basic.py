"""Regression test: fails, and says what dropped, when the model falls below the floor.

    python -m unittest -v test_regression_basic                                   # real model
    EVAL_MODEL=models/keywords_weakened.json python -m unittest -v test_regression_basic  # must fail

Floors are set a little under the current model's scores (macro F1 0.84), so ordinary
edits pass but a real regression does not. Raise them as the model improves.
"""

import os
import unittest

from eval_basic import KeywordRouter, evaluate, load_dataset
from message_api import RouterComponent, api_check, load_contract

HERE = os.path.dirname(os.path.abspath(__file__))
MODEL = os.environ.get("EVAL_MODEL", os.path.join(HERE, "models", "keywords.json"))
DATASET = os.path.join(HERE, "..", "data", "golden.jsonl")

MIN_MACRO_F1 = 0.80
MIN_CLASS_RECALL = 0.70   # no single queue may be starved
MIN_API_VALID = 1.0       # every message must honor the component's messaging API

CONTRACT = load_contract()


class TestRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = evaluate(KeywordRouter(MODEL), load_dataset(DATASET), CONTRACT)

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
        again = evaluate(KeywordRouter(MODEL), load_dataset(DATASET), CONTRACT)
        self.assertEqual(self.report, again, "two runs on the same inputs gave different results")


class TestApiCheckCatchesComponentBugs(unittest.TestCase):
    """The model is fine; the message handling is broken. The API check must notice."""

    def test_detects_lost_correlation_and_wrong_routing_property(self):
        class BuggyComponent(RouterComponent):
            def handle(self, env):
                outs, rejected = super().handle(env)
                for o in outs:
                    o["correlation_id"] = None                  # forgot to propagate
                    o["properties"] = {"Queue": o["body"]["queue"]}   # property name typo
                return outs, rejected

        api = api_check(BuggyComponent(KeywordRouter(os.path.join(HERE, "models", "keywords.json")).route,
                                       CONTRACT), load_dataset(DATASET), CONTRACT)
        self.assertEqual(api["checks"]["body_schema"], 1.0, "the bodies themselves are valid")
        self.assertEqual(api["checks"]["correlation_id"], 0.0)
        self.assertEqual(api["checks"]["routing_property"], 0.0)
        self.assertEqual(api["checks"]["delivered_once"], 0.0, "no subscription filter matches 'Queue'")


if __name__ == "__main__":
    unittest.main()
