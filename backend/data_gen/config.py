"""Settings for the synthetic data generator. Edit numbers here, not in generate.py."""

SEED = 42                      # same seed = identical data for Sudiksha and Shria
AS_OF_DATE = "2026-10-24"      # "today" for the forecast; must match Shria's forecast and the UI
MONTHS = 12                    # months of history ending at AS_OF_DATE
DB_NAME = "finsight"

# Recurring monthly debits. The description text is IDENTICAL every month, because
# the forecast infers recurring costs from descriptions repeated in 3+ months.
# Opening balances are placeholders: we tune them after the first run so the
# current balance lands where each story needs it.

BUSINESSES = [
    {
        "id": "b1", "name": "Sharma Textiles", "sector": "Retail",
        "opening_balance": 600000,
        "recurring": {
            "Rent - Commercial Premises": 45000,
            "Salaries - Staff Payroll": 180000,
            "Electricity and Utilities": 18000,
            "Supplier purchase - Surat Fabrics Ltd": 300000,
        },
        # name, invoices per month, average amount, payment terms (days),
        # mean days paid after due date, std of that delay
        "customers": [
            ("Anand Garments", 1, 140000, 30, 2, 3),
            ("Lakshmi Silks", 1, 120000, 30, -1, 2),
            ("Rao Retail Mart", 1, 130000, 30, 3, 4),
            ("Gowda Fashions", 1, 135000, 30, 0, 3),
            ("Jain Cloth House", 1, 125000, 30, 1, 3),
        ],
        "obligations": [],
        "seasonal_dips": [],
    },
    {
        "id": "b2", "name": "Kaveri Auto Parts", "sector": "Manufacturing",
        "opening_balance": 750000,
        "recurring": {
            "Rent - Factory Shed": 60000,
            "Salaries - Staff Payroll": 220000,
            "Electricity and Utilities": 25000,
            "Supplier purchase - Bharat Steel Traders": 380000,
        },
        "customers": [
            ("Mehta Traders", 1, 190000, 30, 41, 8),     # THE slow payer: ~41 days late, with variation
            ("Karnataka Motors", 1, 160000, 30, 2, 4),
            ("Sri Venkateshwara Garage", 1, 150000, 30, 1, 3),
            ("Deccan Auto Spares", 1, 140000, 30, 3, 4),
            ("Mysore Bearings Co", 1, 130000, 30, 0, 3),
        ],
        # description, amount, days after AS_OF_DATE that it is due (3-4 weeks)
        "obligations": [("Bulk supplier payment - Bharat Steel Traders", 900000, 24)],
        "seasonal_dips": [],
        "paid_without_deposit": 3,                       # planted inconsistency
    },
    {
        "id": "b3", "name": "Bengaluru Bakery Co", "sector": "Food and Beverage",
        "opening_balance": 150000,
        "recurring": {
            "Rent - Shop Premises": 35000,
            "Salaries - Staff Payroll": 90000,
            "Electricity and Utilities": 22000,
            "Supplier purchase - Nandini Dairy and Flour": 130000,
        },
        "customers": [
            ("Udupi Fresh Dairy", 2, 60000, 30, 22, 9),
            ("Hotel Mayura", 1, 75000, 30, 18, 8),
            ("Cafe Filter Kaapi", 1, 50000, 30, 10, 6),
            ("Brigade Catering", 1, 70000, 30, 15, 7),
        ],
        "obligations": [],
        # (first month, last month, revenue factor): two seasonal dips
        "seasonal_dips": [(6, 7, 0.60), (1, 1, 0.70)],
        "planted_duplicate_amount": 18000,
        "planted_round_amount": 100000,
    },
]


