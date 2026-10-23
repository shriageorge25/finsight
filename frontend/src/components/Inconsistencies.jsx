import { useEffect, useState, useCallback } from "react";
import { api, errorMessage } from "../api/api";
import { MOCK } from "../config";
import { useBusiness } from "../context/business";
import StateBox from "./StateBox";

export default function Inconsistencies() {
    const { selectedId } = useBusiness();
    const [items, setItems] = useState(null);
    const [error, setError] = useState(null);

    const load = useCallback(() => {
        if (!selectedId) return () => { };
        let cancelled = false;
        setItems(null);
        setError(null);
        api.inconsistencies(selectedId)
            .then((d) => !cancelled && setItems(d))
            .catch((e) => !cancelled && setError(errorMessage(e)));
        return () => { cancelled = true; };
    }, [selectedId]);

    useEffect(() => load(), [load]);

    if (!selectedId) return <StateBox kind="empty" message="Pick a business." />;

    return (
        <section>
            <h2>
                Inconsistencies {MOCK.inconsistencies && <span className="badge">Demo mode</span>}
            </h2>
            {error && <StateBox kind="error" message={error} onRetry={load} />}
            {!error && items === null && <StateBox kind="loading" />}
            {!error && items?.length === 0 && (
                <StateBox kind="empty" message="No inconsistencies found for this business." />
            )}
            {!error && items?.length > 0 && (
                <ul className="list">
                    {items.map((i) => (
                        <li key={`${i.invoice_id}-${i.issue}`}>
                            <span className={`badge badge-${i.severity}`}>{i.severity}</span>{" "}
                            <strong>{i.invoice_id}</strong>: {i.issue}
                            <div>{i.reason}</div>
                        </li>
                    ))}
                </ul>
            )}
        </section>
    );
}