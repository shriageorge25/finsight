import { useEffect, useState } from "react";
import { api, errorMessage } from "../api/api";
import { BusinessContext } from "./business";

export default function BusinessProvider({ children }) {
    const [businesses, setBusinesses] = useState([]);
    const [selectedId, setSelectedId] = useState(null);
    const [status, setStatus] = useState("loading"); // loading | ready | error
    const [error, setError] = useState("");
    const [attempt, setAttempt] = useState(0);

    useEffect(() => {
        let cancelled = false;
        api
            .businesses()
            .then((list) => {
                if (cancelled) return;
                setBusinesses(list);
                setSelectedId((cur) => cur ?? list[0]?.id ?? null);
                setStatus("ready");
            })
            .catch((e) => {
                if (cancelled) return;
                setError(errorMessage(e));
                setStatus("error");
            });
        return () => {
            cancelled = true;
        };
    }, [attempt]);

    const retry = () => {
        setStatus("loading");
        setAttempt((a) => a + 1);
    };

    const selected = businesses.find((b) => b.id === selectedId) || null;

    return (
        <BusinessContext.Provider
            value={{ businesses, selectedId, selected, setSelectedId, status, error, retry }}
        >
            {children}
        </BusinessContext.Provider>
    );
}