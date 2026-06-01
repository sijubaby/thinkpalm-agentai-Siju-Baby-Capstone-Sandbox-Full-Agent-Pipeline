"""Infer maritime domain from free-text feature description."""

from __future__ import annotations


def infer_domain_from_description(text: str) -> str:
    lower = text.lower()
    scores = {
        "ais": sum(
            kw in lower
            for kw in (
                "ais",
                "mmsi",
                "position report",
                "stale track",
                "transponder",
                "telemetry",
            )
        ),
        "port-workflow": sum(
            kw in lower
            for kw in (
                "port arrival",
                "port departure",
                "berth",
                "in-port",
                "clearance",
                "arrival at berth",
            )
        ),
        "crew-cert": sum(
            kw in lower
            for kw in (
                "crew",
                "certification",
                "certificate",
                "embarkation",
                "sign-on",
                "stcw",
                "expiry",
                "expired",
            )
        ),
    }
    best = max(scores, key=scores.get)
    if scores[best] == 0:
        return "crew-cert"
    return best
