# Eval report — tfidf-logreg-router-WEAKENED

- Examples: 60 · seed 704 · trained on 12 (data sha `44521df9c874ef43`)
- Accuracy: **0.633** (95% CI 0.516–0.750)
- Macro F1: **0.628** (95% CI 0.503–0.745)
- Calibration: Brier 0.746 · ECE 0.380 · 100% of predictions below 0.5 confidence
- Schema-valid messages: **100.0%** (TicketRouted v1)
- Scores fingerprint: `35dc2750afd78003`

## Per class

| Label | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| account | 0.625 | 0.667 | 0.645 | 15 |
| billing | 0.700 | 0.467 | 0.560 | 15 |
| shipping | 0.562 | 0.600 | 0.581 | 15 |
| technical | 0.667 | 0.800 | 0.727 | 15 |

## Confusion matrix (rows = true, columns = predicted)

| | account | billing | shipping | technical |
|---|---|---|---|---|
| **account** | 10 | 1 | 3 | 1 |
| **billing** | 2 | 7 | 3 | 3 |
| **shipping** | 3 | 1 | 9 | 2 |
| **technical** | 1 | 1 | 1 | 12 |

## Slices (channel)

| Channel | N | Accuracy | Macro F1 |
|---|---|---|---|
| chat | 30 | 0.633 | 0.619 |
| email | 30 | 0.633 | 0.633 |

## Reliability (is confidence honest?)

| Confidence bin | N | Mean confidence | Accuracy |
|---|---|---|---|
| 0.2-0.4 | 60 | 0.253 | 0.633 |

## Message contract

60 of 60 published messages match the schema.


## Errors (22)

| ID | True | Predicted | Confidence | Text |
|---|---|---|---|---|
| g003 | billing | account | 0.25 | My invoice shows a price higher than what was advertised. |
| g006 | billing | technical | 0.25 | The promo code didn't apply and I paid full price. |
| g010 | billing | shipping | 0.25 | You billed me after I cancelled my membership. |
| g011 | billing | technical | 0.25 | Is sales tax included in the total at checkout? |
| g012 | billing | shipping | 0.25 | My payment went through but the order still says unpaid. |
| g013 | billing | shipping | 0.25 | Can I split the payment across two cards? |
| g014 | billing | technical | 0.25 | I was promised a student discount but it never showed up. |
| g015 | billing | account | 0.25 | When will the refund actually hit my bank account? |
| g020 | technical | account | 0.25 | Video playback stutters on my phone but works on my laptop. |
| g021 | technical | shipping | 0.25 | The export to CSV button does nothing when I click it. |
| g023 | technical | billing | 0.25 | Search returns no results even for items I know exist. |
| g031 | account | shipping | 0.25 | I forgot my password and the reset email never arrives. |
| g037 | account | technical | 0.25 | Two-factor codes aren't being accepted when I sign in. |
| g040 | account | billing | 0.25 | How do I merge two accounts I accidentally created? |
| g041 | account | shipping | 0.25 | I can't sign in with Google anymore. |
| g044 | account | shipping | 0.25 | My profile picture keeps reverting to the old one. |
| g046 | shipping | account | 0.25 | My package says delivered but it's not at my door. |
| g047 | shipping | technical | 0.25 | When will my order ship? |
| g050 | shipping | technical | 0.26 | The box arrived damaged and the item inside is broken. |
| g055 | shipping | account | 0.25 | Part of my order is missing from the box. |
| g058 | shipping | billing | 0.25 | I need to send this item back, how do I get a return label? |
| g060 | shipping | account | 0.25 | Can I pick up my order at a store instead of having it delivered? |
