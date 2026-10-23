// The ONE place for the API address and the mock/live switches.
export const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

// true = use src/mock data (no backend needed), false = call Shria's live endpoint.
// Flip each one to false only after Shria confirms that endpoint works.
export const MOCK = {
    businesses: false,
    summary: false,
    forecast: false,
    loanSimulate: false,
    latePayers: false,
    inconsistencies: false,
    overdue: false,
    actionsSimulate: true,
    stress: false,
    explain: false,
    reminders: false,
};