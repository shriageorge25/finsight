import { useEffect, useState } from "react";
import { api, errorMessage } from "../api/api";
import { useBusiness } from "../context/business";
import { inr, scoreTone } from "../utils/format";
import StateBox from "./StateBox";

export default function Dashboard() {
    const { selected, selectedId } = useBusiness();
    const [result, setResult] = useState({ id: null, summary: null, error: "" });

    useEffect(() => {
        if (!selectedId) return;
        let cancelled = false;
        api
            .summary(selectedId)
            .then((summary) => { if (!cancelled) setResult({ id: selectedId, summary, error: "" }); })
            .catch((e) => { if (!cancelled) setResult({ id: selectedId, summary: null, error: errorMessage(e) }); });
        return () => { cancelled = true; };
    }, [selectedId]);

    if (!selectedId) return <StateBox kind="empty" message="Pick a business." />;
    if (result.id !== selectedId) return <StateBox kind="loading" />;
    if (result.error) return <StateBox kind="error" message={result.error} />;

    const { summary } = result;
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
                            <strong>{w.week ?? "No specific date"}</strong>: {w.reason}
                        </div>
                    ))
                )}
            </div>
            <StateBox kind="empty" message="Forecast chart goes here (built after the data generator)." />
        </>
    );
}