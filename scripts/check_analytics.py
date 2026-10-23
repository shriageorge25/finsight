"""Runs the analytics on the generated CSVs and compares to planted_truth.json."""
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))
from analytics import customer_delay_stats, find_inconsistencies, get_late_payers  # noqa: E402


def load(name):
    with open(ROOT / "sample_data" / name, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


truth = json.loads((ROOT / "backend/data_gen/planted_truth.json").read_text(encoding="utf-8"))
inv_by_biz, txn_by_biz = defaultdict(list), defaultdict(list)
for r in load("invoices.csv"):
    inv_by_biz[r["business_id"]].append(r)
for r in load("transactions.csv"):
    txn_by_biz[r["business_id"]].append(r)

credits = [t["description"] for t in txn_by_biz["b2"] if t["type"] == "credit"]
print("Sample credit descriptions (b2):", credits[:3])

results = []
flags = {}
for biz in inv_by_biz:
    flags[biz] = find_inconsistencies(txn_by_biz[biz], inv_by_biz[biz])


def ids(biz, issue):
    return sorted(f["invoice_id"] for f in flags[biz] if f["issue"] == issue)


# 1) delay stats vs realised delays
bad = []
for biz, custs in truth["realised_delays"].items():
    stats = customer_delay_stats(inv_by_biz[biz])
    for cust, exp in custs.items():
        got = stats.get(cust, {}).get("mean_delay")
        if got is None or abs(got - exp["mean_delay"]) > 0.01:
            bad.append((biz, cust, exp["mean_delay"], got))
results.append(("delay stats match realised delays", not bad, bad))

# 2) paid but no deposit: exact match, no extras anywhere
p = truth["paid_but_no_deposit"]
got = ids(p["business_id"], "Marked paid, no matching bank deposit")
extra = {b: ids(b, "Marked paid, no matching bank deposit") for b in flags if b != p["business_id"]}
extra = {b: v for b, v in extra.items() if v}
results.append(("paid-no-deposit exact", got == sorted(p["invoice_ids"]) and not extra,
                {"expected": sorted(p["invoice_ids"]), "got": got, "other_businesses": extra}))

# 3) duplicate: later copy flagged
d = truth["duplicate_invoices"]
got = ids(d["business_id"], "Possible duplicate invoice")
results.append(("duplicate flags inv_61 only", got == [d["expected_flag"]], {"got": got}))

# 4) round numbers: planted one found; list the rest
r = truth["round_number_entry"]
got = ids(r["business_id"], "Suspicious round-number entry")
results.append(("round-number finds planted entry", r["invoice_id"] in got, {"all_flagged": got}))

# 5) slow payer appears in late payers
s = truth["slow_payer"]
late = get_late_payers(inv_by_biz[s["business_id"]])
results.append(("slow payer listed as late payer", s["customer"] in [x["customer"] for x in late], late))

failed = 0
for name, ok, detail in results:
    print(("PASS  " if ok else "FAIL  ") + name)
    if not ok:
        failed += 1
        print("      ", detail)
for biz in sorted(inv_by_biz):
    print(biz, "late payers:", [(x["customer"], x["avg_delay_days"]) for x in get_late_payers(inv_by_biz[biz])])
sys.exit(1 if failed else 0)