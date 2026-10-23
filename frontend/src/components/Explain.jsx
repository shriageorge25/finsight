import { useState, useRef, useEffect } from "react";
import { api, errorMessage } from "../api/api";
import { MOCK } from "../config";
import StateBox from "./StateBox";

function explainError(e) {
    const status = e?.response?.status;
    if (status === 404) return "Unknown business.";
    if (status === 503) return "The AI model failed to write the explanation. Try again.";
    return errorMessage(e);
}

export default function Explain({ id }) {
    const [state, setState] = useState({ loading: false, summary: null, error: null });
    const alive = useRef(true);

    useEffect(() => {
        alive.current = true;
        return () => { alive.current = false; };
    }, []);

    const run = () => {
        setState({ loading: true, summary: null, error: null });
        api.explain(id)
            .then((r) => alive.current && setState({ loading: false, summary: r.summary, error: null }))
            .catch((e) => alive.current && setState({ loading: false, summary: null, error: explainError(e) }));
    };

    const { loading, summary, error } = state;

    return (
        <>
            <h2>
                Explain this business {MOCK.explain && <span className="badge">Demo mode</span>}
            </h2>
            <button onClick={run} disabled={loading}>
                {loading ? "Thinking…" : summary ? "Explain again" : "Explain this business"}
            </button>
            {loading && <StateBox kind="loading" message="Writing the explanation…" />}
            {error && <StateBox kind="error" message={error} onRetry={run} />}
            {summary && (
                <div>
                    <p><span className="badge">AI-generated</span></p>
                    <p>{summary}</p>
                </div>
            )}
        </>
    );
}