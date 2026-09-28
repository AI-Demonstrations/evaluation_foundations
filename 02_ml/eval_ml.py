#!/usr/bin/env python3
"""ML evaluation harness: one command, model + dataset in, structured report out.

    python eval_ml.py --model models/router.joblib --dataset ../data/golden.jsonl

Adds to the basic harness:
  * scikit-learn metrics (precision / recall / F1 / confusion matrix)
  * bootstrap 95% confidence intervals — 60 examples is small; know your error bars
  * per-slice metrics (by `channel`) — an average can hide a slice that fails
  * probability calibration (Brier score, expected calibration error) — is the
    model's confidence trustworthy enough to route on, or to escalate when low?
  * message API — the model is wrapped in the same RouterComponent as the basic harness
    and driven through its topics (message_api.py): published messages, routing and
    delivery, and rejection of malformed input are all checked
All randomness is seeded, so two runs give identical scores and fingerprints.
"""

import argparse
import hashlib
import json
import os
import sys

import joblib
import numpy as np
from sklearn.metrics import (accuracy_score, confusion_matrix, f1_score,
                             precision_recall_fscore_support)

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "01_basic"))
from eval_basic import load_dataset  # noqa: E402
from message_api import DEFAULT_CONTRACT, RouterComponent, api_check, api_markdown, load_contract  # noqa: E402

SEED = 704
N_BOOT = 1000
LOW_CONFIDENCE = 0.5


def load_model(path):
    bundle = joblib.load(path)
    return bundle["model"], bundle["meta"]


def bootstrap_ci(y_true, y_pred, metric, rng):
    n = len(y_true)
    stats = []
    for _ in range(N_BOOT):
        idx = rng.integers(0, n, n)
        stats.append(metric(y_true[idx], y_pred[idx]))
    lo, hi = np.percentile(stats, [2.5, 97.5])
    return [round(float(lo), 4), round(float(hi), 4)]


def calibration(y_true, proba, classes, n_bins=5):
    onehot = (y_true[:, None] == classes[None, :]).astype(float)
    brier = float(np.mean(np.sum((proba - onehot) ** 2, axis=1)))
    conf = proba.max(axis=1)
    correct = (classes[proba.argmax(axis=1)] == y_true).astype(float)
    bins = np.linspace(0, 1, n_bins + 1)
    ece, table = 0.0, []
    for lo, hi in zip(bins[:-1], bins[1:]):
        mask = (conf > lo) & (conf <= hi)
        if mask.any():
            gap = abs(conf[mask].mean() - correct[mask].mean())
            ece += mask.mean() * gap
            table.append({"bin": f"{lo:.1f}-{hi:.1f}", "n": int(mask.sum()),
                          "mean_confidence": round(float(conf[mask].mean()), 4),
                          "accuracy": round(float(correct[mask].mean()), 4)})
    return {"brier": round(brier, 4), "ece": round(float(ece), 4),
            "low_confidence_rate": round(float((conf < LOW_CONFIDENCE).mean()), 4),
            "reliability_table": table}


def route_fn(model):
    """Adapt the sklearn pipeline to the component's route(text) -> (label, confidence)."""
    classes = list(model.classes_)

    def route(text):
        proba = model.predict_proba([text])[0]
        i = int(np.argmax(proba))
        return str(classes[i]), round(float(proba[i]), 4)
    return route


def evaluate(model, meta, rows, contract):
    rng = np.random.default_rng(SEED)
    texts = [r["text"] for r in rows]
    y_true = np.array([r["label"] for r in rows])
    classes = np.array(model.classes_)
    proba = model.predict_proba(texts)
    y_pred = classes[proba.argmax(axis=1)]
    labels = sorted({str(y) for y in y_true})

    p, r, f, s = precision_recall_fscore_support(y_true, y_pred, labels=labels, zero_division=0)
    macro_f1 = lambda a, b: f1_score(a, b, labels=labels, average="macro", zero_division=0)  # noqa: E731

    slices = {}
    for ch in sorted({row["channel"] for row in rows}):
        m = np.array([row["channel"] == ch for row in rows])
        slices[ch] = {"n": int(m.sum()), "accuracy": round(float(accuracy_score(y_true[m], y_pred[m])), 4),
                      "macro_f1": round(float(macro_f1(y_true[m], y_pred[m])), 4)}

    conf = proba.max(axis=1)
    message_api = api_check(RouterComponent(route_fn(model), contract), rows, contract)
    errors = [{"id": row["id"], "text": row["text"], "label": t, "predicted": pr, "confidence": round(float(c), 3)}
              for row, t, pr, c in zip(rows, y_true, y_pred, conf) if t != pr]

    return {
        "model": meta["name"], "model_meta": meta, "n_examples": len(rows), "seed": SEED,
        "accuracy": round(float(accuracy_score(y_true, y_pred)), 4),
        "accuracy_ci95": bootstrap_ci(y_true, y_pred, accuracy_score, rng),
        "macro_f1": round(float(macro_f1(y_true, y_pred)), 4),
        "macro_f1_ci95": bootstrap_ci(y_true, y_pred, macro_f1, rng),
        "per_class": {l: {"precision": round(float(p[i]), 4), "recall": round(float(r[i]), 4),
                          "f1": round(float(f[i]), 4), "support": int(s[i])} for i, l in enumerate(labels)},
        "confusion_matrix": {"labels": labels,
                             "rows_true_cols_pred": confusion_matrix(y_true, y_pred, labels=labels).tolist()},
        "slices": {"channel": slices},
        "calibration": calibration(y_true, proba, classes),
        "message_api": message_api,
        "errors": errors,
    }


