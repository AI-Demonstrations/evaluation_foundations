"""The router's messaging API, and an offline check that the component honors it.

In production the router is a component on a topic-based system: it consumes
TicketReceived messages from `tickets.incoming` and publishes TicketRouted messages
to `tickets.routed`, where each queue's worker has a filtered subscription. Its API
*is* that contract — `data/schemas/router.contract.json` plus the two message schemas.

This module lets the Module 05 harness drive the component exactly as the system will:
by sending it messages and inspecting what it publishes. An in-memory bus stands in for
Service Bus (same topic + subscription-filter semantics), so the check stays offline and
gives identical results on every run. Live delivery is still tested in Module 08.

API checks, per golden example:
  input_valid            the message we send is a valid TicketReceived (checks the harness/dataset)
  one_message            the component publishes exactly `messages_per_input` messages
  topic                  ... on the contract's publish topic
  body_schema            ... with a body that validates against TicketRouted
  content_type           ... declared as application/json
  message_id             ... with message_id = body.ticket_id (enables duplicate detection)
  correlation_id         ... carrying the input message's id (traceability)
  routing_property       ... with the routing property equal to the body's queue
  delivered_once         ... and the bus delivers it to exactly one subscription: the right one
Robustness: every malformed input message is rejected (dead-lettered) — not published,
not a crash.
"""

import json
import os

from schema_check import validate

HERE = os.path.dirname(os.path.abspath(__file__))
SCHEMA_DIR = os.path.join(HERE, "..", "data", "schemas")
DEFAULT_CONTRACT = os.path.join(SCHEMA_DIR, "router.contract.json")
HUMAN_REVIEW_BELOW = 0.5

CHECKS = ["input_valid", "one_message", "topic", "body_schema", "content_type",
          "message_id", "correlation_id", "routing_property", "delivered_once"]

# Messages a real topic will eventually deliver. The component must reject each one.
MALFORMED_INPUTS = [
    ("missing_text", {"schema_version": "1.0", "ticket_id": "x1", "channel": "email"}),
    ("text_not_string", {"schema_version": "1.0", "ticket_id": "x2", "text": 123, "channel": "chat"}),
    ("empty_text", {"schema_version": "1.0", "ticket_id": "x3", "text": "", "channel": "chat"}),
    ("unknown_channel", {"schema_version": "1.0", "ticket_id": "x4", "text": "hi", "channel": "fax"}),
    ("unexpected_field", {"schema_version": "1.0", "ticket_id": "x5", "text": "hi", "channel": "chat",
                          "priority": "urgent"}),
    ("wrong_version", {"schema_version": "2.0", "ticket_id": "x6", "text": "hi", "channel": "chat"}),
    ("not_an_object", "route this please"),
]


def load_contract(path=DEFAULT_CONTRACT):
    with open(path) as f:
        c = json.load(f)
    base = os.path.dirname(os.path.abspath(path))
    for side in ("consumes", "publishes"):
        with open(os.path.join(base, c[side]["schema"])) as f:
            c[side]["schema_doc"] = json.load(f)
    return c


def envelope(topic, body, message_id, correlation_id=None, content_type="application/json", properties=None):
    """A message as a broker carries it: the body plus the broker-level properties."""
    return {"topic": topic, "body": body, "message_id": message_id, "correlation_id": correlation_id,
            "content_type": content_type, "properties": dict(properties or {})}


def to_message(row, label, confidence):
    """The TicketRouted body the router publishes."""
    return {"schema_version": "1.0", "ticket_id": row["id"], "queue": label,
            "confidence": confidence, "needs_human": confidence < HUMAN_REVIEW_BELOW}


class InMemoryBus:
    """Topics with filtered subscriptions — the Service Bus behavior the check needs."""

    def __init__(self, contract):
        self.subscriptions = contract["subscriptions"]
        self.delivered = {t: {s: [] for s in subs} for t, subs in self.subscriptions.items()}

    def publish(self, env):
        hits = []
        for name, rule in self.subscriptions.get(env["topic"], {}).items():
            if all(env["properties"].get(k) == v for k, v in rule.items()):
                self.delivered[env["topic"]][name].append(env)
                hits.append(name)
        return hits


class RouterComponent:
    """The component as deployed: a message handler around any model with route(text) -> (label, conf).

    handle() returns (published envelopes, rejection reason or None). A rejected message
    would be dead-lettered by the broker.
    """

    def __init__(self, route_fn, contract):
        self.route = route_fn
        self.c = contract

    def handle(self, env):
        errs = validate(env["body"], self.c["consumes"]["schema_doc"])
        if errs:
            return [], "invalid input: " + "; ".join(errs)
        body = env["body"]
        label, conf = self.route(body["text"])
        out = to_message({"id": body["ticket_id"]}, label, conf)
        pub = self.c["publishes"]
        return [envelope(pub["topic"], out, message_id=out[pub["message_id_field"]],
                         correlation_id=env["message_id"], content_type=pub["content_type"],
                         properties={pub["routing_property"]: out["queue"]})], None


