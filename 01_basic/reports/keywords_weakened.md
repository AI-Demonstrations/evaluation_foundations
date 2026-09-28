# Eval report — keyword-router-v1-WEAKENED

- Examples: 60
- Accuracy: **0.100**
- Macro F1: **0.180**
- Message API: **10.0%** of messages pass every check (schema-valid 10.0%; malformed inputs rejected 100.0%)
- Scores fingerprint: `81586204874e91de`

## Per class

| Label | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| account | 1.000 | 0.067 | 0.125 | 15 |
| billing | 1.000 | 0.133 | 0.235 | 15 |
| shipping | 1.000 | 0.067 | 0.125 | 15 |
| technical | 1.000 | 0.133 | 0.235 | 15 |

## Confusion matrix (rows = true, columns = predicted)

| | account | billing | shipping | technical | (off-contract) |
|---|---|---|---|---|---|
| **account** | 1 | 0 | 0 | 0 | 14 |
| **billing** | 0 | 2 | 0 | 0 | 13 |
| **shipping** | 0 | 0 | 1 | 0 | 14 |
| **technical** | 0 | 0 | 0 | 2 | 13 |

## Message API

Consumes `tickets.incoming`, publishes `tickets.routed`. 6 of 60 golden messages pass every check; 7 of 7 malformed inputs rejected.

| Check | Pass rate |
|---|---|
| input_valid | 100.0% |
| one_message | 100.0% |
| topic | 100.0% |
| body_schema | 10.0% |
| content_type | 100.0% |
| message_id | 100.0% |
| correlation_id | 100.0% |
| routing_property | 100.0% |
| delivered_once | 10.0% |

| Malformed input | Rejected | Detail |
|---|---|---|
| missing_text | yes | invalid input: $: missing required field 'text' |
| text_not_string | yes | invalid input: $.text: expected string, got int |
| empty_text | yes | invalid input: $.text: shorter than 1 |
| unknown_channel | yes | invalid input: $.channel: 'fax' not one of ['email', 'chat'] |
| unexpected_field | yes | invalid input: $: unexpected field 'priority' |
| wrong_version | yes | invalid input: $.schema_version: must equal '1.0', got '2.0' |
| not_an_object | yes | invalid input: $: expected object, got str |

Violations (54; first 20):

- `g001`: body_schema: $.queue: 'other' not one of ['billing', 'technical', 'account', 'shipping']; delivered_once: delivered to no subscription
- `g003`: body_schema: $.queue: 'other' not one of ['billing', 'technical', 'account', 'shipping']; delivered_once: delivered to no subscription
- `g004`: body_schema: $.queue: 'other' not one of ['billing', 'technical', 'account', 'shipping']; delivered_once: delivered to no subscription
- `g005`: body_schema: $.queue: 'other' not one of ['billing', 'technical', 'account', 'shipping']; delivered_once: delivered to no subscription
- `g006`: body_schema: $.queue: 'other' not one of ['billing', 'technical', 'account', 'shipping']; delivered_once: delivered to no subscription
- `g007`: body_schema: $.queue: 'other' not one of ['billing', 'technical', 'account', 'shipping']; delivered_once: delivered to no subscription
- `g008`: body_schema: $.queue: 'other' not one of ['billing', 'technical', 'account', 'shipping']; delivered_once: delivered to no subscription
- `g009`: body_schema: $.queue: 'other' not one of ['billing', 'technical', 'account', 'shipping']; delivered_once: delivered to no subscription
- `g010`: body_schema: $.queue: 'other' not one of ['billing', 'technical', 'account', 'shipping']; delivered_once: delivered to no subscription
- `g011`: body_schema: $.queue: 'other' not one of ['billing', 'technical', 'account', 'shipping']; delivered_once: delivered to no subscription
- `g012`: body_schema: $.queue: 'other' not one of ['billing', 'technical', 'account', 'shipping']; delivered_once: delivered to no subscription
- `g013`: body_schema: $.queue: 'other' not one of ['billing', 'technical', 'account', 'shipping']; delivered_once: delivered to no subscription
- `g014`: body_schema: $.queue: 'other' not one of ['billing', 'technical', 'account', 'shipping']; delivered_once: delivered to no subscription
- `g018`: body_schema: $.queue: 'other' not one of ['billing', 'technical', 'account', 'shipping']; delivered_once: delivered to no subscription
- `g019`: body_schema: $.queue: 'other' not one of ['billing', 'technical', 'account', 'shipping']; delivered_once: delivered to no subscription
- `g020`: body_schema: $.queue: 'other' not one of ['billing', 'technical', 'account', 'shipping']; delivered_once: delivered to no subscription
- `g021`: body_schema: $.queue: 'other' not one of ['billing', 'technical', 'account', 'shipping']; delivered_once: delivered to no subscription
- `g022`: body_schema: $.queue: 'other' not one of ['billing', 'technical', 'account', 'shipping']; delivered_once: delivered to no subscription
- `g023`: body_schema: $.queue: 'other' not one of ['billing', 'technical', 'account', 'shipping']; delivered_once: delivered to no subscription
- `g024`: body_schema: $.queue: 'other' not one of ['billing', 'technical', 'account', 'shipping']; delivered_once: delivered to no subscription

