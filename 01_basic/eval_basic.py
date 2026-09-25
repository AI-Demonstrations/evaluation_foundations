#!/usr/bin/env python3
"""Basic evaluation harness — standard library only.

The "model" is a keyword router loaded from a JSON config. The point is the harness
around it: one command, a model reference and a dataset in, metrics computed from
first principles, a structured report out, and identical scores on every run.

The harness also checks the router's *output message* — the payload it would publish
on the tickets.routed topic — against the message schema from the component contract,
and reports the schema-valid rate. (Delivery over the live topic is tested later, in
the Module 08 integration tests.)

    python eval_basic.py --model models/keywords.json --dataset ../data/golden.jsonl
"""

import argparse
import hashlib
import json
import os
from collections import Counter

from schema_check import validate

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_SCHEMA = os.path.join(HERE, "..", "data", "schemas", "ticket-routed.v1.schema.json")
HUMAN_REVIEW_BELOW = 0.5


# --------------------------------------------------------------------------- model
class KeywordRouter:
    """Scores each label by how many of its keywords appear; ties go to label order."""

    def __init__(self, config_path):
        with open(config_path) as f:
            cfg = json.load(f)
        self.name = cfg["name"]
        self.keywords = cfg["keywords"]
        self.default = cfg["default_label"]

    def route(self, text):
        """Return (label, confidence); confidence = share of keyword hits won by the label."""
        t = text.lower()
        scores = {label: sum(kw in t for kw in kws) for label, kws in self.keywords.items()}
        best = max(scores, key=scores.get)
        total = sum(scores.values())
        if total == 0:
            return self.default, 0.0
        return best, round(scores[best] / total, 4)

    def predict(self, text):
        return self.route(text)[0]


def to_message(row, label, confidence):
    """The TicketRouted payload the router publishes (see data/schemas/)."""
    return {"schema_version": "1.0", "ticket_id": row["id"], "queue": label,
            "confidence": confidence, "needs_human": confidence < HUMAN_REVIEW_BELOW}


def contract_check(messages, schema):
    """Validate every published message; return the schema-valid rate and the violations."""
    violations = []
    for m in messages:
        errs = validate(m, schema)
        if errs:
            violations.append({"ticket_id": m.get("ticket_id"), "errors": errs})
    return {"schema": schema.get("title", ""), "n_messages": len(messages),
            "schema_valid_rate": round(1 - len(violations) / len(messages), 4),
            "violations": violations}


# --------------------------------------------------------------------------- data
def load_dataset(path):
    with open(path) as f:
        rows = [json.loads(line) for line in f if line.strip()]
    for r in rows:
        assert {"id", "text", "label"} <= r.keys(), f"example missing fields: {r}"
    return rows


# --------------------------------------------------------------------------- metrics
OFF_CONTRACT = "(off-contract)"


def confusion_matrix(y_true, y_pred, labels, cols):
    """matrix[i][j] = count of examples whose true label is labels[i], predicted cols[j].

    cols is labels plus, when needed, an OFF_CONTRACT column for predictions that are
    not a valid queue at all — they count as misses for the true label.
    """
    ri = {l: i for i, l in enumerate(labels)}
    ci = {l: i for i, l in enumerate(cols)}
    m = [[0] * len(cols) for _ in labels]
    for t, p in zip(y_true, y_pred):
        m[ri[t]][ci[p]] += 1
    return m


def per_class_metrics(matrix, labels):
    out = {}
    for i, label in enumerate(labels):
        tp = matrix[i][i]
        fp = sum(matrix[r][i] for r in range(len(labels))) - tp   # predicted label, wasn't
        fn = sum(matrix[i]) - tp                                  # was label, predicted other
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        out[label] = {"precision": round(precision, 4), "recall": round(recall, 4),
                      "f1": round(f1, 4), "support": tp + fn}
    return out


