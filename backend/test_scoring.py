"""Run from the backend folder:  python test_scoring.py"""
from stub_data import get_stub_data
import forecast as fc
import scoring


def run(opening=None):
    d = get_stub_data()
    if opening is not None:
        d["business"]["opening_balance"] = opening
    f = fc.simulate(d["business"], d["transactions"], d["invoices"], d["obligations"])
    return scoring.compute_summary(d["business"], d["transactions"], d["invoices"], d["obligations"], f)


for label, s in [("baseline", run()), ("opening 100000", run(100000))]:
    print(label, s["health_score"], s["status"], s["score_components"])
    for w in s["warnings"]:
        print("   ", w["type"], w["severity"], w["week"], "|", w["reason"])