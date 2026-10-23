import json

import llm

RULES = (
    "You draft a short, polite payment reminder from a small business owner to a customer. "
    "Use ONLY the facts in the JSON below. Never invent, estimate or recalculate an amount, date, invoice id or name. "
    "Amounts are already formatted, for example 'Rs. 195,617'; copy them exactly as given, and list each overdue invoice with its id, amount and days overdue. "
    "Address the customer by name, ask them to pay or to tell us when to expect payment, and thank them. "
    "Tone: friendly and professional. No threats, and no mention of penalties, interest or legal action. "
    "Plain text only, under 120 words. Sign off with 'Regards' followed by the business name from the facts."
)


def money(x):
    x = float(x)
    return f"Rs. {x:,.0f}" if x == int(x) else f"Rs. {x:,.2f}"


def build_facts(business, customer, invoices):
    return {
        "customer": customer,
        "business_name": business.get("name") or "the accounts team",
        "overdue_invoices": [dict(i, amount=money(i["amount"])) for i in invoices],
        "total_overdue": money(sum(i["amount"] for i in invoices)),
    }


def draft_reminder(business, customer, invoices):
    facts = build_facts(business, customer, invoices)
    prompt = RULES + "\n\nFACTS (JSON):\n" + json.dumps(facts, indent=1)
    return llm.generate(prompt).strip()
