# FinSight

MSME Cash-Flow Early Warning and Loan Readiness. FinSight analyses a small
business's bank transactions and invoices, forecasts cash for 90 days with a
confidence band, warns about shortfalls, and lets the owner test a loan
("in which week would I run short?").

All numbers come from deterministic code. The AI (Gemini) only writes
plain-language explanations and drafts reminders. All data is synthetic.
Outputs are decision support, not financial advice.

## Ownership

| Area | Owner |
|---|---|
| backend/main.py, db.py, llm.py, forecast.py, loan.py, scoring.py, actions.py, explain.py | Shria |
| backend/data_gen/, backend/analytics/, frontend/, scripts/, sample_data/ | Sudiksha |
| README.md | Shria. Sudiksha proposes changes by message, then both update it in the same commit |

Never edit the other person's files. Never rename a field without updating this file.

## Run

Backend (from backend/): `.venv\Scripts\activate`, then `uvicorn main:app --reload` (http://localhost:8000, docs at /docs)
Frontend (from frontend/): `npm run dev` (http://localhost:5173)
Secrets live in backend/.env (never committed): GEMINI_API_KEY, GEMINI_MODEL, MONGODB_URI

## Conventions

- Dates are ISO strings "YYYY-MM-DD". Amounts are positive numbers in rupees.
- `as_of_date` is "today" for the forecast. It must be identical in the generator, forecast and UI.
- The generator uses `random.seed(42)` so both of us see identical data.
- Database: MongoDB, database name `finsight`.

## Data schema

**businesses**
`{_id:"b1", name, sector, opening_balance, as_of_date}`
`opening_balance` is the balance at the START of the 12 months of history.
Current balance = opening + credits - debits up to as_of_date.

**transactions**
`{business_id, date, description, amount, type:"credit"|"debit", category}`

**invoices**
`{_id:"inv_1", business_id, customer, amount, issue_date, due_date, paid_date: "YYYY-MM-DD" | null}`

**obligations** (one-off future payments, e.g. a large supplier payment)
`{business_id, description, amount, due_date}`
Do not ALSO include these as recurring debits in transactions, or they are counted twice.

## Forecast object (reused everywhere)

```json
{"dates":["2026-10-25"],"expected":[412000],"low":[380000],"high":[440000],"negative_probability":[0.02]}
```
All five arrays have the same length (one entry per day).

## Endpoints

### GET /businesses
```json
[{"id":"b1","name":"Sharma Textiles","sector":"Retail","status":"healthy"}]
```
`status` is one of: healthy | watch | at_risk

### GET /businesses/{id}/summary
```json
{"balance":412000,"health_score":71,
 "score_components":{"liquidity":36,"collections":20,"concentration":10,"data_integrity":10,"buffer":8},
 "warnings":[{"type":"liquidity_gap","severity":"high","week":"2026-03-14",
   "reason":"Cash may run out around 2026-03-14; worst case short by ₹42,000."}]}
```
`warnings[].week` may be null for warnings not tied to a date.
`score_components` is extra detail; the UI may ignore it or show it in "Why this score?".

### GET /businesses/{id}/forecast?days=90
Returns the forecast object.

### POST /businesses/{id}/loan-simulate
Request: `{"amount":500000,"rate":12,"tenure_months":24}`
```json
{"emi":23536,"affordable":false,"first_shortfall_date":"2026-03-14",
 "shortfall_amount":42000,"baseline_first_shortfall_date":null,
 "forecast_with_loan":{"dates":[],"expected":[],"low":[],"high":[],"negative_probability":[]}}
```
`first_shortfall_date` is null when the loan is affordable. The check covers the 90-day horizon.

### GET /businesses/{id}/late-payers
```json
[{"customer":"Mehta Traders","avg_delay_days":38,"amount_at_risk":320000}]
```

### GET /businesses/{id}/inconsistencies
```json
[{"invoice_id":"inv_12","issue":"Marked paid, no matching bank deposit",
  "reason":"Invoice of Rs 85,000 marked paid on 3 Feb but no matching credit found","severity":"high"}]
```
`severity` is one of: high | medium | low

### GET /businesses/{id}/overdue-invoices
```json
[{"invoice_id":"inv_2","customer":"Mehta Traders","amount":120000,"days_overdue":23}]
```

### POST /businesses/{id}/actions/simulate
Request: `{"collect_invoice_ids":["inv_2","inv_3"]}`
```json
{"gap_closed_pct":80,"forecast_after":{"dates":[],"expected":[],"low":[],"high":[],"negative_probability":[]}}
```
`gap_closed_pct` is the reduction in worst-case shortfall if those overdue invoices are collected.

### POST /businesses/{id}/stress
Request: `{"revenue_drop_pct":20,"delay_days":30}` (both optional, default 0)
Returns the forecast object.

### GET /businesses/{id}/explain
```json
{"summary":"Plain-language AI explanation of the business's financial health..."}
```

### POST /businesses/{id}/reminders
Request: `{"customer":"Mehta Traders"}`
```json
{"message":"Hello Mehta Traders, a gentle reminder that ..."}
```

## Function contracts (written by Sudiksha, imported by Shria)

Pure functions: no FastAPI, no database calls. They take lists of dicts and return lists or dicts.

```
customer_delay_stats(invoices) -> {customer: {"mean_delay": float, "std": float, "samples": [int]}}
get_late_payers(invoices)      -> [{"customer", "avg_delay_days", "amount_at_risk"}]
find_inconsistencies(transactions, invoices) -> [{"invoice_id", "issue", "reason", "severity"}]
```
- Delay = paid_date minus due_date in days, PAID invoices only. Negative means early; keep it.
- `samples` is what the Monte Carlo forecast draws random delays from.
- `amount_at_risk` = sum of that customer's UNPAID invoices.

## Modelling assumptions (be honest with judges)

- Forecast: each unpaid invoice arrives on due date plus a delay sampled from that customer's history. 300 simulations; expected = median, band = 10th to 90th percentile.
- Loan proceeds are treated as invested in the business, not held as cash. Only EMIs reduce cash.
- Cash inflows come from invoices only. Recurring costs are inferred from history.
- Data is synthetic. Not financial advice.
### Contract clarifications
- `inconsistencies.issue` is one of: "Marked paid, no matching bank deposit" (high),
  "Possible duplicate invoice" (high), "Suspicious round-number entry" (low).
  `reason` is the specific sentence for that invoice.
- `score_components` are integer points earned. Maximums: liquidity 40, collections 25,
  concentration 15, data_integrity 10, buffer 10. `health_score` = sum of the five.
- Every credit transaction is the payment of one invoice: amount = invoice amount,
  date = paid_date, description contains the invoice id (e.g. "INV-004 payment - Kaveri Retail").
- /loan-simulate when affordable: first_shortfall_date = null, shortfall_amount = 0.
  baseline_first_shortfall_date = null when the baseline has no shortfall.