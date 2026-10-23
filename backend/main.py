from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

import analytics_bridge
import db
import forecast as fc

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


@app.get("/businesses")
def businesses():
    return db.list_businesses()

def load(business_id):
    """Fetch one business's data, or return a clean 404 if it doesn't exist."""
    data = db.get_data(business_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Unknown business")
    return data


@app.get("/businesses/{business_id}/forecast")
def get_forecast(business_id: str, days: int = Query(90, ge=1, le=365)):
    business, transactions, invoices, obligations = load(business_id)
    return fc.simulate(business, transactions, invoices, obligations, days=days)