def fingerprint(report):
    keep = {k: v for k, v in report.items() if k not in ("errors", "model_meta")}
    return hashlib.sha256(json.dumps(keep, sort_keys=True).encode()).hexdigest()[:16]


def to_markdown(rep):
    labels = rep["confusion_matrix"]["labels"]
    cal = rep["calibration"]
    L = [f"# Eval report — {rep['model']}", "",
         f"- Examples: {rep['n_examples']} · seed {rep['seed']} · trained on {rep['model_meta']['n_train']} "
         f"(data sha `{rep['model_meta']['train_data_sha']}`)",
         f"- Accuracy: **{rep['accuracy']:.3f}** (95% CI {rep['accuracy_ci95'][0]:.3f}–{rep['accuracy_ci95'][1]:.3f})",
         f"- Macro F1: **{rep['macro_f1']:.3f}** (95% CI {rep['macro_f1_ci95'][0]:.3f}–{rep['macro_f1_ci95'][1]:.3f})",
         f"- Calibration: Brier {cal['brier']:.3f} · ECE {cal['ece']:.3f} · "
         f"{cal['low_confidence_rate']:.0%} of predictions below {LOW_CONFIDENCE} confidence",
         f"- Message API: **{rep['message_api']['api_valid_rate']:.1%}** of messages pass every check "
         f"(malformed inputs rejected {rep['message_api']['malformed_rejected_rate']:.1%})",
         f"- Scores fingerprint: `{rep['fingerprint']}`", "",
         "## Per class", "", "| Label | Precision | Recall | F1 | Support |", "|---|---|---|---|---|"]
    L += [f"| {l} | {c['precision']:.3f} | {c['recall']:.3f} | {c['f1']:.3f} | {c['support']} |"
          for l, c in rep["per_class"].items()]
    L += ["", "## Confusion matrix (rows = true, columns = predicted)", "",
          "| | " + " | ".join(labels) + " |", "|---" * (len(labels) + 1) + "|"]
    L += [f"| **{l}** | " + " | ".join(map(str, row)) + " |"
          for l, row in zip(labels, rep["confusion_matrix"]["rows_true_cols_pred"])]
    L += ["", "## Slices (channel)", "", "| Channel | N | Accuracy | Macro F1 |", "|---|---|---|---|"]
    L += [f"| {k} | {v['n']} | {v['accuracy']:.3f} | {v['macro_f1']:.3f} |" for k, v in rep["slices"]["channel"].items()]
    L += ["", "## Reliability (is confidence honest?)", "", "| Confidence bin | N | Mean confidence | Accuracy |",
          "|---|---|---|---|"]
    L += [f"| {b['bin']} | {b['n']} | {b['mean_confidence']:.3f} | {b['accuracy']:.3f} |" for b in cal["reliability_table"]]
    L += [""] + api_markdown(rep["message_api"])
    L += ["", f"## Errors ({len(rep['errors'])})", "", "| ID | True | Predicted | Confidence | Text |", "|---|---|---|---|---|"]
    L += [f"| {e['id']} | {e['label']} | {e['predicted']} | {e['confidence']:.2f} | {e['text']} |" for e in rep["errors"]]
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", required=True, help="path to a trained .joblib bundle")
    ap.add_argument("--dataset", required=True, help="path to golden JSONL")
    ap.add_argument("--contract", default=DEFAULT_CONTRACT, help="the component's messaging contract (JSON)")
    ap.add_argument("--out", default="reports")
    args = ap.parse_args()

    model, meta = load_model(args.model)
    rep = evaluate(model, meta, load_dataset(args.dataset), load_contract(args.contract))
    rep["fingerprint"] = fingerprint(rep)

    os.makedirs(args.out, exist_ok=True)
    stem = os.path.splitext(os.path.basename(args.model))[0]
    with open(os.path.join(args.out, f"{stem}.json"), "w") as f:
        json.dump(rep, f, indent=2)
    with open(os.path.join(args.out, f"{stem}.md"), "w") as f:
        f.write(to_markdown(rep))

    print(f"model={rep['model']} n={rep['n_examples']} accuracy={rep['accuracy']:.4f} "
          f"macro_f1={rep['macro_f1']:.4f} ci95={rep['macro_f1_ci95']} "
          f"ece={rep['calibration']['ece']:.4f} api_valid={rep['message_api']['api_valid_rate']:.4f} fingerprint={rep['fingerprint']}")
    for l, c in rep["per_class"].items():
        print(f"  {l:10s} P={c['precision']:.3f} R={c['recall']:.3f} F1={c['f1']:.3f}")
    print(f"report written to {args.out}/{stem}.md")


if __name__ == "__main__":
    main()
