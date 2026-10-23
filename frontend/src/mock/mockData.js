// ===== MOCK DATA: fake numbers shaped like the README contract. NOT real forecast output. =====
import businesses from "./businesses.json";
import summary from "./summary.json";
import latePayers from "./late-payers.json";
import inconsistencies from "./inconsistencies.json";
import overdue from "./overdue-invoices.json";
import explain from "./explain.json";

const START = Date.UTC(2026, 9, 25); // 2026-10-25, the day after as_of_date

const PROFILES = {
    b1: { start: 1240000, drift: 3000, dipAt: null, dipSize: 0 },
    b2: { start: 640000, drift: 2000, dipAt: 24, dipSize: 900000 },
    b3: { start: 85000, drift: -1500, dipAt: null, dipSize: 0 },
};

function build({ start, drift, dipAt, dipSize }) {
    const f = { dates: [], expected: [], low: [], high: [], negative_probability: [] };
    for (let i = 0; i < 90; i++) {
        let v = start + drift * i;
        if (dipAt !== null && i >= dipAt) v -= dipSize;
        const band = 20000 + i * 2500;
        f.dates.push(new Date(START + i * 86400000).toISOString().slice(0, 10));
        f.expected.push(Math.round(v));
        f.low.push(Math.round(v - band));
        f.high.push(Math.round(v + band));
        f.negative_probability.push(Math.round(100 / (1 + Math.exp((v / band) * 2.5))) / 100);
    }
    return f;
}

function firstNegative(f) {
    const i = f.low.findIndex((v) => v < 0);
    return i === -1 ? null : f.dates[i];
}

export const mock = {
    businesses: () => businesses,
    summary: (id) => summary[id],
    forecast: (id) => build(PROFILES[id]),
    latePayers: (id) => latePayers[id],
    inconsistencies: (id) => inconsistencies[id],
    overdue: (id) => overdue[id],
    explain: (id) => explain[id],

    loanSimulate: (id, { amount, rate, tenure_months }) => {
        const r = rate / 12 / 100;
        const emi = r === 0 ? amount / tenure_months
            : (amount * r * Math.pow(1 + r, tenure_months)) / (Math.pow(1 + r, tenure_months) - 1);
        const p = PROFILES[id];
        const withLoan = build({ ...p, drift: p.drift - emi / 30 });
        const first = firstNegative(withLoan);
        return {
            emi: Math.round(emi),
            affordable: first === null,
            first_shortfall_date: first,
            shortfall_amount: first === null ? 0 : Math.round(-Math.min(...withLoan.low)),
            baseline_first_shortfall_date: firstNegative(build(p)),
            forecast_with_loan: withLoan,
        };
    },

    actionsSimulate: (id, { collect_invoice_ids }) => {
        const p = PROFILES[id];
        const pct = Math.min(100, collect_invoice_ids.length * 40);
        return { gap_closed_pct: pct, forecast_after: build({ ...p, dipSize: p.dipSize * (1 - pct / 100) }) };
    },

    stress: (id, { revenue_drop_pct = 0, delay_days = 0 } = {}) => {
        const p = PROFILES[id];
        const cut = p.drift > 0 ? (p.drift * revenue_drop_pct) / 100 : 0;
        return build({ ...p, drift: p.drift - cut - delay_days * 100 });
    },

    reminder: ({ customer }) => ({
        message: `[MOCK] Hello ${customer}, a gentle reminder that your invoice is overdue. Please share the payment date. Thank you.`,
    }),
};