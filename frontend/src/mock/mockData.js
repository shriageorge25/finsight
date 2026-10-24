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

// Same shape as the real GET /businesses/{id}/invoices?unpaid=true.
// b2 copies the real response. b1 and b3 are made-up demo rows (my choice, not from the backend).
const UNPAID = {
    b1: [
        { invoice_id: "inv_demo_1", customer: "Jain Cloth House", amount: 120000, due_date: "2026-10-20", days_overdue: 4 },
        { invoice_id: "inv_demo_2", customer: "Rao Retail Mart", amount: 95000, due_date: "2026-11-05", days_overdue: -12 },
    ],
    b2: [
        { invoice_id: "inv_54", customer: "Mehta Traders", amount: 195617, due_date: "2026-09-12", days_overdue: 42 },
        { invoice_id: "inv_59", customer: "Mehta Traders", amount: 176515, due_date: "2026-10-11", days_overdue: 13 },
        { invoice_id: "inv_63", customer: "Karnataka Motors", amount: 188835, due_date: "2026-11-02", days_overdue: -9 },
        { invoice_id: "inv_64", customer: "Mehta Traders", amount: 182315, due_date: "2026-11-11", days_overdue: -18 },
        { invoice_id: "inv_65", customer: "Mysore Bearings Co", amount: 135361, due_date: "2026-11-13", days_overdue: -20 },
        { invoice_id: "inv_66", customer: "Sri Venkateshwara Garage", amount: 136136, due_date: "2026-11-13", days_overdue: -20 },
        { invoice_id: "inv_67", customer: "Deccan Auto Spares", amount: 164527, due_date: "2026-11-18", days_overdue: -25 },
    ],
    b3: [
        { invoice_id: "inv_demo_3", customer: "Udupi Fresh Dairy", amount: 150000, due_date: "2026-10-10", days_overdue: 14 },
        { invoice_id: "inv_demo_4", customer: "Demo Caterers", amount: 80000, due_date: "2026-11-08", days_overdue: -15 },
    ],
};

export const mock = {
    businesses: () => businesses,
    summary: (id) => summary[id],
    forecast: (id) => build(PROFILES[id]),
    latePayers: (id) => latePayers[id],
    inconsistencies: (id) => inconsistencies[id],
    overdue: (id) => overdue[id],
    unpaidInvoices: (id) => UNPAID[id],
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