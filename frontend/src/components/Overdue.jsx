import { useEffect, useState, useCallback } from "react";
import { api, errorMessage } from "../api/api";
import { MOCK } from "../config";
import { useBusiness } from "../context/business";
import { inr } from "../utils/format";
import StateBox from "./StateBox";

function reminderError(e) {
    const detail = e?.response?.data?.detail;
    if (e?.response?.status === 404) return detail || "No overdue invoices for this customer.";
    if (e?.response?.status === 503) return "The AI model failed to draft the reminder. Try again.";
    return errorMessage(e);
}

export default function Overdue() {
    const { selectedId } = useBusiness();
    const [items, setItems] = useState(null);
    const [error, setError] = useState(null);
    // drafts[customer] = { loading, message, error }
    const [drafts, setDrafts] = useState({});

    const load = useCallback(() => {
        if (!selectedId) return () => { };
        let cancelled = false;
        setItems(null);
        setError(null);
        setDrafts({});
        api.overdue(selectedId)
            .then((d) => !cancelled && setItems(d))
            .catch((e) => !cancelled && setError(errorMessage(e)));
        return () => { cancelled = true; };
    }, [selectedId]);

    useEffect(() => load(), [load]);

    const draft = (customer) => {
        const id = selectedId;
        setDrafts((d) => ({ ...d, [customer]: { loading: true } }));
        api.reminders(id, { customer })
            .then((r) => setDrafts((d) => ({ ...d, [customer]: { message: r.message } })))
            .catch((e) => setDrafts((d) => ({ ...d, [customer]: { error: reminderError(e) } })));
    };

    if (!selectedId) return <StateBox kind="empty" message="Pick a business." />;

    const total = items ? items.reduce((s, i) => s + i.amount, 0) : 0;
    const groups = {};
    (items || []).forEach((i) => { (groups[i.customer] ||= []).push(i); });

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
                    <p>{items.length} overdue, {inr(total)} in total</p>
                    {Object.entries(groups).map(([customer, rows]) => {
                        const d = drafts[customer] || {};
                        return (
                            <div key={customer} style={{ marginBottom: "1.25rem" }}>
                                <strong>{customer}</strong>
                                <ul className="list">
                                    {rows.map((i) => (
                                        <li key={i.invoice_id}>
                                            {i.invoice_id}, {inr(i.amount)}, {i.days_overdue} days overdue
                                        </li>
                                    ))}
                                </ul>
                                <button onClick={() => draft(customer)} disabled={d.loading}>
                                    {d.loading ? "Drafting…" : d.message ? "Redraft" : "Draft reminder"}
                                </button>
                                {d.loading && <StateBox kind="loading" message="Drafting reminder…" />}
                                {d.error && (
                                    <StateBox kind="error" message={d.error} onRetry={() => draft(customer)} />
                                )}
                                {d.message && (
                                    <div>
                                        <p>
                                            <span className="badge">Draft for owner review</span>{" "}
                                            {MOCK.reminders && <span className="badge">Demo mode</span>}{" "}
                                            Nothing has been sent.
                                        </p>
                                        <pre style={{ whiteSpace: "pre-wrap", fontFamily: "inherit" }}>{d.message}</pre>
                                        <button onClick={() => navigator.clipboard.writeText(d.message)}>Copy</button>
                                    </div>
                                )}
                            </div>
                        );
                    })}
                </>
            )}
        </section>
    );
}