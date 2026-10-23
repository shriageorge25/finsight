"""Run from the backend folder:  python test_forecast.py"""
from stub_data import get_stub_data
import forecast as fc


def run(opening=None):
    d = get_stub_data()  # fresh copy each time, so changing it here is safe
    if opening is not None:
        d["business"]["opening_balance"] = opening
    f = fc.simulate(d["business"], d["transactions"], d["invoices"], d["obligations"])
    return d, f


d, f = run()
n = len(f["dates"])
assert all(len(f[k]) == n for k in f), "forecast lists must be the same length"

print("balance:", fc.current_balance(d["business"], d["transactions"]))
print("recurring:", [(r["description"], r["amount"], r["day"]) for r in fc.infer_recurring(d["transactions"])])
print("forecast days:", n)
print("first risk day (baseline):", fc.first_risk_day(f))
i = f["dates"].index("2026-11-08")
print("band on 2026-11-08 -> low/expected/high:", f["low"][i], f["expected"][i], f["high"][i])
print("end of horizon -> low/expected/high:", f["low"][-1], f["expected"][-1], f["high"][-1])

_, f2 = run(opening=100000)
print("first risk day (opening 100000):", fc.first_risk_day(f2))

_, f3 = run()
print("two runs identical:", f == f3)