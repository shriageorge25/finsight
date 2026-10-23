"""Simple stand-ins for Sudiksha's analytics functions (same contracts).

Used only until her backend/analytics package is importable. Pure functions:
no FastAPI, no database calls.
"""
from datetime import date
from statistics import mean, pstdev

LATE_THRESHOLD_DAYS = 5  # a customer averaging more than this is "late"


def _days(later, earlier):
    return (date.fromisoformat(later) - date.fromisoformat(earlier)).days


def customer_delay_stats(invoices):
    """-> {customer: {mean_delay, std, samples[]}} from PAID invoices only."""
    samples = {}
    for inv in invoices:
        if inv.get("paid_date"):
            samples.setdefault(inv["customer"], []).append(
                _days(inv["paid_date"], inv["due_date"])
            )
    return {
        customer: {
            "mean_delay": round(mean(s), 2),
            "std": round(pstdev(s), 2),
            "samples": s,
        }
        for customer, s in samples.items()
    }


def get_late_payers(invoices):
    """-> [{customer, avg_delay_days, amount_at_risk}], biggest risk first."""
    result = []
    for customer, stats in customer_delay_stats(invoices).items():
        if stats["mean_delay"] > LATE_THRESHOLD_DAYS:
            at_risk = sum(
                inv["amount"]
                for inv in invoices
                if inv["customer"] == customer and not inv.get("paid_date")
            )
            result.append(
                {
                    "customer": customer,
                    "avg_delay_days": stats["mean_delay"],
                    "amount_at_risk": at_risk,
                }
            )
    return sorted(result, key=lambda r: r["amount_at_risk"], reverse=True)


def find_inconsistencies(transactions, invoices):
    """-> [{invoice_id, issue, reason, severity}]. Fallback checks duplicates only."""
    seen = {}
    issues = []
    for inv in invoices:
        key = (inv["customer"], inv["amount"], inv["issue_date"])
        if key in seen:
            issues.append(
                {
                    "invoice_id": inv["_id"],
                    "issue": "Possible duplicate invoice",
                    "reason": f"Same customer, amount and issue date as {seen[key]}",
                    "severity": "high",
                }
            )
        else:
            seen[key] = inv["_id"]
    return issues