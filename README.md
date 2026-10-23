FinSight
MSME Cash-Flow Early Warning and Loan Readiness. FinSight analyses a small
business's bank transactions and invoices, forecasts cash for 90 days with a
confidence band, warns about shortfalls, and lets the owner test a loan
("in which week would I run short?").
All numbers come from deterministic code. The LLM (Gemini today; Amazon Bedrock
planned, with Gemini as fallback) only writes plain-language explanations and
drafts reminders. All data is synthetic. Outputs are decision support, not
financial advice.
Ownership
Area	Owner
backend/main.py, db.py, llm.py, forecast.py, loan.py, scoring.py, actions.py, explain.py, stub_data.py, fallback_analytics.py, analytics_bridge.py, README.md	Shria
backend/data_gen/, backend/analytics/, frontend/, scripts/, sample_data/	Sudiksha
README changes: Sudiksha proposes by message, then both update it in the same commit.
Never edit the other person's files. Never rename a field without updating this file.
Pull before every push. Commit small.
Run
Backend (from backend/): `.venv\Scripts\activate`, then `uvicorn main:app --reload`
(http://localhost:8000, interactive docs at /docs)
Frontend (from frontend/): `npm run dev` (http://localhost:5173). Backend CORS allows this origin.
Secrets live in backend/.env (never committed): GEMINI_API_KEY, GEMINI_MODEL, MONGODB_URI
Each person runs the backend locally. The frontend calls http://localhost:8000.
If MongoDB Atlas is unreachable (3 s timeout), the backend serves built-in synthetic
stub data (business id `stub-1`) instead of failing. `GET /health` shows which source is live.
GET /health
```json
{"status":"ok","data_source":"mongodb","analytics":"sudiksha"}
```
`data_source` is `mongodb` or `stub`. `analytics` is `sudiksha` (her functions imported)
or `fallback` (backend's own fallback_analytics.py is in use).
Conventions
Dates are ISO strings "YYYY-MM-DD". Amounts are positive numbers in rupees.
`as_of_date` is "today" for the forecast: 2026-10-24 everywhere (generator, forecast, UI).
The generator uses `random.seed(42)` so both of us see identical data.
Database: MongoDB, database name `finsight`.
Errors (convention for all new endpoints): unknown business id or customer returns 404,
invalid request body returns 422.
Data schema
businesses
`{_id:"b1", name, sector, opening_balance, as_of_date}`
`opening_balance` is the balance at the START of the 12 months of history.
Current balance = opening + credits - debits up to as_of_date.
transactions
`{business_id, date, description, amount, type:"credit"|"debit", category}`
invoices
`{_id:"inv_1", business_id, customer, amount, issue_date, due_date, paid_date: "YYYY-MM-DD" | null}`
obligations (one-off future payments, e.g. a GST payment)
`{business_id, description, amount, due_date}`
Do not ALSO include these as recurring debits in transactions, or they are counted twice.
Forecast object (reused everywhere)
```json
{"dates":["2026-10-25"],"expected":[412000],"low":[380000],"high":[440000],"negative_probability":[0.02]}
```
All five arrays have the same length (one entry per day). The first date is the day
after as_of_date. `expected` is the median, `low` the 10th percentile, `high` the 90th.
Endpoints
GET /businesses
```json
[{"id":"b1","name":"Sharma Textiles","sector":"Retail","status":"healthy"}]
```
`status` is one of: healthy | watch | at_risk (from the health score, see below).
GET /businesses/{id}/summary
```json
{"balance":412000,"health_score":71,
 "score_components":{"liquidity":36,"collections":20,"concentration":10,"data_integrity":10,"buffer":8},
 "warnings":[{"type":"liquidity_gap","severity":"high","week":"2026-12-14",
   "reason":"Cash may run out around 2026-12-14; worst case short by ₹42,000."}]}
```
`warnings[].week` holds a date (the first risk day), despite the field name. It is null
for warnings not tied to a date.
Warning types currently produced: `liquidity_gap`, `overdue_collections`,
`customer_concentration`.
`score_components` is extra detail; the UI may ignore it or show it in "Why this score?".
GET /businesses/{id}/forecast?days=90
Returns the forecast object. `days` defaults to 90.
POST /businesses/{id}/loan-simulate
Request: `{"amount":500000,"rate":12,"tenure_months":24}` (`rate` is annual percent)
```json
{"emi":23536,"affordable":false,"first_shortfall_date":"2026-12-14",
 "shortfall_amount":42000,"baseline_first_shortfall_date":null,
 "forecast_with_loan":{"dates":[],"expected":[],"low":[],"high":[],"negative_probability":[]}}
```
`affordable` is true when the loan scenario has no risk day in the 90-day horizon.
`first_shortfall_date` = first risk day with the loan. Null when affordable.
`shortfall_amount` = worst-case (10th percentile) shortfall: the largest amount by which
`low` goes below zero. 0 when affordable.
`baseline_first_shortfall_date` = same, without the loan. Null if the baseline has none.
Risk day = `negative_probability >= 0.20`.
GET /businesses/{id}/late-payers
```json
[{"customer":"Mehta Traders","avg_delay_days":38,"amount_at_risk":320000}]
```
GET /businesses/{id}/inconsistencies
```json
[{"invoice_id":"inv_12","issue":"Marked paid, no matching bank deposit",
  "reason":"Invoice of Rs 85,000 marked paid on 3 Feb but no matching credit found","severity":"high"}]
```
`severity` is one of: high | medium | low (medium is currently unused).
GET /businesses/{id}/overdue-invoices
```json
[{"invoice_id":"inv_2","customer":"Mehta Traders","amount":120000,"days_overdue":23}]
```
Overdue = unpaid with due_date before as_of_date.
POST /businesses/{id}/actions/simulate
Request: `{"collect_invoice_ids":["inv_2","inv_3"]}`
```json
{"gap_closed_pct":80,"forecast_after":{"dates":[],"expected":[],"low":[],"high":[],"negative_probability":[]}}
```
"Collecting" an invoice means its money arrives tomorrow. `gap_closed_pct` is the
reduction in worst-case shortfall if those invoices are collected, from 0 to 100.
It is 0 when the baseline has no shortfall.
POST /businesses/{id}/stress
Request: `{"revenue_drop_pct":20,"delay_days":30}` (both optional, default 0)
Returns the forecast object. Invoice amounts are scaled by (1 - revenue_drop_pct/100) and
every sampled payment delay is shifted by delay_days, using the same random draws as the baseline.
GET /businesses/{id}/explain
```json
{"summary":"Plain-language AI explanation of the business's financial health..."}
```
POST /businesses/{id}/reminders
Request: `{"customer":"Mehta Traders"}`
```json
{"message":"Hello Mehta Traders, a gentle reminder that ..."}
```
Function contracts (written by Sudiksha, imported by Shria via analytics_bridge.py)
Pure functions: no FastAPI, no database calls. They take lists of dicts and return lists or dicts.
They must be importable as `from analytics import ...` (export them from backend/analytics/init.py).
If the import fails, the backend silently uses fallback_analytics.py and `/health` shows `fallback`.
```
customer_delay_stats(invoices) -> {customer: {"mean_delay": float, "std": float, "samples": [int]}}
get_late_payers(invoices)      -> [{"customer", "avg_delay_days", "amount_at_risk"}]
find_inconsistencies(transactions, invoices) -> [{"invoice_id", "issue", "reason", "severity"}]
```
Delay = paid_date minus due_date in days, PAID invoices only. Negative means early; keep it.
`samples` is what the Monte Carlo forecast draws random delays from.
`amount_at_risk` = sum of that customer's UNPAID invoices.
`issue` is one of: "Marked paid, no matching bank deposit" (high),
"Possible duplicate invoice" (high), "Suspicious round-number entry" (low).
`reason` is the specific sentence for that invoice.
Detection rules (so judges get one consistent answer):
Marked paid, no matching bank deposit: paid_date is set but, within the same business, no credit transaction has a description containing the invoice number (inv_34 matches "INV-034", zero-padding ignored) and an amount equal to the invoice amount.
Possible duplicate invoice: same customer, amount and issue_date as another invoice.
Suspicious round-number entry: an invoice whose amount is an exact multiple of 10,000 and at least 50,000. Example: b3 inv_57, amount 100000. (Team choice, not in the original spec.)
Inconsistency `invoice_id` is the plain invoice number (e.g. "inv_34"), taken from the invoice's `invoice_id` field. Mongo `_id` is business-scoped (e.g. "b2_inv_34"); `business_id` is stored on every invoice.
Health score (backend/scoring.py, formula-based)
`health_score` = sum of five integer components. Status: healthy >= 70, watch >= 45, else at_risk.
Component	Max	Formula
liquidity	40	40 x (1 - highest negative_probability over the 90 days)
collections	25	25 x (1 - overdue share of unpaid invoice value)
concentration	15	full marks while the top customer is <= 30% of unpaid value, falling linearly to 0 at 100%
data_integrity	10	10 minus 2 per high-severity inconsistency (floor 0)
buffer	10	10 x min(runway / 2, 1), runway = balance / monthly recurring debits
The concentration slope, the 2 points per issue and the runway definition are team design
choices, not taken from the problem statement.
Modelling assumptions (be honest with judges)
Forecast: start from the current balance. Each unpaid invoice arrives on its due date plus a
delay sampled from that customer's history (pooled delays if the customer has no history).
300 simulations, fixed seed 7, one fixed random number per (run, invoice).
expected = median, band = 10th to 90th percentile,
negative_probability = share of runs below zero.
Already-overdue invoices: only delays longer than the current lateness are possible. If the
history has none, we assume payment within the next 14 days (our added assumption).
Earliest arrival is tomorrow.
Recurring debits: descriptions that repeat in at least 3 different months (median amount,
median day of month). One-off obligations come from the obligations collection.
Loan proceeds are treated as invested in the business, not held as cash. Only EMIs reduce
cash, one every 30 days across the 90-day horizon.
The band shows uncertainty about WHEN money arrives. It narrows toward day 90 as all
invoices have arrived in every run. It does not say whether customers are good.
Known limitation: the forecast counts only invoices already issued, not future unbilled sales.
Cash inflows come from invoices only.
Amazon Forecast and Lookout for Metrics are closed to new customers, so our Monte Carlo
forecast and rule-based detectors replace them. The AWS architecture in the problem
statement is suggested, not mandatory.
Data is synthetic, with a documented set of planted inconsistencies. Not financial advice.
AWS status (update only when built)
Built: none yet.
Planned: S3 with KMS encryption, IAM least-privilege user, CloudTrail, Textract, Bedrock, SNS.
Stretch: EventBridge + Lambda, Glue + Athena, API Gateway + Lambda.
Roadmap only (not built, do not claim): AppFlow, Aurora, QuickSight, SageMaker, IAM Identity Center.