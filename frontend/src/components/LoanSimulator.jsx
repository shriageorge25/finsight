import { useEffect, useState } from "react";
import { api, errorMessage } from "../api/api";
import { MOCK } from "../config";
import { useBusiness } from "../context/business";
import { inr } from "../utils/format";
import ForecastChart from "./ForecastChart";
import StateBox from "./StateBox";

function LoanForm({ id }) {
    const [amount, setAmount] = useState("500000");
    const [rate, setRate] = useState("12");
    const [tenure, setTenure] = useState("24");
    const [baseline, setBaseline] = useState(null);
    const [state, setState] = useState({ loading: false, result: null, error: "" });

    useEffect(() => {
        let cancelled = false;
        api.forecast(id).then((f) => !cancelled && setBaseline(f)).catch(() => { });
        return () => { cancelled = true; };
    }, [id]);

    const run = () => {
        const a = Number(amount), r = Number(rate), t = Number(tenure);
        if (!(a > 0)) return setState({ loading: false, result: null, error: "Amount must be more than 0." });
        if (!(r > 0 && r <= 100)) return setState({ loading: false, result: null, error: "Rate must be above 0 and at most 100 (annual %)." });
        if (!Number.isInteger(t) || t < 1 || t > 360) return setState({ loading: false, result: null, error: "Tenure must be a whole number from 1 to 360 months." });
        setState({ loading: true, result: null, error: "" });
        api.loanSimulate(id, { amount: a, rate: r, tenure_months: t })
            .then((result) => setState({ loading: false, result, error: "" }))
            .catch((e) => setState({ loading: false, result: null, error: errorMessage(e) }));
    };

    const { loading, result, error } = state;
    return (
        <section>
            <h2>Loan simulator {MOCK.loanSimulate && <span className="badge">Demo mode</span>}</h2>
            <div style={{ display: "flex", gap: 16, flexWrap: "wrap", marginBottom: 12 }}>
                <label>Amount (₹)<br /><input type="number" value={amount} onChange={(e) => setAmount(e.target.value)} /></label>
                <label>Annual rate (%)<br /><input type="number" value={rate} onChange={(e) => setRate(e.target.value)} /></label>
                <label>Tenure (months)<br /><input type="number" value={tenure} onChange={(e) => setTenure(e.target.value)} /></label>
            </div>
            <button onClick={run} disabled={loading}>{loading ? "Simulating…" : "Simulate loan"}</button>
            {loading && <StateBox kind="loading" message="Simulating…" />}
            {error && <StateBox kind="error" message={error} onRetry={run} />}
            {result && (
                <div>
                    <p>Monthly EMI: <strong>{inr(result.emi)}</strong></p>
                    {result.affordable ? (
                        <p>Affordable: no risk day in the next 90 days.</p>
                    ) : (
                        <p>
                            Not affordable: first risk day with the loan is {result.first_shortfall_date}
                            {result.baseline_first_shortfall_date
                                ? ` (without the loan: ${result.baseline_first_shortfall_date})`
                                : " (without the loan: no risk day)"}
                            . Worst-case shortfall: {inr(result.shortfall_amount)}.
                        </p>
                    )}
                    <p><small>Risk day = at least a 20% chance of a negative balance. Solid line: baseline. Dashed line: with the loan.</small></p>
                    {baseline && <ForecastChart forecast={baseline} stress={result.forecast_with_loan} />}
                </div>
            )}
        </section>
    );
}

export default function LoanSimulator() {
    const { selectedId } = useBusiness();
    if (!selectedId) return <StateBox kind="empty" message="Pick a business." />;
    return <LoanForm key={selectedId} id={selectedId} />;
}