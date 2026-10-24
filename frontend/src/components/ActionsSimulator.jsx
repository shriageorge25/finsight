import { useEffect, useState, useCallback } from "react";
import { api, errorMessage } from "../api/api";
import { MOCK } from "../config";
import { useBusiness } from "../context/business";
import { inr } from "../utils/format";
import StateBox from "./StateBox";

// The backend sends a useful message (e.g. "Not unpaid invoices of this business: [...]") in detail.
function simulateError(e) {
    const detail = e?.response?.data?.detail;
    if (typeof detail === "string") return detail;
    return errorMessage(e);
}

function dueText(days) {
    if (days > 0) return `${days} days overdue`;
    if (days < 0) return `due in ${-days} days`;
    return "due today";
}

export default function ActionsSimulator() {
    const { selectedId } = useBusiness();
    const [items, setItems] = useState(null);
    const [error, setError] = useState(null);
    const [picked, setPicked] = useState([]); // invoice_ids ticked by the user
    const [sim, setSim] = useState(null); // { id, loading, result, error }

    const load = useCallback(() => {
        if (!selectedId) return () => { };
        let cancelled = false;
        setItems(null);
        setError(null);
        setPicked([]);
        setSim(null);
        api.unpaidInvoices(selectedId)
            .then((d) => !cancelled && setItems(d))
            .catch((e) => !cancelled && setError(errorMessage(e)));
        return () => { cancelled = true; };
    }, [selectedId]);

    useEffect(() => load(), [load]);

    const toggle = (invoiceId) => {
        setSim(null); // old result no longer matches the selection
        setPicked((p) => (p.includes(invoiceId) ? p.filter((x) => x !== invoiceId) : [...p, invoiceId]));
    };

    const simulate = () => {
        const id = selectedId;
        setSim({ id, loading: true });
        api.actionsSimulate(id, { collect_invoice_ids: picked })
            .then((r) => setSim({ id, result: r }))
            .catch((e) => setSim({ id, error: simulateError(e) }));
    };

    if (!selectedId) return <StateBox kind="empty" message="Pick a business." />;

    const demo = MOCK.unpaidInvoices || MOCK.actionsSimulate;
    const s = sim && sim.id === selectedId ? sim : null;

    return (
        <section>
            <h2>
                What if we collect these? {demo && <span className="badge">Demo mode</span>}
            </h2>
            {error && <StateBox kind="error" message={error} onRetry={load} />}
            {!error && items === null && <StateBox kind="loading" />}
            {!error && items?.length === 0 && (
                <StateBox kind="empty" message="No unpaid invoices for this business." />
            )}
            {!error && items?.length > 0 && (
                <>
                    <p>Tick the invoices you could collect early, then simulate.</p>
                    <ul className="list">
                        {items.map((i) => (
                            <li key={i.invoice_id}>
                                <label>
                                    <input
                                        type="checkbox"
                                        checked={picked.includes(i.invoice_id)}
                                        onChange={() => toggle(i.invoice_id)}
                                    />{" "}
                                    {i.invoice_id}, {i.customer}, {inr(i.amount)}, {dueText(i.days_overdue)}
                                </label>
                            </li>
                        ))}
                    </ul>
                    <button onClick={simulate} disabled={picked.length === 0 || s?.loading}>
                        {s?.loading ? "Simulating…" : "Simulate collecting these"}
                    </button>
                    {s?.loading && <StateBox kind="loading" message="Simulating…" />}
                    {s?.error && <StateBox kind="error" message={s.error} onRetry={simulate} />}
                    {s?.result && (
                        <p>
                            Collecting these closes <strong>{s.result.gap_closed_pct}%</strong> of the
                            worst-case shortfall (the lowest point of the pessimistic forecast band).
                        </p>
                    )}
                </>
            )}
        </section>
    );
}