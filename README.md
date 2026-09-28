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
| Messaging API | Driven through its topics: 9 checks per message, 7 malformed inputs (`message_api.py`) | Same check, shared code |
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

## Running the regression tests (`unittest`)

The regression tests use `unittest`, Python's built-in test framework, so they need nothing
beyond the standard library. It works like this:

1. A test file contains classes that subclass `unittest.TestCase`.
2. Every method whose name starts with `test_` is one test. The runner finds and runs them all.
3. `setUpClass` runs once before a class's tests. Here it runs the full evaluation once and
   stores the result in `cls.report`, so every test checks the same report.
4. Each `self.assert…(value, floor, message)` is one check. When it fails, the test is marked
   `FAIL` and the message says what dropped, e.g. `macro F1 dropped to 0.180 (floor 0.8)`.
5. The run exits with code 0 if every test passed and 1 otherwise. CI uses that exit code as
   the pass/fail gate.

**Command syntax.** Run from inside `01_basic/` or `02_ml/`, since the tests find the dataset
and contract by relative path (`../data/...`):

```bash
python -m unittest -v <module>[.<Class>[.<test_method>]] [more names ...]
```

| Part | Meaning |
|---|---|
| `python -m unittest` | Starts the `unittest` test runner (`-m` runs a module as a script) |
| `-v` | Verbose: prints each test's name and `ok` / `FAIL` / `ERROR` instead of dots |
| `<module>` | The test file without `.py`, e.g. `test_regression_basic` |
| `.<Class>` | Optional: only the tests in one class, e.g. `.TestRegression` |
| `.<test_method>` | Optional: one test, e.g. `.test_message_api` |

With no name, `python -m unittest` discovers every `test*.py` file in the current directory.

**The tests in each example.**

| Test | `01_basic` | `02_ml` | Fails when |
|---|:-:|:-:|---|
| `TestRegression.test_macro_f1_floor` | ✓ | ✓ | Macro F1 falls below the floor (0.80) |
| `TestRegression.test_every_class_recall_floor` | ✓ | ✓ | Any single queue's recall falls below 0.70 |
| `TestRegression.test_calibration_ceiling` | | ✓ | ECE rises above 0.25 |
| `TestRegression.test_message_api` | ✓ | ✓ | Any golden message fails one of the nine API checks |
| `TestRegression.test_malformed_input_rejected` | ✓ | ✓ | Any malformed input is published or crashes the component |
| `TestRegression.test_deterministic` | ✓ | ✓ | Two runs on the same inputs give different reports |
| `TestApiCheckCatchesComponentBugs` | ✓ | | The API check misses a deliberately buggy message handler |

**Examples — `01_basic/`:**

```bash
cd 01_basic

# Every test
python -m unittest -v test_regression_basic

# One class
python -m unittest -v test_regression_basic.TestRegression

# Only the messaging API checks
python -m unittest -v \
  test_regression_basic.TestRegression.test_message_api \
  test_regression_basic.TestRegression.test_malformed_input_rejected \
  test_regression_basic.TestApiCheckCatchesComponentBugs

# Against the weakened model: must FAIL (F1, recall and message API)
EVAL_MODEL=models/keywords_weakened.json python -m unittest -v test_regression_basic
```

**Examples — `02_ml/`** (train both models first):

```bash
cd 02_ml
python train.py --out models/router.joblib
python train.py --out models/router_weakened.joblib --weaken

# Every test
python -m unittest -v test_regression_ml

# One test
python -m unittest -v test_regression_ml.TestRegression.test_calibration_ceiling

# Against the weakened model: must FAIL (F1, recall and calibration; the API tests still pass)
EVAL_MODEL=models/router_weakened.joblib python -m unittest -v test_regression_ml
```

`EVAL_MODEL` is an environment variable the test files read to choose the model; without it
they test the real model. Running the weakened model is how you show the tests actually catch
a regression and do not pass regardless of what they are given. `run_evidence.sh` runs both
cases and saves the output in `02_ml/logs/`.

## How the examples map to the deliverable

| Deliverable requirement | Where it is shown |
|---|---|
| Harness runs from one command with a model ref and a dataset path | `eval_basic.py` / `eval_ml.py --model … --dataset …` |
| Structured report | `reports/<model>.json` and `reports/<model>.md` |
| Fixed seeds; two runs give identical scores | Scores fingerprint printed each run; `02_ml/logs/run1.log` vs `run2.log`, `determinism.log` |
| Regression test fails on a weakened model and says what dropped | `test_regression_*.py`; `02_ml/logs/test_real_model.log` and `test_weakened_model.log` |
| Golden dataset: curated, provenance, human review, agreement on ≥ 20 | `data/golden.jsonl`, `data/PROVENANCE.md`, `02_ml/review_agreement.py` |
| Classification metrics: precision, recall, F1, confusion matrix | Both reports |
| The component's messaging API is correct (topics, schemas, routing, rejection of bad input) | "Message API" section of both reports; `test_message_api`, `test_malformed_input_rejected` |
| README defines each metric and what good and bad look like | Below |

## Results on the golden set

| Model | Accuracy | Macro F1 | Notes |
|---|---|---|---|
| Keyword rules | 0.833 | 0.840 | 100% API-valid. High precision, but anything without a keyword falls through to `technical` (P = 0.63) |
| Keyword rules, weakened | 0.100 | 0.180 | Falls back to queue `other`, which is not in the contract: 10% API-valid, and those messages reach no subscription. Test fails on F1, recall and the message API |
| TF-IDF + LogReg | 0.850 | 0.854 (95% CI 0.75–0.93) | 100% API-valid. Errors spread across classes; under-confident (ECE 0.18) |
| TF-IDF + LogReg, weakened | 0.633 | 0.628 | Still 100% API-valid, so the API tests pass; test fails on F1, recall and calibration |

