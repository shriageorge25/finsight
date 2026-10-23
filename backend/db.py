import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

last_source = "stub"  # "mongodb" or "stub": set by the most recent data call

db = None
try:
    db = MongoClient(os.getenv("MONGODB_URI"), serverSelectionTimeoutMS=3000)["finsight"]
except Exception as e:  # e.g. DNS failure while resolving the cluster address
    print(f"DB_UNAVAILABLE at startup: {type(e).__name__}")  # type only, never the URI


def get_data(bid):
    """Returns (business, transactions, invoices, obligations) or None."""
    global last_source
    if db is not None:
        try:
            biz = db.businesses.find_one({"_id": bid})
            if biz:
                f = {"business_id": bid}
                result = (biz,
                          list(db.transactions.find(f, {"_id": 0})),
                          list(db.invoices.find(f)),
                          list(db.obligations.find(f, {"_id": 0})))
                last_source = "mongodb"
                return result
        except Exception as e:
            print(f"DB_UNAVAILABLE: {type(e).__name__}; using stub data")
    import stub_data  # falls back to stub until Sudiksha's generator seeds the DB
    if bid == stub_data.BUSINESS["_id"]:
        last_source = "stub"
        return (stub_data.BUSINESS, stub_data.TRANSACTIONS,
                stub_data.INVOICES, stub_data.OBLIGATIONS)
    return None


def list_businesses():
    global last_source
    if db is not None:
        try:
            docs = list(db.businesses.find())
            if docs:
                last_source = "mongodb"
                return docs
        except Exception as e:
            print(f"DB_UNAVAILABLE: {type(e).__name__}; using stub data")
    import stub_data
    last_source = "stub"
    return [stub_data.BUSINESS]