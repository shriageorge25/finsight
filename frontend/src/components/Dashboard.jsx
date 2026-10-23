import { useEffect, useState } from "react";
import { api, errorMessage } from "../api/api";
import { useBusiness } from "../context/business";
import { inr, scoreTone } from "../utils/format";
import StateBox from "./StateBox";
import StressPanel from "./StressPanel";

export default function Dashboard() {
    const { selected, selectedId } = useBusiness();
    const [result, setResult] = useState({ id: null, summary: null, forecast: null, error: "" });

    useEffect(() => {
        if (!selectedId) return;
        let cancelled = false;
        Promise.all([api.summary(selectedId), api.forecast(selectedId)])
            .then(([summary, forecast]) => { if (!cancelled) setResult({ id: selectedId, summary, forecast, error: "" }); })
            .catch((e) => { if (!cancelled) setResult({ id: selectedId, summary: null, forecast: null, error: errorMessage(e) }); });
        return () => { cancelled = true; };
    }, [selectedId]);

    if (!selectedId) return <StateBox kind="empty" message="Pick a business." />;
    if (result.id !== selectedId) return <StateBox kind="loading" />;
    if (result.error) return <StateBox kind="error" message={result.error} />;

    const { summary, forecast } = result;
    return (
        <>
            <h1>{selected?.name}</h1>
            <div className="grid">
                <div className="card">
                    <h2>Current balance</h2>
                    <div className="big">{inr(summary.balance)}</div>
                </div>
                <div className="card">
                    <h2>Health score</h2>
                    <div className={`big tone-${scoreTone(summary.health_score)}`}>{summary.health_score} / 100</div>
                </div>
            </div>
            <div className="card">
                <h2>Top warnings</h2>
                {summary.warnings.length === 0 ? (
                    <p>No warnings. Nothing needs attention right now.</p>
                ) : (
                    summary.warnings.map((w, i) => (
                        <div key={i} className={`warning ${w.severity}`}>
                            <strong>{w.type.replace(/_/g, " ")}</strong>
                            {w.week ? ` (from ${w.week})` : ""}: {w.reason}
                        </div>
                    ))
                )}
            </div>
            <div className="card">
                <h2>Cash forecast (90 days)</h2>
                <StressPanel key={selectedId} id={selectedId} forecast={forecast} />
            </div>
        </>
    );
}