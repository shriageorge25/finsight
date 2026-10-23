import { useEffect, useState, useCallback } from "react";
import { api, errorMessage } from "../api/api";
import { MOCK } from "../config";
import { useBusiness } from "../context/business";
import { inr } from "../utils/format";
import StateBox from "./StateBox";

export default function Overdue() {
    const { selectedId } = useBusiness();
    const [items, setItems] = useState(null);
    const [error, setError] = useState(null);

    const load = useCallback(() => {
        if (!selectedId) return () => { };
        let cancelled = false;
        setItems(null);
        setError(null);
        api.overdue(selectedId)
            .then((d) => !cancelled && setItems(d))
            .catch((e) => !cancelled && setError(errorMessage(e)));
        return () => { cancelled = true; };
    }, [selectedId]);

    useEffect(() => load(), [load]);

    if (!selectedId) return <StateBox kind="empty" message="Pick a business." />;

    const total = items ? items.reduce((s, i) => s + i.amount, 0) : 0;

    return (
        <section>
            <h2>
                Overdue invoices {MOCK.overdue && <span className="badge">Demo mode</span>}
            </h2>
            {error && <StateBox kind="error" message={error} onRetry={load} />}
            {!error && items === null && <StateBox kind="loading" />}
            {!error && items?.length === 0 && (
                <StateBox kind="empty" message="No overdue invoices for this business." />
            )}
            {!error && items?.length > 0 && (
                <>
                    <p>
                        {items.length} overdue, {inr(total)} in total
                    </p>
                    <ul className="list">
                        {items.map((i) => (
                            <li key={i.invoice_id}>
                                <strong>{i.customer}</strong>: {i.invoice_id}, {inr(i.amount)},{" "}
                                {i.days_overdue} days overdue
                            </li>
                        ))}
                    </ul>
                </>
            )}
        </section>
    );
}