**The lesson in these numbers:** the ML model "wins" by 0.014 F1, well inside its
confidence interval. On 60 examples, you *cannot* claim it is better. Either grow the golden
set or compare on the errors themselves. Report intervals, not just point scores.

A second lesson came from building `01_basic/models/keywords.json`: a first draft of the
rules, written while looking at the golden set, scored 0.97; the generic rules shipped here
score 0.84. Rules (or prompts, or
hyperparameters) tuned on the evaluation set measure memory, not skill. Tune on something
else; touch the golden set only to evaluate.

## The messaging API (topics)

The router is one component in a pub/sub system, and its API **is** its messaging contract:

| | Topic | Message | Schema |
|---|---|---|---|
| Consumes | `tickets.incoming` | `TicketReceived` | `data/schemas/ticket-received.v1.schema.json` |
| Publishes | `tickets.routed` | `TicketRouted`, with the routing property `queue`, `message_id` = `ticket_id`, and the input's id as `correlation_id` | `data/schemas/ticket-routed.v1.schema.json` |
| Subscriptions on `tickets.routed` | `billing`, `technical`, `account`, `shipping` | each filters on `queue = '<name>'` | `data/schemas/router.contract.json` |

`data/schemas/router.contract.json` states the whole API in plain JSON, and the harness reads
it together with the two schema files, the kind of JSON Schema files Module 02 asks each team
to commit for its interfaces. `data/schemas/asyncapi.yaml` is optional, extra reading: the same
API in AsyncAPI, the pub/sub counterpart of OpenAPI. The harness does not need it.

**How the harness tests the API (`01_basic/message_api.py`).** The harness never calls the
model directly for this check. It wraps the model in `RouterComponent`, the message handler
that runs in production, and drives it the way the system will:

1. Each golden example is sent **as a `TicketReceived` message** on `tickets.incoming`.
2. Whatever the component publishes goes onto an **in-memory bus** with the same topics and
   subscription filters as Service Bus, so the check is offline and repeatable.
3. Nine checks run on every message:

   | Check | Passes when |
   |---|---|
   | `input_valid` | The message sent is a valid `TicketReceived` (catches a bad golden example) |
   | `one_message` | The component publishes exactly one message |
   | `topic` | It publishes on `tickets.routed` |
   | `body_schema` | The body validates against `TicketRouted` |
   | `content_type` | It is declared `application/json` |
   | `message_id` | `message_id` equals the body's `ticket_id`, so broker duplicate detection works |
   | `correlation_id` | It carries the input message's id, so a request can be traced across components |
   | `routing_property` | The `queue` property matches the body's `queue`; subscribers filter on it |
   | `delivered_once` | The bus delivers it to exactly one subscription, the right one |

4. Seven **malformed input messages** are sent: missing text, wrong types, empty text, an
   unknown channel, an unexpected field, a wrong schema version, and a body that isn't an
   object. The component must reject every one, without publishing and without crashing.
   In production, a rejected message is dead-lettered.

The report gives the **API-valid rate** (messages passing all nine checks), the pass rate of
each check, every violation, and the malformed-input results. The regression tests require
100% on both. `TestApiCheckCatchesComponentBugs` shows why the checks go beyond the body
schema: a component whose model is fine but that drops the correlation id and misspells
the routing property publishes valid bodies, and **no subscriber ever receives them**.

This belongs in the evaluation for two reasons. The *model* can break the API: the weakened
keyword model falls back to a queue called `other`, so 90% of its messages fail the schema
and reach no subscription. And candidate models in Module 07 differ in how reliably they
hold a format, especially LLMs, which can return malformed JSON or invent labels.

**What stays for Modules 08–09.** The in-memory bus checks the contract, not the broker. Real
Service Bus delivery, dead-letter queues, retries and redelivery, authentication, and
network paths are tested against live infrastructure in the Module 08 integration tests and
the Module 09 deployed stack.

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
- **API-valid rate (messaging API)** — the share of golden messages for which the component's
  published message passes all nine API checks. The target is **1.0**: one bad message is
  dead-lettered, or, if its routing property is wrong, silently reaches no worker at all.
  The per-check pass rates tell you *what* broke: `body_schema` points at the model's output,
  while `correlation_id`, `routing_property` or `delivered_once` alone point at the message
  handling code. For an LLM component, `body_schema` is usually the first to move when you
  change the prompt or the model.
- **Malformed-input rejection rate** — the share of deliberately bad input messages the
  component rejects cleanly. The target is **1.0**. Anything less means a bad message on the
  topic can crash the component or be routed as if it were valid.
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
5. Describe your component's messaging API in a contract file like `router.contract.json`:
   the topic it consumes and its schema, the topic it publishes and its schema, the routing
   property, and the subscription filters. Use the JSON Schema files from your Module 02
   contract. Wrap your model in a message handler like `RouterComponent` and pass the file
   with `--contract`.
6. Set the regression floors just under your current scores, and commit the logs.

> The golden-set tickets were generated with Claude (claude-opus-5-5) and the reviewer
> labels are illustrative. See `data/PROVENANCE.md`.
