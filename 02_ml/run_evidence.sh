#!/usr/bin/env bash
# Produce the committed evidence the Module 5 deliverable asks for, in logs/:
#   two identical harness runs, regression-test pass (real) and fail (weakened),
#   and reviewer agreement. Instructors grade from these files, not by running code.
set -u
cd "$(dirname "$0")"
DATA=../data/golden.jsonl
mkdir -p logs

python3 train.py --out models/router.joblib
python3 train.py --out models/router_weakened.joblib --weaken

python3 eval_ml.py --model models/router.joblib --dataset "$DATA" 2>&1 | tee logs/run1.log
python3 eval_ml.py --model models/router.joblib --dataset "$DATA" 2>&1 | tee logs/run2.log
if diff -q <(grep fingerprint= logs/run1.log) <(grep fingerprint= logs/run2.log) >/dev/null; then
  echo "DETERMINISM: run1 and run2 fingerprints match" | tee logs/determinism.log
else
  echo "DETERMINISM: run1 and run2 DIFFER" | tee logs/determinism.log
fi

python3 eval_ml.py --model models/router_weakened.joblib --dataset "$DATA" > logs/run_weakened.log 2>&1
# tracebacks name files by absolute path; strip this directory so logs don't carry your machine's paths
python3 -m unittest -v test_regression_ml 2>&1 | sed "s|$PWD/||g" > logs/test_real_model.log
echo "real model tests exit code: ${PIPESTATUS[0]}" | tee -a logs/test_real_model.log
EVAL_MODEL=models/router_weakened.joblib python3 -m unittest -v test_regression_ml 2>&1 | sed "s|$PWD/||g" > logs/test_weakened_model.log
echo "weakened model tests exit code: ${PIPESTATUS[0]} (non-zero expected)" | tee -a logs/test_weakened_model.log

python3 review_agreement.py --dataset "$DATA" | tee logs/review_agreement.log
