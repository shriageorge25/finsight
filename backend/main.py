from datetime import date

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

import analytics_bridge
import db
import forecast as fc
import loan
import scoring

app = FastAPI(title="FinSight API")

app.add_middleware(  # lets Sudiksha's Vite dev server call this API
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    db.list_businesses()  # refreshes db.last_source
    return {
        "status": "ok",
        "data_source": db.last_source,  # "mongodb" or "stub"
        "analytics": "fallback" if analytics_bridge.USING_FALLBACK else "sudiksha",
    }


def load(business_id):
    """Fetch one business's data, or return a clean 404 if it doesn't exist."""
    data = db.get_data(business_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Unknown business")
    return data


class LoanRequest(BaseModel):
    amount: float = Field(gt=0)
    rate: float = Field(gt=0, le=100)  # annual percent
    tenure_months: int = Field(ge=1, le=360)


@app.get("/businesses")
def businesses():
    result = []
    for b in db.list_businesses():
        business, transactions, invoices, obligations = load(b["_id"])
        f = fc.simulate(business, transactions, invoices, obligations)
        summary = scoring.compute_summary(business, transactions, invoices, obligations, f)
        result.append({
            "id": b["_id"],
            "name": b["name"],
            "sector": b["sector"],
            "status": summary["status"],
        })
    return result


@app.get("/businesses/{business_id}/forecast")
def get_forecast(business_id: str, days: int = Query(90, ge=1, le=365)):
    business, transactions, invoices, obligations = load(business_id)
    return fc.simulate(business, transactions, invoices, obligations, days=days)


@app.get("/businesses/{business_id}/summary")
def get_summary(business_id: str):
    business, transactions, invoices, obligations = load(business_id)
    f = fc.simulate(business, transactions, invoices, obligations)
    return scoring.compute_summary(business, transactions, invoices, obligations, f)


@app.post("/businesses/{business_id}/loan-simulate")
def loan_simulate(business_id: str, req: LoanRequest):
    business, transactions, invoices, obligations = load(business_id)
    return loan.simulate_loan(
        business, transactions, invoices, obligations,
        amount=req.amount,
        annual_rate_pct=req.rate,
        tenure_months=req.tenure_months,
    )


@app.get("/businesses/{business_id}/late-payers")
def late_payers(business_id: str):
    business, transactions, invoices, obligations = load(business_id)
    return analytics_bridge.get_late_payers(invoices)


@app.get("/businesses/{business_id}/overdue-invoices")
def overdue_invoices(business_id: str):
    business, transactions, invoices, obligations = load(business_id)
    as_of = date.fromisoformat(business["as_of_date"])
    result = []
    for inv in invoices:
        if inv.get("paid_date") is None:
            days = (as_of - date.fromisoformat(inv["due_date"])).days
            if days > 0:
                result.append({
                    "invoice_id": inv.get("invoice_id") or inv["_id"],
                    "customer": inv["customer"],
                    "amount": inv["amount"],
                    "days_overdue": days,
                })
    return result


@app.get("/businesses/{business_id}/inconsistencies")
def inconsistencies(business_id: str):
    business, transactions, invoices, obligations = load(business_id)
    return analytics_bridge.find_inconsistencies(transactions, invoices)

class StressRequest(BaseModel):
    revenue_drop_pct: float = Field(0, ge=0, le=100)
    delay_days: int = Field(0, ge=0, le=365)


@app.post("/businesses/{business_id}/stress")
def stress(business_id: str, req: StressRequest):
    business, transactions, invoices, obligations = load(business_id)
    factor = 1 - req.revenue_drop_pct / 100
    scaled = [{**inv, "amount": inv["amount"] * factor} for inv in invoices]
    return fc.simulate(
        business, transactions, scaled, obligations,
        delay_shift=req.delay_days,
    )


class ActionRequest(BaseModel):
    collect_invoice_ids: list[str]


def _worst_shortfall(f):
    return max(0.0, -min(f["low"]))


@app.post("/businesses/{business_id}/actions/simulate")
def actions_simulate(business_id: str, req: ActionRequest):
    business, transactions, invoices, obligations = load(business_id)
    unpaid_ids = {inv.get("invoice_id") or inv.get("_id")
                  for inv in invoices if not inv.get("paid_date")}
    unknown = [i for i in req.collect_invoice_ids if i not in unpaid_ids]
    if unknown:
        raise HTTPException(status_code=422,
                            detail=f"Not unpaid invoices of this business: {unknown}")
    base = fc.simulate(business, transactions, invoices, obligations)
    after = fc.simulate(business, transactions, invoices, obligations,
                        collect_ids=set(req.collect_invoice_ids))
    before_gap = _worst_shortfall(base)
    after_gap = _worst_shortfall(after)
    if before_gap <= 0:
        pct = 0
    else:
        pct = max(0, min(100, round(100 * (before_gap - after_gap) / before_gap)))
    return {"gap_closed_pct": pct, "forecast_after": after}

from statements import router as statements_router
app.include_router(statements_router)

import explain


@app.get("/businesses/{business_id}/explain")
def explain_business(business_id: str):
    summary = get_summary(business_id)
    try:
        text = explain.explain_summary(summary)
    except Exception:
        raise HTTPException(status_code=503, detail="The explanation service is unavailable")
    if not text:
        raise HTTPException(status_code=503, detail="The explanation service returned nothing")
    return {"summary": text}

import reminders


class ReminderRequest(BaseModel):
    customer: str = Field(min_length=1, max_length=100)


@app.post("/businesses/{business_id}/reminders")
def reminders_draft(business_id: str, req: ReminderRequest):
    business = load(business_id)[0]
    wanted = req.customer.strip().lower()
    mine = [i for i in overdue_invoices(business_id) if i["customer"].strip().lower() == wanted]
    if not mine:
        raise HTTPException(status_code=404, detail="No overdue invoices for this customer")
    try:
        text = reminders.draft_reminder(business, mine[0]["customer"], mine)
    except Exception:
        raise HTTPException(status_code=503, detail="The reminder service is unavailable")
    if not text:
        raise HTTPException(status_code=503, detail="The reminder service returned nothing")
    return {"message": text}
