"""Loan Readiness Simulator (deterministic, no AI)."""
from forecast import simulate, first_risk_day

EMI_INTERVAL_DAYS = 30


def calculate_emi(amount: float, annual_rate_pct: float, tenure_months: int) -> int:
    """Fixed monthly instalment for a reducing-balance loan, rounded to whole rupees."""
    if amount <= 0 or tenure_months <= 0:
        raise ValueError("amount and tenure_months must be positive")
    if annual_rate_pct < 0:
        raise ValueError("rate cannot be negative")

    r = annual_rate_pct / 12 / 100  # monthly interest rate
    if r == 0:
        emi = amount / tenure_months
    else:
        factor = (1 + r) ** tenure_months
        emi = amount * r * factor / (factor - 1)
    return round(emi)


def emi_schedule(emi, tenure_months, days=90):
    """Cash leaving on each forecast day: one EMI every 30 days, the first 30 days
    after as_of_date. Index 0 is as_of_date + 1 day, so an EMI due on day d is at d - 1."""
    out = [0.0] * days
    for k in range(1, tenure_months + 1):
        day = EMI_INTERVAL_DAYS * k
        if day > days:
            break
        out[day - 1] += emi
    return out


def simulate_loan(business, transactions, invoices, obligations,
                  amount, annual_rate_pct, tenure_months, days=90):
    """Baseline vs loan scenario on the same random draws (same seed)."""
    emi = calculate_emi(amount, annual_rate_pct, tenure_months)
    baseline = simulate(business, transactions, invoices, obligations, days=days)
    with_loan = simulate(business, transactions, invoices, obligations, days=days,
                         extra_outflows=emi_schedule(emi, tenure_months, days))

    first = first_risk_day(with_loan)  # risk day: negative_probability >= 0.20
    affordable = first is None
    # worst case = 10th-percentile line at its lowest point, only if not affordable
    shortfall = 0 if affordable else round(max(0.0, -min(with_loan["low"])))
    return {
        "emi": emi,
        "affordable": affordable,
        "first_shortfall_date": first,
        "shortfall_amount": shortfall,
        "baseline_first_shortfall_date": first_risk_day(baseline),
        "forecast_with_loan": with_loan,
    }