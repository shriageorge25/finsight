"""Seed MongoDB (db 'finsight') from sample_data CSVs.
Dry run by default. Add --write to insert. Run from the repo root."""
import argparse
import csv
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))
from analytics import find_inconsistencies  # noqa: E402


def read(name):
    with open(ROOT / "sample_data" / name, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def build(bid):
    biz = [dict(r, opening_balance=float(r["opening_balance"]))
           for r in read("businesses.csv") if r["_id"] == bid]
    txns = [dict(r, amount=float(r["amount"]))
            for r in read("transactions.csv") if r["business_id"] == bid]
    invs = []
    for r in read("invoices.csv"):
        if r["business_id"] != bid:
            continue
        plain = r["_id"]
        invs.append({
            "_id": f"{bid}_{plain}", "invoice_id": plain, "business_id": bid,
            "customer": r["customer"], "amount": float(r["amount"]),
            "issue_date": r["issue_date"], "due_date": r["due_date"],
            "paid_date": r["paid_date"] or None,
        })
    obls = [dict(r, amount=float(r["amount"]))
            for r in read("obligations.csv") if r["business_id"] == bid]
    return biz, txns, invs, obls


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="b2")
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    bid = args.only

    biz, txns, invs, obls = build(bid)
    if not biz:
        sys.exit(f"No business {bid} in businesses.csv")
    print(f"[{bid}] businesses={len(biz)} transactions={len(txns)} "
          f"invoices={len(invs)} obligations={len(obls)}")
    print("sample invoice:", invs[0])
    flags = find_inconsistencies(txns, invs)
    print("detector on built docs:", [(f["invoice_id"], f["issue"]) for f in flags])

    if not args.write:
        print("DRY RUN: nothing written. Add --write to insert into Atlas.")
        return

    from dotenv import load_dotenv
    from pymongo import MongoClient
    load_dotenv(ROOT / "backend" / ".env")
    load_dotenv(ROOT / ".env")
    uri = os.getenv("MONGODB_URI")
    if not uri:
        sys.exit("MONGODB_URI not set (check your .env). Nothing written.")
    db = MongoClient(uri, serverSelectionTimeoutMS=5000)["finsight"]
    db.businesses.delete_one({"_id": bid})
    for col in ("transactions", "invoices", "obligations"):
        db[col].delete_many({"business_id": bid})
    db.businesses.insert_many(biz)
    db.transactions.insert_many(txns)
    db.invoices.insert_many(invs)
    if obls:
        db.obligations.insert_many(obls)
    print(f"WROTE {bid} to Atlas database 'finsight'.")


if __name__ == "__main__":
    main()