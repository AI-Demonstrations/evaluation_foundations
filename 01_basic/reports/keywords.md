# Eval report — keyword-router-v1

- Examples: 60
- Accuracy: **0.833**
- Macro F1: **0.840**
- Schema-valid messages: **100.0%** (TicketRouted v1)
- Scores fingerprint: `7529fdde4b7da91d`

## Per class

| Label | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| account | 1.000 | 0.733 | 0.846 | 15 |
| billing | 1.000 | 0.800 | 0.889 | 15 |
| shipping | 0.923 | 0.800 | 0.857 | 15 |
| technical | 0.625 | 1.000 | 0.769 | 15 |

## Confusion matrix (rows = true, columns = predicted)

| | account | billing | shipping | technical |
|---|---|---|---|---|
| **account** | 11 | 0 | 0 | 4 |
| **billing** | 0 | 12 | 1 | 2 |
| **shipping** | 0 | 0 | 12 | 3 |
| **technical** | 0 | 0 | 0 | 15 |

## Message contract

60 of 60 published messages match the schema.


## Errors (10)

| ID | True | Predicted | Text |
|---|---|---|---|
| g007 | billing | technical | I need a copy of my receipt for my expense report. |
| g010 | billing | shipping | You billed me after I cancelled my membership. |
| g011 | billing | technical | Is sales tax included in the total at checkout? |
| g037 | account | technical | Two-factor codes aren't being accepted when I sign in. |
| g041 | account | technical | I can't sign in with Google anymore. |
| g042 | account | technical | Please update my phone number for verification texts. |
| g043 | account | technical | I'd like to download a copy of all my personal data. |
| g050 | shipping | technical | The box arrived damaged and the item inside is broken. |
| g056 | shipping | technical | The courier left my parcel with a neighbor I don't know. |
| g058 | shipping | technical | I need to send this item back, how do I get a return label? |
