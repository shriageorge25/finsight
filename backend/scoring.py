"""Health score and warnings. Formula-based, deterministic (no LLM)."""
import forecast as fc
from analytics_bridge import find_inconsistencies

CONCENTRATION_LIMIT = 0.30   # top customer above this share of unpaid is penalised
POINTS_PER_HIGH_ISSUE = 2    # each high-severity inconsistency costs this many points
RUNWAY_CAP_MONTHS = 2        # runway beyond this gets no extra credit


def unpaid_invoices(invoices):
    return [i for i in invoices if not i.get("paid_date")]


def overdue_invoices(invoices, as_of):
    """Unpaid and past due. ISO date strings compare correctly as text."""
    return [i for i in unpaid_invoices(invoices) if i["due_date"] < as_of]


def compute_summary(business, transactions, invoices, obligations, forecast):
    as_of = business["as_of_date"]
    balance = fc.current_balance(business, transactions)

    unpaid = unpaid_invoices(invoices)
    unpaid_total = sum(i["amount"] for i in unpaid)
    overdue_total = sum(i["amount"] for i in overdue_invoices(invoices, as_of))
    overdue_share = overdue_total / unpaid_total if unpaid_total else 0.0

    by_customer = {}
    for i in unpaid:
        by_customer[i["customer"]] = by_customer.get(i["customer"], 0) + i["amount"]
    top_share = max(by_customer.values()) / unpaid_total if unpaid_total else 0.0

    issues = find_inconsistencies(transactions, invoices)
    n_high = sum(1 for x in issues if x["severity"] == "high")

    monthly_out = sum(r["amount"] for r in fc.infer_recurring(transactions))
    runway = balance / monthly_out if monthly_out > 0 else RUNWAY_CAP_MONTHS
    max_neg = max(forecast["negative_probability"])

    raw = {
        "liquidity": 40 * (1 - max_neg),
        "collections": 25 * (1 - overdue_share),
        "concentration": 15 * (1 - min(1, max(0, (top_share - CONCENTRATION_LIMIT) / (1 - CONCENTRATION_LIMIT)))),
        "data_integrity": max(0, 10 - POINTS_PER_HIGH_ISSUE * n_high),
        "buffer": 10 * max(0, min(runway / RUNWAY_CAP_MONTHS, 1)),
    }
    components = {k: int(round(v)) for k, v in raw.items()}
    score = sum(components.values())  # health_score is exactly the sum of the components
    status = "healthy" if score >= 70 else "watch" if score >= 45 else "at_risk"

    warnings = []
    risk_day = fc.first_risk_day(forecast)
    if risk_day:
        idx = forecast["dates"].index(risk_day)
        p = forecast["negative_probability"][idx]
        warnings.append({
            "type": "liquidity_gap",
            "severity": "high" if p >= 0.5 else "medium",
            "week": risk_day,
            "reason": f"Cash has a {p:.0%} chance of going negative on {risk_day}.",
        })
    if overdue_total > 0:
        warnings.append({
            "type": "overdue_collections",
            "severity": "high" if overdue_share >= 0.5 else "medium",
            "week": None,
            "reason": f"Rs. {overdue_total:,.0f} of unpaid invoices are overdue ({overdue_share:.0%} of everything unpaid).",
        })
    if top_share > CONCENTRATION_LIMIT:
        top_name = max(by_customer, key=by_customer.get)
        warnings.append({
            "type": "customer_concentration",
            "severity": "high" if top_share >= 0.5 else "medium",
            "week": None,
            "reason": f"{top_name} accounts for {top_share:.0%} of unpaid invoices.",
        })
    if n_high > 0:
        warnings.append({
            "type": "data_integrity",
            "severity": "high",
            "week": None,
            "reason": f"{n_high} high-severity " + ("inconsistency" if n_high == 1 else "inconsistencies") + " found in the records.",
        })

    return {
        "balance": balance,
        "health_score": score,
        "status": status,
        "score_components": components,
        "warnings": warnings,
    }