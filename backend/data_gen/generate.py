"""Synthetic data generator for FinSight. Run from backend/:  python -m data_gen.generate"""
import json
import os
import random
from collections import Counter
from datetime import date, timedelta

from data_gen import config as C

AS_OF = date.fromisoformat(C.AS_OF_DATE)
START = AS_OF - timedelta(days=364)  # 365 days of history, ending at AS_OF


def iso(d):
    return d.isoformat()


def make_amount(avg, issue_day, dips):
    """Irregular amount (never a multiple of 100) with seasonal dips applied."""
    factor = 1.0
    for first, last, f in dips:
        if first <= issue_day.month <= last:
            factor = f
    amount = max(int(random.gauss(avg * factor, avg * factor * 0.12)), 5000)
    if amount % 100 == 0:
        amount += random.randint(1, 99)
    return amount


def build_invoices(biz):
    """All invoices for one business, sorted by issue date (ids come later)."""
    out = []
    for name, per_month, avg, terms, mean_delay, std in biz["customers"]:
        d = START - timedelta(days=75) + timedelta(days=random.randint(0, 10))
        step = 30 // per_month
        while d <= AS_OF:
            due = d + timedelta(days=terms)
            delay = round(random.gauss(mean_delay, std))
            paid = max(due + timedelta(days=delay), d + timedelta(days=1))
            out.append({
                "business_id": biz["id"],
                "customer": name,
                "amount": make_amount(avg, d, biz["seasonal_dips"]),
                "issue_date": iso(d),
                "due_date": iso(due),
                # a payment that would land after AS_OF has not happened yet
                "paid_date": iso(paid) if paid <= AS_OF else None,
            })
            d += timedelta(days=step + random.randint(-2, 2))
    out.sort(key=lambda r: (r["issue_date"], r["customer"]))
    out = [r for r in out if not r["paid_date"] or r["paid_date"] >= iso(START)]
    return out


def status(inv):
    if inv["paid_date"]:
        return "paid"
    return "overdue" if inv["due_date"] < iso(AS_OF) else "not yet due"


def assign_ids(invs):
    """inv_1, inv_2, ... in issue-date order, per business."""
    for n, inv in enumerate(invs, start=1):
        inv["_id"] = f"inv_{n}"
    return invs


def invoice_label(inv_id):
    """inv_4 -> INV-004, used in bank descriptions so detectors can match."""
    return "INV-%03d" % int(inv_id.split("_")[1])


def month_starts(first, last):
    """First day of every month from first's month through last's month."""
    y, m = first.year, first.month
    out = []
    while (y, m) <= (last.year, last.month):
        out.append(date(y, m, 1))
        m += 1
        if m == 13:
            y, m = y + 1, 1
    return out


def build_transactions(biz, invs, skip_ids):
    """Credits (one per paid invoice, except skip_ids) plus monthly debits."""
    txns = []
    for inv in invs:
        if inv["paid_date"] and inv["_id"] not in skip_ids:
            txns.append({
                "business_id": biz["id"],
                "date": inv["paid_date"],
                "description": f"{invoice_label(inv['_id'])} payment - {inv['customer']}",
                "amount": inv["amount"],
                "type": "credit",
                "category": "invoice_payment",
            })
    for first_of_month in month_starts(START, AS_OF):
        for text, amount in biz["recurring"].items():
            day = first_of_month + timedelta(days=random.randint(0, 4))
            if day < START or day > AS_OF:
                continue
            txns.append({
                "business_id": biz["id"],
                "date": iso(day),
                "description": text,
                "amount": amount,
                "type": "debit",
                "category": text.split(" - ")[0].split(" and ")[0].lower(),
            })
    txns.sort(key=lambda t: (t["date"], t["description"]))
    return txns


def build_obligations(biz):
    return [{
        "business_id": biz["id"],
        "description": desc,
        "amount": amount,
        "due_date": iso(AS_OF + timedelta(days=days)),
    } for desc, amount, days in biz["obligations"]]


def current_balance(biz, txns):
    credits = sum(t["amount"] for t in txns if t["type"] == "credit")
    debits = sum(t["amount"] for t in txns if t["type"] == "debit")
    return biz["opening_balance"] + credits - debits


def delay_days(inv):
    return (date.fromisoformat(inv["paid_date"]) - date.fromisoformat(inv["due_date"])).days


def realised_delays(invs):
    """customer -> mean delay and count, from PAID invoices only (what detectors will see)."""
    by = {}
    for inv in invs:
        if inv["paid_date"]:
            by.setdefault(inv["customer"], []).append(delay_days(inv))
    return {c: {"mean_delay": round(sum(v) / len(v), 2), "paid_invoices": len(v)}
            for c, v in by.items()}


def slow_payer(biz):
    """The customer configured with the largest mean delay."""
    return max(biz["customers"], key=lambda c: c[4])[0]


