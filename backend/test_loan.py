"""Checks for loan.py. Run from backend/ with the venv active."""
import copy
from stub_data import BUSINESS, TRANSACTIONS, INVOICES, OBLIGATIONS
from forecast import simulate
from loan import simulate_loan

b, t, i, o = (copy.deepcopy(x) for x in (BUSINESS, TRANSACTIONS, INVOICES, OBLIGATIONS))


def check(name, ok):
    print(("PASS  " if ok else "FAIL  ") + name)


def close(a, b_):
    return abs(a - b_) < 0.05


base = simulate(b, t, i, o)
small = simulate_loan(b, t, i, o, 100000, 12, 12)
big = simulate_loan(b, t, i, o, 5000000, 12, 12)

emi = small["emi"]
fl = small["forecast_with_loan"]
check("EMI of 100000 at 12% for 12 months is 8885", emi == 8885)
check("no change before the first EMI (day 29)", close(base["expected"][28] - fl["expected"][28], 0))
check("day 30 is lower by one EMI", close(base["expected"][29] - fl["expected"][29], emi))
check("day 90 is lower by three EMIs", close(base["expected"][89] - fl["expected"][89], 3 * emi))
for name, r in (("small", small), ("big", big)):
    check(f"{name}: affordable matches first_shortfall_date",
          r["affordable"] == (r["first_shortfall_date"] is None))
    check(f"{name}: shortfall is 0 exactly when affordable",
          (r["shortfall_amount"] == 0) == r["affordable"])

for name, r in (("small", small), ("big", big)):
    print(name, {k: v for k, v in r.items() if k != "forecast_with_loan"})