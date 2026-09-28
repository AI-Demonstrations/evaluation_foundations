# Eval report — keyword-router-v1

- Examples: 60
- Accuracy: **0.833**
- Macro F1: **0.840**
- Message API: **100.0%** of messages pass every check (schema-valid 100.0%; malformed inputs rejected 100.0%)
- Scores fingerprint: `03258bd96a3409f7`

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

## Message API

Consumes `tickets.incoming`, publishes `tickets.routed`. 60 of 60 golden messages pass every check; 7 of 7 malformed inputs rejected.

| Check | Pass rate |
|---|---|
| input_valid | 100.0% |
| one_message | 100.0% |
| topic | 100.0% |
| body_schema | 100.0% |
| content_type | 100.0% |
| message_id | 100.0% |
| correlation_id | 100.0% |
| routing_property | 100.0% |
| delivered_once | 100.0% |

| Malformed input | Rejected | Detail |
|---|---|---|
| missing_text | yes | invalid input: $: missing required field 'text' |
| text_not_string | yes | invalid input: $.text: expected string, got int |
| empty_text | yes | invalid input: $.text: shorter than 1 |
| unknown_channel | yes | invalid input: $.channel: 'fax' not one of ['email', 'chat'] |
| unexpected_field | yes | invalid input: $: unexpected field 'priority' |
| wrong_version | yes | invalid input: $.schema_version: must equal '1.0', got '2.0' |
| not_an_object | yes | invalid input: $: expected object, got str |

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
