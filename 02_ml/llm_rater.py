#!/usr/bin/env python3
"""LLM second rater for the golden set: an independent label for the agreement check.

    # key: CLAUDKEY=... in the repo's .env file (git-ignored), or exported in the shell
    python llm_rater.py --dataset ../data/golden.jsonl --dry-run   # show the prompt, no API call
    python llm_rater.py --dataset ../data/golden.jsonl             # label, write reviewer_b
    python review_agreement.py --dataset ../data/golden.jsonl      # then compute kappa

The rater sees only the ticket text and the rubric from data/PROVENANCE.md, never your
label (reviewer_a) or the final label. It labels the double-review subset (rows that
already have a reviewer_b field, 20 here) unless --ids names others, writes its answer to
reviewer_b, and records the model, prompt and answers in data/llm_rater_run.json so the
run is documented. Disagreements are yours to adjudicate: any without a written
resolution get adjudication "PENDING".

Use a different model from the one that generated the examples, so the rater does not
share the generator's blind spots (the tickets here came from claude-opus-5-5).
"""

import argparse
import datetime
import hashlib
import json
import os
import re

import anthropic

HERE = os.path.dirname(os.path.abspath(__file__))
LABELS = ["billing", "technical", "account", "shipping"]
MODEL = "claude-opus-5"
KEY_VAR = "CLAUDKEY"
ENV_FILE = os.path.join(HERE, "..", ".env")

SYSTEM_TEMPLATE = """You label customer-support tickets for a routing system with four queues.
Apply this rubric exactly; it is the same one the human reviewer used.

{rubric}

Answer with the single queue the rubric assigns."""


def load_rubric(provenance_path):
    """The '## Review rubric' section of PROVENANCE.md, so the rater and the human share one rubric."""
    text = open(provenance_path).read()
    m = re.search(r"^## Review rubric\s*\n(.*?)(?=^## )", text, re.S | re.M)
    if not m:
        raise SystemExit(f"no '## Review rubric' section in {provenance_path}")
    return m.group(1).strip()


def load_api_key(env_file=ENV_FILE):
    """CLAUDKEY from the shell, else from the .env file; the key never goes in code or git."""
    if os.environ.get(KEY_VAR):
        return os.environ[KEY_VAR]
    if os.path.exists(env_file):
        for line in open(env_file):
            name, sep, value = line.strip().partition("=")
            if sep and name.strip().removeprefix("export ").strip() == KEY_VAR:
                return value.strip().strip("'\"")
    raise SystemExit(f"no {KEY_VAR}: set it in {os.path.normpath(env_file)} or export it")


def rate(client, system, ticket_text):
    response = client.beta.messages.create(
        model=MODEL,
        max_tokens=2048,
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",                      # a declined request is re-run on a fallback model
        output_config={
            "effort": "low",                      # a four-way classification needs little deliberation
            "format": {
                "type": "json_schema",
                "schema": {
                    "type": "object",
                    "properties": {"queue": {"type": "string", "enum": LABELS}},
                    "required": ["queue"],
                    "additionalProperties": False,
                },
            },
        },
        system=system,
        messages=[{"role": "user", "content": f"Ticket:\n{ticket_text}"}],
    )
    if response.stop_reason == "refusal":
        raise RuntimeError(f"rater declined: {response.stop_details}")
    text = next(b.text for b in response.content if b.type == "text")
    return json.loads(text)["queue"], response.model


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dataset", default=os.path.join(HERE, "..", "data", "golden.jsonl"))
    ap.add_argument("--provenance", default=os.path.join(HERE, "..", "data", "PROVENANCE.md"))
    ap.add_argument("--ids", nargs="*", help="example ids to rate (default: rows that have a reviewer_b field)")
    ap.add_argument("--record", default=os.path.join(HERE, "..", "data", "llm_rater_run.json"),
                    help="where to write the run record (model, prompt, answers)")
    ap.add_argument("--dry-run", action="store_true", help="print the prompt for the first example and stop")
    args = ap.parse_args()

    rows = [json.loads(line) for line in open(args.dataset) if line.strip()]
    ids = set(args.ids) if args.ids else {r["id"] for r in rows if r.get("reviewer_b") is not None}
    targets = [r for r in rows if r["id"] in ids]
    system = SYSTEM_TEMPLATE.format(rubric=load_rubric(args.provenance))

    if args.dry_run:
        print(f"model: {MODEL}\nexamples to rate: {len(targets)}\n\n--- system ---\n{system}\n\n"
              f"--- user ({targets[0]['id']}) ---\nTicket:\n{targets[0]['text']}")
        return

    client = anthropic.Anthropic(api_key=load_api_key())
    answers, served_by = {}, set()
    for r in targets:
        answers[r["id"]], model = rate(client, system, r["text"])
        served_by.add(model)
        mark = "" if answers[r["id"]] == r["reviewer_a"] else "   <- disagrees with reviewer_a"
        print(f"{r['id']}  {answers[r['id']]:<10}{mark}")

    for r in rows:
        if r["id"] in answers:
            r["reviewer_b"] = answers[r["id"]]
            if r["reviewer_b"] == r["reviewer_a"]:
                r["adjudication"] = None
            elif not r.get("adjudication"):
                r["adjudication"] = "PENDING"
    with open(args.dataset, "w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    record = {
        "date": datetime.date.today().isoformat(),
        "model": MODEL,
        "served_by": sorted(served_by),
        "settings": {"effort": "low", "output": "json_schema enum of queues", "fallbacks": "default"},
        "system_prompt": system,
        "user_prompt": "Ticket:\n{text}",
        "prompt_sha256": hashlib.sha256(system.encode()).hexdigest()[:16],
        "answers": dict(sorted(answers.items())),
    }
    with open(args.record, "w") as f:
        json.dump(record, f, indent=2, ensure_ascii=False)
        f.write("\n")
    pending = sum(1 for r in rows if r.get("adjudication") == "PENDING")
    print(f"\nwrote reviewer_b for {len(answers)} examples to {args.dataset}; run record in {args.record}")
    if pending:
        print(f"{pending} disagreement(s) need your adjudication (adjudication = \"PENDING\")")


if __name__ == "__main__":
    main()
