#!/usr/bin/env python3
"""Inter-reviewer agreement on the double-reviewed subset of the golden set.

    python review_agreement.py --dataset ../data/golden.jsonl

Reports raw agreement and Cohen's kappa (agreement corrected for chance). Rough guide:
kappa > 0.8 strong, 0.6–0.8 substantial, < 0.6 means the rubric is ambiguous — fix the
rubric before trusting the labels. The same computation calibrates an LLM judge:
put the judge's labels in one column and a human's in the other.
"""

import argparse
import json

from sklearn.metrics import cohen_kappa_score


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dataset", default="../data/golden.jsonl")
    ap.add_argument("--a", default="reviewer_a", help="field holding the first rater's label")
    ap.add_argument("--b", default="reviewer_b", help="field holding the second rater's label")
    args = ap.parse_args()

    with open(args.dataset) as f:
        rows = [json.loads(l) for l in f if l.strip()]
    pairs = [r for r in rows if r.get(args.b)]
    a = [r[args.a] for r in pairs]
    b = [r[args.b] for r in pairs]

    agree = sum(x == y for x, y in zip(a, b))
    print(f"double-reviewed examples: {len(pairs)} of {len(rows)}")
    print(f"raw agreement:            {agree}/{len(pairs)} = {agree / len(pairs):.3f}")
    print(f"Cohen's kappa:            {cohen_kappa_score(a, b):.3f}")
    print("\ndisagreements and resolution:")
    for r in pairs:
        if r[args.a] != r[args.b]:
            print(f"  {r['id']}  {args.a}={r[args.a]:9s} {args.b}={r[args.b]:9s} final={r['label']:9s} {r['text']}")
            if r.get("adjudication"):
                print(f"        -> {r['adjudication']}")


if __name__ == "__main__":
    main()
