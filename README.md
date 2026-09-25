# Evaluation Foundations — Module 05 Examples

Two runnable examples of an **offline evaluation harness** for EN.705.704 Module 05
(*Eval Harness & Golden Dataset*). Both evaluate the same task — routing customer-support
tickets to one of four queues (`billing`, `technical`, `account`, `shipping`) — against the
same 60-example golden dataset, so their numbers are directly comparable.

**Where this sits in the course.** Module 05 builds the measuring tool; Module 07 uses it to
choose a model. In week 5 your team has not selected a model yet, so the harness is built and
tested against a **baseline**, and Module 07 later runs each candidate through the same harness
and golden set. The two examples play those two roles:

- `01_basic/` — the **week-5 baseline**: simple rules a team can write before any model is chosen.
  This is the "real model" the Module 05 regression test runs against.
- `02_ml/` — a **Module 07-style candidate**: a trained model evaluated by the same dataset contract,
  so its scores line up with the baseline's. Swap in each of your candidates the same way.

| | `01_basic/` — baseline | `02_ml/` — candidate |
|---|---|---|
| Model | Keyword rules from a JSON config | TF-IDF + logistic regression (scikit-learn) |
| Dependencies | Python standard library only | numpy, scikit-learn |
| Metrics | Accuracy, per-class P/R/F1, confusion matrix — computed by hand | Same via scikit-learn, **plus** bootstrap 95% CIs, per-slice metrics, calibration (Brier, ECE) |
| Weakened model | `models/keywords_weakened.json` | `train.py --weaken` |
| Message contract | Every published message validated against `data/schemas/` | Same check, shared code |
| Extra | — | Reviewer agreement (Cohen's kappa), evidence script |

## Quick start

```bash
pip install -r requirements.txt

# Basic — standard library only
cd 01_basic
python eval_basic.py --model models/keywords.json --dataset ../data/golden.jsonl
python -m unittest -v test_regression_basic
EVAL_MODEL=models/keywords_weakened.json python -m unittest -v test_regression_basic   # fails, by design

# ML
cd ../02_ml
python train.py --out models/router.joblib
python eval_ml.py --model models/router.joblib --dataset ../data/golden.jsonl
./run_evidence.sh          # every piece of committed evidence the deliverable asks for, into logs/
```

Tested on Python 3.9 with scikit-learn 1.6 and numpy 2.0. `pytest` runs the tests
unchanged if you prefer it to `unittest`.

## How the examples map to the deliverable

| Deliverable requirement | Where it is shown |
|---|---|
| Harness runs from one command with a model ref and a dataset path | `eval_basic.py` / `eval_ml.py --model … --dataset …` |
| Structured report | `reports/<model>.json` and `reports/<model>.md` |
| Fixed seeds; two runs give identical scores | Scores fingerprint printed each run; `02_ml/logs/run1.log` vs `run2.log`, `determinism.log` |
| Regression test fails on a weakened model and says what dropped | `test_regression_*.py`; `02_ml/logs/test_real_model.log` and `test_weakened_model.log` |
| Golden dataset: curated, provenance, human review, agreement on ≥ 20 | `data/golden.jsonl`, `data/PROVENANCE.md`, `02_ml/review_agreement.py` |
| Classification metrics: precision, recall, F1, confusion matrix | Both reports |
| Output conforms to the component's message contract | Schema-valid rate in both reports; `test_message_contract` |
| README defines each metric and what good and bad look like | Below |

## Results on the golden set

| Model | Accuracy | Macro F1 | Notes |
|---|---|---|---|
| Keyword rules | 0.833 | 0.840 | 100% schema-valid. High precision, but anything without a keyword falls through to `technical` (P = 0.63) |
| Keyword rules, weakened | 0.100 | 0.180 | Falls back to queue `other`, which is not in the contract: 10% schema-valid. Test fails on F1, recall and contract |
| TF-IDF + LogReg | 0.850 | 0.854 (95% CI 0.75–0.93) | 100% schema-valid. Errors spread across classes; under-confident (ECE 0.18) |
| TF-IDF + LogReg, weakened | 0.633 | 0.628 | Still schema-valid, so contract passes; test fails on F1, recall and calibration |

**The lesson in these numbers:** the ML model "wins" by 0.014 F1, well inside its
confidence interval. On 60 examples, you *cannot* claim it is better. Either grow the golden
set or compare on the errors themselves. Report intervals, not just point scores.

A second lesson came from building `01_basic/models/keywords.json`: a first draft of the
rules, written while looking at the golden set, scored 0.97; the generic rules shipped here
score 0.84. Rules (or prompts, or
hyperparameters) tuned on the evaluation set measure memory, not skill. Tune on something
else; touch the golden set only to evaluate.

## The message contract (topics)

The router is one component in a pub/sub system: it consumes `tickets.incoming` and
publishes a `TicketRouted` message on the `tickets.routed` topic, where each queue's worker
has a filtered subscription. The message payload is defined in
`data/schemas/ticket-routed.v1.schema.json`, the kind of JSON Schema file Module 02 asks
each team to commit for its interfaces. The harness reads that **same** file, so the
contract and the evaluation cannot drift apart.

`data/schemas/asyncapi.yaml` is optional, extra reading. It shows how the topic layout
(topics, publishers, subscribers) can be described alongside the JSON Schema, using AsyncAPI,
the pub/sub counterpart of OpenAPI. The harness does not need it.

**What the harness checks (Module 05, offline).** For every golden example it builds the
exact message the router would publish, validates it against the schema, and reports the
**schema-valid rate** and each violation. This belongs in the evaluation because it is a
property of the *model's output*. A rule set can fall back to a queue that doesn't exist, and
an LLM will sometimes return malformed JSON, a missing field or an invented label, at a rate
that only a dataset can measure. It also matters for Module 07, since candidate models differ
in how reliably they hold a format.

**What the harness does not check (Modules 08–09).** It never touches a live topic. Whether
messages are *delivered* belongs in the Module 08 integration tests and the Module 09
deployed stack, not in a deterministic offline harness. Those checks are that every
subscription receives the message, filters route correctly, malformed messages dead-letter
instead of crashing a consumer, redelivery is idempotent, and correlation IDs survive the hop.

`01_basic/schema_check.py` is a small standard-library validator covering the keywords a
message contract usually needs. For full JSON Schema support, `pip install jsonschema` and
swap it in.

## Metric definitions — what a score means for this task

- **Precision (per queue)** — of the tickets routed to this queue, the share that belong
  there. 0.8 means one in five tickets a team receives is someone else's work. Low
  precision wastes agent time on re-routing.
- **Recall (per queue)** — of the tickets that belong in this queue, the share that reached
  it. 0.8 means one in five of this team's customers waits in the wrong queue. Low recall
  delays customers. The tests set a floor on recall for *every* queue, so a model can't
  score well overall by ignoring a small queue.
- **F1** — the harmonic mean of precision and recall; high only when both are.
  **Macro F1** averages F1 over queues equally, so small queues count as much as large ones.
  Good here: ≥ 0.85. Bad: < 0.75, which means roughly a quarter of routing decisions need a human.
- **Confusion matrix** — rows are true queues, columns predicted. Read the off-diagonal cells:
  they show *which* queues get mixed up (here, billing ↔ shipping), which tells you what to fix.
- **Bootstrap 95% CI** — resample the golden set 1,000 times (seeded) and take the middle 95%
  of scores. A wide interval means the dataset is too small to separate the models you are comparing.
- **Per-slice metrics** — the same metrics restricted to `channel = email` or `chat`. A good
  average can hide a slice that fails; a gap of more than ~0.1 is worth investigating.
- **Brier score / ECE (calibration)** — whether the model's confidence matches its accuracy.
  ECE 0.05 means confidence is honest to within 5 points; ECE 0.18 (this model) means it
  is right far more often than it claims. That matters if you route low-confidence tickets
  to a human: the threshold you pick will be wrong unless calibration is good.
- **Schema-valid rate (message contract)** — the share of published messages that pass the
  topic's payload schema. The target is **1.0**: a single invalid message is dead-lettered
  or, worse, crashes a subscriber. Anything below 1.0 fails the regression test, and the
  report lists which tickets broke which rule. For an LLM component, expect this to be the
  first metric that moves when you change the prompt or the model.
- **Cohen's kappa (reviewer agreement)** — agreement between two labelers corrected for
  chance. ≥ 0.8 strong, 0.6–0.8 substantial (this set: 0.73), < 0.6 means the rubric is
  ambiguous. The same measure is how you **calibrate an LLM judge**: score the judge's labels
  against a human's on ≥ 20 examples.

## Adapting this to your team's project

1. Define the harness interface first: what goes in (model reference, dataset path) and
   what comes out (report schema). Then build the dataset to fit it.
2. Replace `golden.jsonl` with your own ≥ 50 examples covering every component, with real
   reviewers in `reviewer_a` / `reviewer_b` and the source of each example.
3. Start with a baseline: rules, a heuristic, or one default model you expect to be a
   candidate. Replace the model loader (`KeywordRouter` / `load_model`) with it, and make
   `--model` accept an API endpoint, a checkpoint or a config, so that in Module 07 each
   candidate plugs in without code changes. Keep the `evaluate()` → report contract.
4. For generative output, add an LLM-as-judge metric, and use `review_agreement.py --a judge
   --b human` to report its agreement with human labels.
5. Point `--schema` at the message schema in your Module 02 contract (the JSON Schema file,
   or the schema extracted from your OpenAPI file), and build each output into the exact
   message your component publishes before validating it.
6. Set the regression floors just under your current scores, and commit the logs.

> The golden-set tickets were generated with Claude (claude-opus-5-5) and the reviewer
> labels are illustrative. See `data/PROVENANCE.md`.
