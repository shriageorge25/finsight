// The ONE place for the API address and the mock toggle.
export const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

// true  = use JSON files in src/mock (works with no backend)
// false = call Shria's real FastAPI endpoints
export const USE_MOCK = true;