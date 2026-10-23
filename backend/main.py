from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import analytics_bridge
import db

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