def input_envelope(row, contract):
    body = {"schema_version": "1.0", "ticket_id": row["id"], "text": row["text"],
            "channel": row.get("channel", "email")}
    return envelope(contract["consumes"]["topic"], body, message_id="in-" + row["id"])


def api_check(component, rows, contract):
    pub = contract["publishes"]
    passed = {k: 0 for k in CHECKS}
    violations = []
    all_ok = 0
    for row in rows:
        bus = InMemoryBus(contract)
        env = input_envelope(row, contract)
        failed = []
        if validate(env["body"], contract["consumes"]["schema_doc"]):
            failed.append("input_valid: golden example is not a valid TicketReceived")
        try:
            outs, rejected = component.handle(env)
        except Exception as e:                            # a crash is an API failure, not a harness failure
            outs, rejected = [], f"component raised {type(e).__name__}: {e}"
        results = {"input_valid": not failed}
        results["one_message"] = len(outs) == pub["messages_per_input"]
        if not results["one_message"]:
            failed.append(f"one_message: published {len(outs)}" + (f" ({rejected})" if rejected else ""))
        o = outs[0] if outs else None
        body = o["body"] if o else None
        body_errs = validate(body, pub["schema_doc"]) if o else ["nothing published"]
        results["topic"] = bool(o) and o["topic"] == pub["topic"]
        results["body_schema"] = not body_errs
        results["content_type"] = bool(o) and o["content_type"] == pub["content_type"]
        results["message_id"] = bool(o) and isinstance(body, dict) and o["message_id"] == body.get(pub["message_id_field"])
        results["correlation_id"] = bool(o) and o["correlation_id"] == env["message_id"]
        results["routing_property"] = (bool(o) and isinstance(body, dict)
                                       and o["properties"].get(pub["routing_property"]) == body.get("queue"))
        hits = bus.publish(o) if o else []
        results["delivered_once"] = bool(o) and isinstance(body, dict) and hits == [body.get("queue")]
        for k in CHECKS[1:]:
            if not results[k] and k != "one_message":
                detail = {"topic": lambda: o["topic"] if o else None,
                          "body_schema": lambda: "; ".join(body_errs),
                          "content_type": lambda: o["content_type"] if o else None,
                          "message_id": lambda: o["message_id"] if o else None,
                          "correlation_id": lambda: o["correlation_id"] if o else None,
                          "routing_property": lambda: o["properties"] if o else None,
                          "delivered_once": lambda: f"delivered to {hits or 'no subscription'}"}[k]()
                failed.append(f"{k}: {detail}")
        for k, v in results.items():
            passed[k] += bool(v)
        if all(results.values()):
            all_ok += 1
        else:
            violations.append({"ticket_id": row["id"], "failed": failed})

    robustness = []
    for name, bad in MALFORMED_INPUTS:
        env = envelope(contract["consumes"]["topic"], bad, message_id=f"bad-{name}")
        try:
            outs, rejected = component.handle(env)
            ok = not outs and bool(rejected)
            robustness.append({"case": name, "rejected": ok, "detail": rejected or f"published {len(outs)}"})
        except Exception as e:
            robustness.append({"case": name, "rejected": False, "detail": f"crashed: {type(e).__name__}"})

    n = len(rows)
    return {
        "contract": contract["component"],
        "consumes": contract["consumes"]["topic"], "publishes": pub["topic"],
        "n_messages": n,
        "api_valid_rate": round(all_ok / n, 4),
        "schema_valid_rate": round(passed["body_schema"] / n, 4),
        "checks": {k: round(passed[k] / n, 4) for k in CHECKS},
        "malformed_rejected_rate": round(sum(r["rejected"] for r in robustness) / len(robustness), 4),
        "robustness": robustness,
        "violations": violations,
    }


def api_markdown(api):
    L = ["## Message API", "",
         f"Consumes `{api['consumes']}`, publishes `{api['publishes']}`. "
         f"{round(api['api_valid_rate'] * api['n_messages'])} of {api['n_messages']} golden messages pass every check; "
         f"{sum(r['rejected'] for r in api['robustness'])} of {len(api['robustness'])} malformed inputs rejected.", "",
         "| Check | Pass rate |", "|---|---|"]
    L += [f"| {k} | {v:.1%} |" for k, v in api["checks"].items()]
    L += ["", "| Malformed input | Rejected | Detail |", "|---|---|---|"]
    L += [f"| {r['case']} | {'yes' if r['rejected'] else '**NO**'} | {r['detail'][:120]} |" for r in api["robustness"]]
    if api["violations"]:
        L += ["", f"Violations ({len(api['violations'])}; first 20):", ""]
        L += [f"- `{v['ticket_id']}`: " + "; ".join(v["failed"]) for v in api["violations"][:20]]
    return L
