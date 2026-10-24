import { useEffect, useState, useCallback } from "react";
import { api, errorMessage } from "../api/api";
import { MOCK } from "../config";
import { useBusiness } from "../context/business";
import { inr } from "../utils/format";
import StateBox from "./StateBox";

export default function LatePayers() {
    const { selectedId } = useBusiness();
    const [items, setItems] = useState(null);
    const [error, setError] = useState(null);

    const load = useCallback(() => {
        if (!selectedId) return () => { };
        let cancelled = false;
        setItems(null);
        setError(null);
        api.latePayers(selectedId)
            .then((d) => !cancelled && setItems(d))
            .catch((e) => !cancelled && setError(errorMessage(e)));
        return () => { cancelled = true; };
    }, [selectedId]);

    useEffect(() => load(), [load]);

    if (!selectedId) return <StateBox kind="empty" message="Pick a business." />;

    return (
        <section>
            <h2>
                Late payers {MOCK.latePayers && <span className="badge">Demo mode</span>}
            </h2>
            {error && <StateBox kind="error" message={error} onRetry={load} />}
            {!error && items === null && <StateBox kind="loading" />}
            {!error && items?.length === 0 && (
                <StateBox kind="empty" message="No late payers for this business." />
            )}
            {!error && items?.length > 0 && (
                <ul className="list">
                    {items.map((p) => (
                        <li key={p.customer}>
                            <strong>{p.customer}</strong>: pays about{" "}
                            {Math.round(p.avg_delay_days)} days late, {inr(p.amount_at_risk)} at risk
                        </li>
                    ))}
                </ul>
            )}
        </section>
    );
}