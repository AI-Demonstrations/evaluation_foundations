# Eval report — keyword-router-v1-WEAKENED

- Examples: 60
- Accuracy: **0.100**
- Macro F1: **0.180**
- Schema-valid messages: **10.0%** (TicketRouted v1)
- Scores fingerprint: `12930b508f0d16d6`

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

## Message contract

6 of 60 published messages match the schema.

- `g001`: $.queue: 'other' not one of ['billing', 'technical', 'account', 'shipping']
- `g003`: $.queue: 'other' not one of ['billing', 'technical', 'account', 'shipping']
- `g004`: $.queue: 'other' not one of ['billing', 'technical', 'account', 'shipping']
- `g005`: $.queue: 'other' not one of ['billing', 'technical', 'account', 'shipping']
- `g006`: $.queue: 'other' not one of ['billing', 'technical', 'account', 'shipping']
- `g007`: $.queue: 'other' not one of ['billing', 'technical', 'account', 'shipping']
- `g008`: $.queue: 'other' not one of ['billing', 'technical', 'account', 'shipping']
- `g009`: $.queue: 'other' not one of ['billing', 'technical', 'account', 'shipping']
- `g010`: $.queue: 'other' not one of ['billing', 'technical', 'account', 'shipping']
- `g011`: $.queue: 'other' not one of ['billing', 'technical', 'account', 'shipping']
- `g012`: $.queue: 'other' not one of ['billing', 'technical', 'account', 'shipping']
- `g013`: $.queue: 'other' not one of ['billing', 'technical', 'account', 'shipping']
- `g014`: $.queue: 'other' not one of ['billing', 'technical', 'account', 'shipping']
- `g018`: $.queue: 'other' not one of ['billing', 'technical', 'account', 'shipping']
- `g019`: $.queue: 'other' not one of ['billing', 'technical', 'account', 'shipping']
- `g020`: $.queue: 'other' not one of ['billing', 'technical', 'account', 'shipping']
- `g021`: $.queue: 'other' not one of ['billing', 'technical', 'account', 'shipping']
- `g022`: $.queue: 'other' not one of ['billing', 'technical', 'account', 'shipping']
- `g023`: $.queue: 'other' not one of ['billing', 'technical', 'account', 'shipping']
- `g024`: $.queue: 'other' not one of ['billing', 'technical', 'account', 'shipping']

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
