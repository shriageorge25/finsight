"""Checks the running API against the README contract.
Run from backend/ with uvicorn running: python check_contract.py [business_id]
"""
import json
import sys
import urllib.error
import urllib.request

BASE = "http://localhost:8000"
FORECAST_KEYS = ["dates", "expected", "low", "high", "negative_probability"]
failures = 0


def call(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, None


def check(name, ok):
    global failures
    print(("PASS  " if ok else "FAIL  ") + name)
    if not ok:
        failures += 1


def has_keys(rows, keys):
    return isinstance(rows, list) and all(isinstance(r, dict) and all(k in r for k in keys) for r in rows)


def is_forecast(f):
    if not isinstance(f, dict) or any(k not in f for k in FORECAST_KEYS):
        return False
    n = len(f["dates"])
    return n > 0 and all(len(f[k]) == n for k in FORECAST_KEYS)


bid = sys.argv[1] if len(sys.argv) > 1 else "stub-1"
p = "/businesses/" + bid

s, d = call("GET", "/health")
check("/health keys", s == 200 and has_keys([d], ["status", "data_source", "analytics"]))

s, d = call("GET", "/businesses")
check("/businesses keys", s == 200 and has_keys(d, ["id", "name", "sector", "status"]))

s, d = call("GET", p + "/summary")
check("summary keys", s == 200 and has_keys([d], ["balance", "health_score", "score_components", "warnings"]))
check("summary score_components", s == 200 and has_keys([d["score_components"]], ["liquidity", "collections", "concentration", "data_integrity", "buffer"]))
check("summary warnings keys", s == 200 and has_keys(d["warnings"], ["type", "severity", "week", "reason"]))

s, d = call("GET", p + "/forecast?days=10")
check("forecast shape, 10 days", s == 200 and is_forecast(d) and len(d["dates"]) == 10)

s, d = call("POST", p + "/loan-simulate", {"amount": 500000, "rate": 12, "tenure_months": 24})
loan_keys = ["emi", "affordable", "first_shortfall_date", "shortfall_amount", "baseline_first_shortfall_date", "forecast_with_loan"]
check("loan-simulate keys", s == 200 and has_keys([d], loan_keys))
check("loan-simulate forecast shape", s == 200 and is_forecast(d["forecast_with_loan"]))

s, d = call("GET", p + "/late-payers")
check("late-payers keys", s == 200 and has_keys(d, ["customer", "avg_delay_days", "amount_at_risk"]))

s, d = call("GET", p + "/overdue-invoices")
check("overdue-invoices keys", s == 200 and has_keys(d, ["invoice_id", "customer", "amount", "days_overdue"]))

s, d = call("GET", p + "/inconsistencies")
check("inconsistencies keys", s == 200 and has_keys(d, ["invoice_id", "issue", "reason", "severity"]))

for path in ["/summary", "/forecast", "/late-payers", "/overdue-invoices", "/inconsistencies"]:
    s, d = call("GET", "/businesses/nope" + path)
    check("404 for unknown business: " + path, s == 404)

s, d = call("POST", "/businesses/nope/loan-simulate", {"amount": 500000, "rate": 12, "tenure_months": 24})
check("404 for unknown business: loan-simulate", s == 404)

s, d = call("POST", p + "/loan-simulate", {"amount": -5, "rate": 12, "tenure_months": 12})
check("422 for bad loan amount", s == 422)

print()
print("ALL CHECKS PASSED" if failures == 0 else str(failures) + " CHECK(S) FAILED")
sys.exit(1 if failures else 0)