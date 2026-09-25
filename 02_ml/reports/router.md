# Eval report — tfidf-logreg-router

- Examples: 60 · seed 704 · trained on 600 (data sha `757825ca9c6539e1`)
- Accuracy: **0.850** (95% CI 0.750–0.933)
- Macro F1: **0.854** (95% CI 0.752–0.934)
- Calibration: Brier 0.288 · ECE 0.182 · 28% of predictions below 0.5 confidence
- Schema-valid messages: **100.0%** (TicketRouted v1)
- Scores fingerprint: `aa0fa23474651ed2`

## Per class

| Label | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| account | 0.933 | 0.933 | 0.933 | 15 |
| billing | 0.684 | 0.867 | 0.765 | 15 |
| shipping | 0.857 | 0.800 | 0.828 | 15 |
| technical | 1.000 | 0.800 | 0.889 | 15 |

## Confusion matrix (rows = true, columns = predicted)

| | account | billing | shipping | technical |
|---|---|---|---|---|
| **account** | 14 | 1 | 0 | 0 |
| **billing** | 1 | 13 | 1 | 0 |
| **shipping** | 0 | 3 | 12 | 0 |
| **technical** | 0 | 2 | 1 | 12 |

## Slices (channel)

| Channel | N | Accuracy | Macro F1 |
|---|---|---|---|
| chat | 30 | 0.867 | 0.873 |
| email | 30 | 0.833 | 0.831 |

## Reliability (is confidence honest?)

| Confidence bin | N | Mean confidence | Accuracy |
|---|---|---|---|
| 0.2-0.4 | 5 | 0.355 | 0.600 |
| 0.4-0.6 | 21 | 0.493 | 0.714 |
| 0.6-0.8 | 14 | 0.708 | 0.929 |
| 0.8-1.0 | 20 | 0.903 | 1.000 |

## Message contract

60 of 60 published messages match the schema.


## Errors (9)

| ID | True | Predicted | Confidence | Text |
|---|---|---|---|---|
| g011 | billing | shipping | 0.62 | Is sales tax included in the total at checkout? |
| g015 | billing | account | 0.42 | When will the refund actually hit my bank account? |
| g023 | technical | billing | 0.55 | Search returns no results even for items I know exist. |
| g025 | technical | shipping | 0.52 | The API is returning timeouts for every request. |
| g026 | technical | billing | 0.37 | Dark mode makes some of the text unreadable. |
| g042 | account | billing | 0.45 | Please update my phone number for verification texts. |
| g053 | shipping | billing | 0.50 | My order has been stuck in transit for two weeks. |
| g056 | shipping | billing | 0.32 | The courier left my parcel with a neighbor I don't know. |
| g058 | shipping | billing | 0.48 | I need to send this item back, how do I get a return label? |
