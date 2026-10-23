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