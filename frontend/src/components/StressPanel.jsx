import { useEffect, useState } from "react";
import { api, errorMessage } from "../api/api";
import ForecastChart from "./ForecastChart";

// My own check: first day the EXPECTED line goes below zero.
const firstNegative = (f) => {
    const i = f.expected.findIndex((v) => v < 0);
    return i === -1 ? "none in 90 days" : f.dates[i];
};

// Shria's definition: first day with ANY chance of going negative.
// Returns null when the data has no negative_probability (the mock may not).
const firstRisk = (f) => {
    if (!f?.negative_probability) return null;
    const i = f.negative_probability.findIndex((p) => p > 0);
    return i === -1 ? "none in 90 days" : f.dates[i];
};

export default function StressPanel({ id, forecast }) {
    const [drop, setDrop] = useState(0);
    const [delay, setDelay] = useState(0);
    const [stress, setStress] = useState(null);
    const [error, setError] = useState("");
    const active = drop > 0 || delay > 0;

    useEffect(() => {
        if (!active) return;
        let cancelled = false;
        const timer = setTimeout(() => {
            api
                .stress(id, { revenue_drop_pct: drop, delay_days: delay })
                .then((s) => { if (!cancelled) { setStress(s); setError(""); } })
                .catch((e) => { if (!cancelled) setError(errorMessage(e)); });
        }, 250);
        return () => { cancelled = true; clearTimeout(timer); };
    }, [id, drop, delay, active]);

    const shown = active && stress ? stress : null;
    const risk = shown ? firstRisk(shown) : null;

    return (
        <div>
            <div style={{ display: "flex", gap: 24, flexWrap: "wrap", marginBottom: 12 }}>
                <label>
                    Revenue drop: {drop}%
                    <br />
                    <input type="range" min="0" max="50" step="5" value={drop} onChange={(e) => setDrop(Number(e.target.value))} />
                </label>
                <label>
                    Payment delay: {delay} days
                    <br />
                    <input type="range" min="0" max="60" step="5" value={delay} onChange={(e) => setDelay(Number(e.target.value))} />
                </label>
            </div>
            {active && error && <p role="alert">{error}</p>}
            <ForecastChart forecast={forecast} stress={shown} />
            <p>
                Expected balance first goes below zero: {firstNegative(forecast)}
                {shown ? ` (baseline), ${firstNegative(shown)} (stressed)` : ""}
            </p>
            {risk && (
                <p>First day with any chance of a shortfall (stressed): {risk}</p>
            )}
        </div>
    );
}