## Errors (54)

| ID | True | Predicted | Text |
|---|---|---|---|
| g001 | billing | other | I was charged twice for my subscription this month. |
| g003 | billing | other | My invoice shows a price higher than what was advertised. |
| g004 | billing | other | Why did my card get declined when I tried to pay? |
| g005 | billing | other | Please update the credit card on file for my plan. |
| g006 | billing | other | The promo code didn't apply and I paid full price. |
| g007 | billing | other | I need a copy of my receipt for my expense report. |
| g008 | billing | other | There's a charge from you I don't recognize on my statement. |
| g009 | billing | other | How do I switch from monthly to annual billing? |
| g010 | billing | other | You billed me after I cancelled my membership. |
| g011 | billing | other | Is sales tax included in the total at checkout? |
| g012 | billing | other | My payment went through but the order still says unpaid. |
| g013 | billing | other | Can I split the payment across two cards? |
| g014 | billing | other | I was promised a student discount but it never showed up. |
| g018 | technical | other | The page just spins forever and never loads. |
| g019 | technical | other | Notifications stopped working after the latest update. |
| g020 | technical | other | Video playback stutters on my phone but works on my laptop. |
| g021 | technical | other | The export to CSV button does nothing when I click it. |
| g022 | technical | other | Sync between my tablet and desktop has been broken since yesterday. |
| g023 | technical | other | Search returns no results even for items I know exist. |
| g024 | technical | other | I get a blank white screen after logging in on Safari. |
| g025 | technical | other | The API is returning timeouts for every request. |
| g026 | technical | other | Dark mode makes some of the text unreadable. |
| g027 | technical | other | The mobile app won't install on my Android phone. |
| g028 | technical | other | My uploaded files show as corrupted when I download them. |
| g029 | technical | other | The checkout page freezes when I click the pay button. |
| g030 | technical | other | Bluetooth pairing with the device keeps failing. |
| g032 | account | other | How do I change the email address on my profile? |
| g033 | account | other | Someone else logged into my account from another country. |
| g034 | account | other | Please delete my account and all my data. |
| g035 | account | other | I'm locked out after too many login attempts. |
| g036 | account | other | Can I add a second user to my household account? |
| g037 | account | other | Two-factor codes aren't being accepted when I sign in. |
| g038 | account | other | I want to change my username. |
| g039 | account | other | My account was suspended and I don't know why. |
| g040 | account | other | How do I merge two accounts I accidentally created? |
| g041 | account | other | I can't sign in with Google anymore. |
| g042 | account | other | Please update my phone number for verification texts. |
| g043 | account | other | I'd like to download a copy of all my personal data. |
| g044 | account | other | My profile picture keeps reverting to the old one. |
| g045 | account | other | How do I transfer ownership of the team account to a coworker? |
| g047 | shipping | other | When will my order ship? |
| g048 | shipping | other | The tracking number you sent doesn't work. |
| g049 | shipping | other | Can I change the delivery address for an order I just placed? |
| g050 | shipping | other | The box arrived damaged and the item inside is broken. |
| g051 | shipping | other | I received the wrong item in my shipment. |
| g052 | shipping | other | Do you ship to Canada? |
| g053 | shipping | other | My order has been stuck in transit for two weeks. |
| g054 | shipping | other | Can I upgrade to overnight delivery? |
| g055 | shipping | other | Part of my order is missing from the box. |
| g056 | shipping | other | The courier left my parcel with a neighbor I don't know. |
| g057 | shipping | other | How much is shipping to Alaska? |
| g058 | shipping | other | I need to send this item back, how do I get a return label? |
| g059 | shipping | other | The delivery window keeps getting pushed back. |
| g060 | shipping | other | Can I pick up my order at a store instead of having it delivered? |