def evaluate(model, rows, schema):
    labels = sorted({r["label"] for r in rows})
    y_true = [r["label"] for r in rows]
    routed = [model.route(r["text"]) for r in rows]
    y_pred = [label for label, _ in routed]
    contract = contract_check([to_message(r, l, c) for r, (l, c) in zip(rows, routed)], schema)
    y_pred_cm = [p if p in labels else OFF_CONTRACT for p in y_pred]
    cols = labels + ([OFF_CONTRACT] if OFF_CONTRACT in y_pred_cm else [])
    matrix = confusion_matrix(y_true, y_pred_cm, labels, cols)
    per_class = per_class_metrics(matrix, labels)
    accuracy = sum(t == p for t, p in zip(y_true, y_pred)) / len(rows)
    macro_f1 = sum(c["f1"] for c in per_class.values()) / len(labels)
    errors = [{"id": r["id"], "text": r["text"], "label": t, "predicted": p}
              for r, t, p in zip(rows, y_true, y_pred) if t != p]
    return {
        "model": model.name,
        "n_examples": len(rows),
        "label_counts": dict(sorted(Counter(y_true).items())),
        "accuracy": round(accuracy, 4),
        "macro_f1": round(macro_f1, 4),
        "per_class": per_class,
        "confusion_matrix": {"labels": labels, "columns": cols, "rows_true_cols_pred": matrix},
        "contract": contract,
        "errors": errors,
    }


def scores_fingerprint(report):
    """Hash of the scores only — two runs on the same inputs must print the same value."""
    scores = {k: report[k] for k in ("accuracy", "macro_f1", "per_class", "confusion_matrix", "contract")}
    return hashlib.sha256(json.dumps(scores, sort_keys=True).encode()).hexdigest()[:16]


# --------------------------------------------------------------------------- report
def to_markdown(report):
    labels = report["confusion_matrix"]["labels"]
    lines = [f"# Eval report — {report['model']}", "",
             f"- Examples: {report['n_examples']}",
             f"- Accuracy: **{report['accuracy']:.3f}**",
             f"- Macro F1: **{report['macro_f1']:.3f}**",
             f"- Schema-valid messages: **{report['contract']['schema_valid_rate']:.1%}** "
             f"({report['contract']['schema']})",
             f"- Scores fingerprint: `{report['fingerprint']}`", "",
             "## Per class", "", "| Label | Precision | Recall | F1 | Support |", "|---|---|---|---|---|"]
    for l, c in report["per_class"].items():
        lines.append(f"| {l} | {c['precision']:.3f} | {c['recall']:.3f} | {c['f1']:.3f} | {c['support']} |")
    lines += ["", "## Confusion matrix (rows = true, columns = predicted)", "",
              "| | " + " | ".join(report["confusion_matrix"]["columns"]) + " |",
              "|---" * (len(report["confusion_matrix"]["columns"]) + 1) + "|"]
    for l, row in zip(labels, report["confusion_matrix"]["rows_true_cols_pred"]):
        lines.append(f"| **{l}** | " + " | ".join(map(str, row)) + " |")
    lines += ["", "## Message contract", "",
              f"{report['contract']['n_messages'] - len(report['contract']['violations'])} of "
              f"{report['contract']['n_messages']} published messages match the schema.", ""]
    for v in report["contract"]["violations"][:20]:
        lines.append(f"- `{v['ticket_id']}`: " + "; ".join(v["errors"]))
    lines += ["", f"## Errors ({len(report['errors'])})", "", "| ID | True | Predicted | Text |", "|---|---|---|---|"]
    for e in report["errors"]:
        lines.append(f"| {e['id']} | {e['label']} | {e['predicted']} | {e['text']} |")
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", required=True, help="path to a keyword-router JSON config")
    ap.add_argument("--dataset", required=True, help="path to golden JSONL")
    ap.add_argument("--schema", default=DEFAULT_SCHEMA, help="JSON Schema of the published message")
    ap.add_argument("--out", default="reports", help="directory for report.json / report.md")
    args = ap.parse_args()

    with open(args.schema) as f:
        schema = json.load(f)
    report = evaluate(KeywordRouter(args.model), load_dataset(args.dataset), schema)
    report["fingerprint"] = scores_fingerprint(report)

    os.makedirs(args.out, exist_ok=True)
    stem = os.path.splitext(os.path.basename(args.model))[0]
    with open(os.path.join(args.out, f"{stem}.json"), "w") as f:
        json.dump(report, f, indent=2)
    with open(os.path.join(args.out, f"{stem}.md"), "w") as f:
        f.write(to_markdown(report))

    print(f"model={report['model']} n={report['n_examples']} "
          f"accuracy={report['accuracy']:.4f} macro_f1={report['macro_f1']:.4f} "
          f"schema_valid={report['contract']['schema_valid_rate']:.4f} fingerprint={report['fingerprint']}")
    for l, c in report["per_class"].items():
        print(f"  {l:10s} P={c['precision']:.3f} R={c['recall']:.3f} F1={c['f1']:.3f}")
    print(f"report written to {args.out}/{stem}.md")


if __name__ == "__main__":
    main()
