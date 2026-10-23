"""Cash-flow forecast: Monte Carlo over customer payment delays.

Deterministic code only (no LLM). Same seed -> same numbers every run.
"""
import calendar
from datetime import date, timedelta
from statistics import median

import numpy as np

from analytics_bridge import customer_delay_stats

SEED = 7
N_SIMS = 300
RISK_THRESHOLD = 0.20
OVERDUE_FALLBACK_DAYS = 14  # assumption: no history of such lateness -> pays within 14 days


def _d(s):
    return date.fromisoformat(s)


def current_balance(business, transactions):
    """opening_balance + credits - debits, up to as_of_date (ISO strings compare correctly)."""
    as_of = business["as_of_date"]
    bal = business["opening_balance"]
    for t in transactions:
        if t["date"] <= as_of:
            bal += t["amount"] if t["type"] == "credit" else -t["amount"]
    return bal


def infer_recurring(transactions, min_months=3):
    """Debits whose description appears in >= min_months different months."""
    groups = {}
    for t in transactions:
        if t["type"] == "debit":
            groups.setdefault(t["description"].strip().lower(), []).append(t)
    recurring = []
    for items in groups.values():
        months = {t["date"][:7] for t in items}
        if len(months) >= min_months:
            recurring.append(
                {
                    "description": items[0]["description"],
                    "amount": float(median(t["amount"] for t in items)),
                    "day": int(round(median(int(t["date"][8:10]) for t in items))),
                }
            )
    return recurring


def _fixed_outflows(dates, recurring, obligations):
    """Known money going out on each forecast day (recurring + one-off obligations)."""
    one_off = {}
    for o in obligations:
        one_off[o["due_date"]] = one_off.get(o["due_date"], 0) + o["amount"]
    out = np.zeros(len(dates))
    for i, d in enumerate(dates):
        last_day = calendar.monthrange(d.year, d.month)[1]
        for r in recurring:
            if d.day == min(r["day"], last_day):
                out[i] += r["amount"]
        out[i] += one_off.get(d.isoformat(), 0)
    return out


def simulate(business, transactions, invoices, obligations,
             days=90, n_sims=N_SIMS, seed=SEED, extra_outflows=None,
             delay_shift=0, collect_ids=None):
    """Return {dates, expected, low, high, negative_probability}, all the same length."""
    as_of = _d(business["as_of_date"])
    dates = [as_of + timedelta(days=i) for i in range(1, days + 1)]
    balance = current_balance(business, transactions)
    fixed = _fixed_outflows(dates, infer_recurring(transactions), obligations)
    if extra_outflows is not None:  # e.g. loan EMIs: known amounts leaving on given days
        fixed = fixed + np.asarray(extra_outflows, dtype=float)
    stats = customer_delay_stats(invoices)
    pooled = sorted(d for s in stats.values() for d in s["samples"]) or [0]
    unpaid = [inv for inv in invoices if not inv.get("paid_date")]

    rng = np.random.default_rng(seed)
    u = rng.random((n_sims, len(unpaid)))  # one fixed random number per (run, invoice)
    inflow = np.zeros((n_sims, days))
    rows = np.arange(n_sims)

    for j, inv in enumerate(unpaid):
        if collect_ids and (inv.get("invoice_id") or inv.get("_id")) in collect_ids:
            inflow[:, 0] += inv["amount"]  # collected: money arrives tomorrow
            continue
        due_offset = (_d(inv["due_date"]) - as_of).days  # negative if already overdue
        late = max(0, -due_offset)
        pool = np.array(stats.get(inv["customer"], {}).get("samples") or pooled)
        if late > 0:
            pool = pool[pool > late]  # only delays longer than current lateness
        if late > 0 and len(pool) == 0:
            delay = late + 1 + (u[:, j] * OVERDUE_FALLBACK_DAYS).astype(int)
        else:
            pool = np.sort(pool)
            delay = pool[(u[:, j] * len(pool)).astype(int)]
        delay = delay + int(delay_shift)  # stress test: all payments this many days later
        offset = np.maximum(due_offset + delay, 1)  # earliest possible arrival: tomorrow
        ok = offset <= days
        np.add.at(inflow, (rows[ok], offset[ok] - 1), inv["amount"])

    cash = balance + np.cumsum(inflow - fixed, axis=1)  # shape (n_sims, days)
    return {
        "dates": [d.isoformat() for d in dates],
        "expected": np.round(np.median(cash, axis=0), 2).tolist(),
        "low": np.round(np.percentile(cash, 10, axis=0), 2).tolist(),
        "high": np.round(np.percentile(cash, 90, axis=0), 2).tolist(),
        "negative_probability": np.round((cash < 0).mean(axis=0), 4).tolist(),
    }


def first_risk_day(forecast, threshold=RISK_THRESHOLD):
    """First date whose negative probability is >= threshold, else None."""
    for d, p in zip(forecast["dates"], forecast["negative_probability"]):
        if p >= threshold:
            return d
    return None
