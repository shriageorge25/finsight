export const inr = (n) => "₹" + Math.round(n).toLocaleString("en-IN");

// Green / amber / red for the 0-100 health score.
export const scoreTone = (s) => (s >= 70 ? "green" : s >= 40 ? "amber" : "red");

export const statusLabel = { healthy: "Healthy", watch: "Watch", at_risk: "At risk" };