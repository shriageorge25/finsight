"""Sudiksha's analytics: the three functions analytics_bridge.py imports."""
import re
import statistics
from collections import defaultdict
from datetime import date, datetime

# Tunable thresholds (assistant's choices, not in the spec)
LATE_PAYER_MIN_DELAY_DAYS = 3    # mean delay at or above this = "late payer"
ROUND_AMOUNT_STEP = 10000        # multiple of this ...
ROUND_AMOUNT_MIN = 50000         # ... and at least this = "round number"

ISSUE_NO_DEPOSIT = "Marked paid, no matching bank deposit"
ISSUE_DUPLICATE = "Possible duplicate invoice"
ISSUE_ROUND = "Suspicious round-number entry"


def _to_date(value):
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])


def _invoice_id(inv):
    for key in ("_id", "invoice_id", "id"):
        if inv.get(key) is not None:
            return str(inv[key])
    return None


def customer_delay_stats(invoices):
    """{customer: {mean_delay, std, samples[]}}; delay = paid_date - due_date in days."""
    delays = defaultdict(list)
    for inv in invoices:
        paid = _to_date(inv.get("paid_date"))
        due = _to_date(inv.get("due_date"))
        if paid is None or due is None:
            continue
        delays[inv["customer"]].append((paid - due).days)
    stats = {}
    for customer, samples in delays.items():
        stats[customer] = {
            "mean_delay": round(statistics.mean(samples), 2),
            "std": round(statistics.stdev(samples), 2) if len(samples) >= 2 else 0.0,
            "samples": samples,
        }
    return stats


def get_late_payers(invoices):
    """[{customer, avg_delay_days, amount_at_risk}], biggest rupees at risk first."""
    stats = customer_delay_stats(invoices)
    unpaid = defaultdict(float)
    for inv in invoices:
        if _to_date(inv.get("paid_date")) is None:
            unpaid[inv["customer"]] += float(inv["amount"])
    result = []
    for customer, s in stats.items():
        if s["mean_delay"] >= LATE_PAYER_MIN_DELAY_DAYS:
            result.append({
                "customer": customer,
                "avg_delay_days": s["mean_delay"],
                "amount_at_risk": round(unpaid.get(customer, 0.0), 2),
            })
    result.sort(key=lambda r: r["amount_at_risk"], reverse=True)
    return result


def find_inconsistencies(transactions, invoices):
    """[{invoice_id, issue, reason, severity}] using the three agreed labels."""
    findings = []
    credit_text = [str(t.get("description", ""))
                   for t in transactions if t.get("type") == "credit"]

    # 1) Marked paid but no credit transaction mentions the invoice id
    for inv in invoices:
        inv_id = _invoice_id(inv)
        if inv_id is None or _to_date(inv.get("paid_date")) is None:
            continue
        pattern = re.compile(r"(?<![A-Za-z0-9])" + re.escape(inv_id) + r"(?![A-Za-z0-9])")
        if not any(pattern.search(text) for text in credit_text):
            findings.append({
                "invoice_id": inv_id,
                "issue": ISSUE_NO_DEPOSIT,
                "reason": f"Invoice {inv_id} is marked paid on {inv['paid_date']} "
                          f"but no bank credit references it.",
                "severity": "high",
            })

    # 2) Same customer + amount + issue_date: flag every copy after the first
    groups = defaultdict(list)
    for inv in invoices:
        key = (inv["customer"], float(inv["amount"]), str(inv["issue_date"])[:10])
        groups[key].append(inv)
    for group in groups.values():
        if len(group) > 1:
            group = sorted(group, key=lambda i: _invoice_id(i) or "")
            original = _invoice_id(group[0])
            for dup in group[1:]:
                findings.append({
                    "invoice_id": _invoice_id(dup),
                    "issue": ISSUE_DUPLICATE,
                    "reason": f"Same customer, amount and issue date as {original}.",
                    "severity": "high",
                })

    # 3) Suspiciously round amounts
    for inv in invoices:
        amount = float(inv["amount"])
        if amount >= ROUND_AMOUNT_MIN and amount % ROUND_AMOUNT_STEP == 0:
            findings.append({
                "invoice_id": _invoice_id(inv),
                "issue": ISSUE_ROUND,
                "reason": f"Amount {amount:,.0f} is an unusually round number.",
                "severity": "low",
            })

    return findings