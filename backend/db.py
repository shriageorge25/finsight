import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()
db = MongoClient(os.getenv("MONGODB_URI"))["finsight"]


def get_data(bid):
    """Returns (business, transactions, invoices, obligations) or None."""
    biz = db.businesses.find_one({"_id": bid})
    if biz:
        f = {"business_id": bid}
        return (biz,
                list(db.transactions.find(f, {"_id": 0})),
                list(db.invoices.find(f)),
                list(db.obligations.find(f, {"_id": 0})))
    import stub_data  # falls back to stub until Sudiksha's generator seeds the DB
    if bid == stub_data.BUSINESS["_id"]:
        return (stub_data.BUSINESS, stub_data.TRANSACTIONS,
                stub_data.INVOICES, stub_data.OBLIGATIONS)
    return None


def list_businesses():
    docs = list(db.businesses.find())
    if docs:
        return docs
    import stub_data
    return [stub_data.BUSINESS]