def add_planted_invoices(biz, invs):
    """b3 only: one exact duplicate invoice and one round-number invoice, both unpaid."""
    if "planted_round_amount" not in biz:
        return
    unpaid = sorted((i for i in invs if not i["paid_date"]), key=lambda i: i["due_date"])
    invs.append(dict(unpaid[0]))  # exact copy: same customer, amount and dates
    issue = AS_OF - timedelta(days=70)
    invs.append({
        "business_id": biz["id"], "customer": "Hotel Mayura",
        "amount": biz["planted_round_amount"],
        "issue_date": iso(issue), "due_date": iso(issue + timedelta(days=30)),
        "paid_date": None,
    })
    invs.sort(key=lambda r: (r["issue_date"], r["customer"]))


def pick_paid_without_deposit(biz, invs):
    """b2 only: paid invoices (not the slow payer's) that will get NO bank credit."""
    rng = random.Random(C.SEED + 1)  # separate generator, so main data is unaffected
    lo = iso(AS_OF - timedelta(days=170))
    hi = iso(AS_OF - timedelta(days=25))
    slow = slow_payer(biz)
    pool = [i for i in invs if i["paid_date"] and lo <= i["paid_date"] <= hi
            and i["customer"] != slow and i["amount"] >= 100000]
    return rng.sample(pool, biz["paid_without_deposit"])


def write_outputs(bundle):
    """CSVs always; MongoDB unless run with --no-db."""
    import sys
    import pandas as pd
    out_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "sample_data"))
    os.makedirs(out_dir, exist_ok=True)
    for name, rows in bundle.items():
        pd.DataFrame(rows).to_csv(os.path.join(out_dir, name + ".csv"), index=False)
    print("wrote CSVs to", out_dir)
    if "--no-db" in sys.argv:
        return
    from db import db  # Shria's connection to the "finsight" database
    for name, rows in bundle.items():
        db[name].delete_many({})
        if rows:
            db[name].insert_many([dict(r) for r in rows])
        print("seeded", name, db[name].count_documents({}))

def main():
    random.seed(C.SEED)
    truth = {"seed": C.SEED, "as_of_date": C.AS_OF_DATE, "realised_delays": {}}
    bundle = {"businesses": [], "transactions": [], "invoices": [], "obligations": []}
    for biz in C.BUSINESSES:
        invs = build_invoices(biz)
        add_planted_invoices(biz, invs)
        assign_ids(invs)
        delays = realised_delays(invs)
        truth["realised_delays"][biz["id"]] = delays

        skip_ids = set()
        if biz.get("paid_without_deposit"):
            picked = pick_paid_without_deposit(biz, invs)
            skip_ids = {i["_id"] for i in picked}
            slow = slow_payer(biz)
            truth["paid_but_no_deposit"] = {
                "business_id": biz["id"],
                "invoice_ids": sorted(skip_ids),
                "details": [{"invoice_id": i["_id"], "label": invoice_label(i["_id"]),
                             "customer": i["customer"], "amount": i["amount"],
                             "paid_date": i["paid_date"]} for i in picked],
            }
            truth["slow_payer"] = {
                "business_id": biz["id"], "customer": slow,
                "true_avg_delay_days": delays[slow]["mean_delay"],
                "paid_invoices": delays[slow]["paid_invoices"],
                "configured_mean_delay": max(c[4] for c in biz["customers"]),
            }
        if "planted_round_amount" in biz:
            groups = Counter((i["customer"], i["amount"], i["issue_date"]) for i in invs)
            key = [k for k, n in groups.items() if n > 1][0]
            dup_ids = [i["_id"] for i in invs
                       if (i["customer"], i["amount"], i["issue_date"]) == key]
            truth["duplicate_invoices"] = {
                "business_id": biz["id"], "invoice_ids": dup_ids,
                "customer": key[0], "amount": key[1], "issue_date": key[2],
                "expected_flag": dup_ids[-1],  # the later copy is the duplicate
            }
            rnd = [i for i in invs if i["amount"] == biz["planted_round_amount"]][0]
            truth["round_number_entry"] = {
                "business_id": biz["id"], "invoice_id": rnd["_id"], "amount": rnd["amount"]}

        txns = build_transactions(biz, invs, skip_ids)
        obls = build_obligations(biz)
        bundle["businesses"].append({"_id": biz["id"], "name": biz["name"], "sector": biz["sector"],
                                     "opening_balance": biz["opening_balance"], "as_of_date": C.AS_OF_DATE})
        bundle["transactions"] += txns
        bundle["invoices"] += invs
        bundle["obligations"] += obls
        low, running = 10**12, biz["opening_balance"]
        for t in txns:
            running += t["amount"] if t["type"] == "credit" else -t["amount"]
            low = min(low, running)
        print(biz["id"], biz["name"], "| invoices", len(invs), dict(Counter(status(i) for i in invs)),
              "| txns", len(txns), "| balance", current_balance(biz, txns), "| lowest", low)

    write_outputs(bundle)
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "planted_truth.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(truth, f, indent=2)
    print("wrote", path)


if __name__ == "__main__":
    main()

