import { NavLink, Outlet } from "react-router-dom";
import { MOCK } from "../config";
import { useBusiness } from "../context/business";
import { statusLabel } from "../utils/format";
import StateBox from "./StateBox";

export default function Layout() {
    const { businesses, selected, selectedId, setSelectedId, status, error, retry } = useBusiness();
    const usingMock = Object.values(MOCK).some(Boolean);

    let body;
    if (status === "loading") body = <StateBox kind="loading" message="Loading businesses…" />;
    else if (status === "error") body = <StateBox kind="error" message={error} onRetry={retry} />;
    else if (businesses.length === 0) body = <StateBox kind="empty" message="No businesses found. Has the database been seeded?" />;
    else body = <Outlet />;

    return (
        <div className="app">
            <header className="header">
                <span className="brand">FinSight</span>
                <nav className="nav">
                    <NavLink to="/" end>Dashboard</NavLink>
                    <NavLink to="/loan">Loan Simulator</NavLink>
                    <NavLink to="/inconsistencies">Inconsistencies</NavLink>
                    <NavLink to="/overdue">Overdue</NavLink>
                    <NavLink to="/late-payers">Late payers</NavLink>
                </nav>
                <span className="spacer" />
                {usingMock && <span className="badge mock">Demo mode: some data is mock</span>}
                {selected && <span className={`badge ${selected.status}`}>{statusLabel[selected.status]}</span>}
                <label className="switcher">
                    <span>Business</span>
                    <select
                        value={selectedId ?? ""}
                        onChange={(e) => setSelectedId(e.target.value)}
                        disabled={businesses.length === 0}
                    >
                        {businesses.map((b) => (
                            <option key={b.id} value={b.id}>{b.name}</option>
                        ))}
                    </select>
                </label>
            </header>
            <main className="main">{body}</main>
            <footer className="footer">Synthetic data. Decision support, not financial advice.</footer>
        </div>
    );
}