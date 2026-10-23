"""Synthetic stub data for development only.

Shaped exactly like the shared contract in README.md. db.get_data() falls back
to this until the real generator has seeded MongoDB. All values are made up.
"""

BUSINESS_ID = "stub-1"


def _tx(date, description, amount, tx_type, category):
    return {
        "business_id": BUSINESS_ID,
        "date": date,
        "description": description,
        "amount": amount,
        "type": tx_type,
        "category": category,
    }


def _inv(inv_id, customer, amount, issue_date, due_date, paid_date):
    return {
        "_id": inv_id,
        "business_id": BUSINESS_ID,
        "customer": customer,
        "amount": amount,
        "issue_date": issue_date,
        "due_date": due_date,
        "paid_date": paid_date,
    }


def get_stub_data():
    """Return a fresh dict each call, so tests can change values safely."""
    business = {
        "_id": BUSINESS_ID,
        "name": "Stub Textiles (synthetic)",
        "sector": "Textile retail",
        "opening_balance": 500000,
        "as_of_date": "2026-10-24",
    }

    transactions = []
    for month, receipts in [
        ("2026-07", 200000),
        ("2026-08", 220000),
        ("2026-09", 215000),
        ("2026-10", 230000),
    ]:
        transactions.append(_tx(f"{month}-01", "Salaries", 120000, "debit", "payroll"))
        transactions.append(_tx(f"{month}-05", "Rent", 45000, "debit", "rent"))
        transactions.append(_tx(f"{month}-15", "Customer receipts", receipts, "credit", "sales"))

    invoices = [
        # paid history (gives each customer a delay pattern)
        _inv("INV-001", "Sharma Traders", 60000, "2026-06-10", "2026-07-10", "2026-07-14"),
        _inv("INV-002", "Sharma Traders", 55000, "2026-07-10", "2026-08-10", "2026-08-12"),
        _inv("INV-003", "Sharma Traders", 58000, "2026-08-10", "2026-09-10", "2026-09-17"),
        _inv("INV-004", "Kaveri Retail", 80000, "2026-06-20", "2026-07-20", "2026-08-09"),
        _inv("INV-005", "Kaveri Retail", 75000, "2026-07-20", "2026-08-20", "2026-09-12"),
        _inv("INV-006", "Kaveri Retail", 78000, "2026-08-20", "2026-09-20", "2026-10-12"),
        _inv("INV-007", "Metro Mart", 40000, "2026-06-25", "2026-07-25", "2026-07-25"),
        _inv("INV-008", "Metro Mart", 42000, "2026-07-25", "2026-08-25", "2026-08-27"),
        # unpaid (these drive the forecast)
        _inv("INV-009", "Kaveri Retail", 70000, "2026-09-05", "2026-10-05", None),
        _inv("INV-010", "Sharma Traders", 50000, "2026-10-01", "2026-11-05", None),
        _inv("INV-011", "Metro Mart", 30000, "2026-10-10", "2026-11-15", None),
    ]

    obligations = [
        {
            "business_id": BUSINESS_ID,
            "description": "GST payment",
            "amount": 50000,
            "due_date": "2026-11-20",
        }
    ]

    return {
        "business": business,
        "transactions": transactions,
        "invoices": invoices,
        "obligations": obligations,
    }
# Module-level constants, because db.get_data() imports these names.
_DATA = get_stub_data()
BUSINESS = _DATA["business"]
TRANSACTIONS = _DATA["transactions"]
INVOICES = _DATA["invoices"]
OBLIGATIONS = _DATA["obligations"]