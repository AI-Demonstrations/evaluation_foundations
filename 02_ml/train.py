#!/usr/bin/env python3
"""Train the ticket router: TF-IDF + logistic regression, fully seeded.

Training data is synthesized from templates (seeded), so it is deliberately *not* the
golden set — the golden set is only ever used for evaluation.

    python train.py --out models/router.joblib               # the real model
    python train.py --out models/router_weakened.joblib --weaken   # for the regression test
"""

import argparse
import hashlib
import json
import os
import random

import joblib
import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

SEED = 704

TEMPLATES = {
    "billing": [
        "I was {charged} {amount} for {thing}", "please refund the {amount} you took for {thing}",
        "my {doc} for {thing} looks wrong", "the {doc} doesn't match what I paid",
        "my {method} was declined for {thing}", "how do I update my {method}",
        "why was I {charged} again this month", "the discount on {thing} was not applied",
        "can I get my money back for {thing}", "I need a {doc} for {thing}",
        "question about the cost of {thing}", "you {charged} me after I cancelled {thing}",
    ],
    "technical": [
        "the {surface} {fails} when I {action}", "I get an error when I {action}",
        "{surface} is {slow} since the last update", "the {surface} {fails} on my {device}",
        "{feature} is broken on the {surface}", "{feature} does nothing when I {action}",
        "I see a {glitch} when I {action}", "the {surface} shows a {glitch}",
        "{feature} stopped working on my {device}", "cannot {action}, the {surface} {fails}",
    ],
    "account": [
        "I can't {signin} to my account", "reset my {cred} please", "how do I change my {field}",
        "I'm locked out of my account", "someone accessed my account without permission",
        "please close my account", "the {cred} reset link never arrives",
        "update the {field} on my profile", "I need to {signin} but my {cred} fails",
        "my account was {state}", "add another user to my account", "export my account data",
    ],
    "shipping": [
        "where is my {parcel}", "my {parcel} hasn't arrived", "the {parcel} arrived {damage}",
        "tracking for my {parcel} is not updating", "can you change the {addr} for my {parcel}",
        "my {parcel} was delivered to the wrong {addr}", "how long does delivery take to {place}",
        "do you deliver to {place}", "I got the wrong item in my {parcel}",
        "my {parcel} is late", "I want to return my {parcel}", "is express shipping available to {place}",
    ],
}
SLOTS = {
    "charged": ["charged", "billed", "overcharged", "double charged"],
    "amount": ["$20", "$9.99", "twice", "the full amount", "an extra fee"],
    "thing": ["my plan", "my subscription", "last month", "my order", "the upgrade", "the annual plan"],
    "doc": ["invoice", "receipt", "bill", "statement"],
    "method": ["credit card", "card", "payment method", "debit card"],
    "surface": ["app", "website", "page", "dashboard", "mobile app", "desktop client"],
    "fails": ["crashes", "freezes", "hangs", "closes", "won't load"],
    "action": ["open settings", "upload a file", "save", "export", "log out", "refresh"],
    "slow": ["very slow", "lagging", "timing out", "unresponsive"],
    "device": ["phone", "laptop", "tablet", "Android", "iPhone", "Chrome"],
    "feature": ["search", "sync", "notifications", "export", "the upload button", "video"],
    "glitch": ["blank screen", "500 error", "spinner that never stops", "corrupted file"],
    "signin": ["log in", "sign in", "log on"],
    "cred": ["password", "two-factor code", "PIN", "security question"],
    "field": ["email address", "username", "phone number", "name", "profile photo"],
    "state": ["suspended", "disabled", "hacked", "deleted by mistake"],
    "parcel": ["package", "order", "shipment", "delivery", "box"],
    "damage": ["damaged", "crushed", "open", "wet", "broken"],
    "addr": ["address", "house", "apartment", "location"],
    "place": ["Canada", "Hawaii", "the UK", "Mexico", "a PO box"],
}


def synthesize(n_per_class, rng):
    rows = []
    for label, templates in TEMPLATES.items():
        for _ in range(n_per_class):
            t = rng.choice(templates)
            rows.append((t.format(**{k: rng.choice(v) for k, v in SLOTS.items()}), label))
    rng.shuffle(rows)
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default="models/router.joblib")
    ap.add_argument("--n-per-class", type=int, default=150)
    ap.add_argument("--weaken", action="store_true",
                    help="deliberately cripple the model (3 examples/class, heavy regularization)")
    args = ap.parse_args()

    rng = random.Random(SEED)
    n = 3 if args.weaken else args.n_per_class
    rows = synthesize(n, rng)
    texts, labels = zip(*rows)

    model = Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, min_df=1)),
        ("clf", LogisticRegression(C=0.05 if args.weaken else 5.0, max_iter=2000, random_state=SEED)),
    ])
    model.fit(texts, labels)

    data_hash = hashlib.sha256(json.dumps(rows).encode()).hexdigest()[:16]
    meta = {"name": "tfidf-logreg-router" + ("-WEAKENED" if args.weaken else ""),
            "seed": SEED, "n_train": len(rows), "train_data_sha": data_hash,
            "sklearn": sklearn.__version__}
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    joblib.dump({"model": model, "meta": meta}, args.out)
    print(f"trained {meta['name']} on {len(rows)} examples (data sha {data_hash}) -> {args.out}")


if __name__ == "__main__":
    main()
