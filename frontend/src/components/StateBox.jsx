export default function StateBox({ kind = "empty", message, onRetry }) {
    const text = message || (kind === "loading" ? "Loading…" : "Nothing to show yet.");
    return (
        <div className={`state state-${kind}`} role={kind === "error" ? "alert" : "status"}>
            {kind === "loading" && <div className="spinner" />}
            <p>{text}</p>
            {kind === "error" && onRetry && <button onClick={onRetry}>Try again</button>}
        </div>
    );
}