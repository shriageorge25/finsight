import { client } from "./client";
import { MOCK, API_URL } from "../config";
import { mock } from "../mock/mockData";

// Mock replies arrive after a short delay so loading states are visible and testable.
const fake = (data, ms = 300) =>
    new Promise((resolve) => setTimeout(() => resolve(structuredClone(data)), ms));

const get = async (url, params) => (await client.get(url, { params })).data;
const post = async (url, body) => (await client.post(url, body)).data;

export const api = {
    businesses: () => (MOCK.businesses ? fake(mock.businesses()) : get("/businesses")),

    summary: (id) => (MOCK.summary ? fake(mock.summary(id)) : get(`/businesses/${id}/summary`)),

    forecast: (id, days = 90) =>
        MOCK.forecast ? fake(mock.forecast(id)) : get(`/businesses/${id}/forecast`, { days }),

    loanSimulate: (id, body) =>
        MOCK.loanSimulate ? fake(mock.loanSimulate(id, body), 150) : post(`/businesses/${id}/loan-simulate`, body),

    latePayers: (id) =>
        MOCK.latePayers ? fake(mock.latePayers(id)) : get(`/businesses/${id}/late-payers`),

    inconsistencies: (id) =>
        MOCK.inconsistencies ? fake(mock.inconsistencies(id)) : get(`/businesses/${id}/inconsistencies`),

    overdue: (id) =>
        MOCK.overdue ? fake(mock.overdue(id)) : get(`/businesses/${id}/overdue-invoices`),

    actionsSimulate: (id, body) =>
        MOCK.actionsSimulate ? fake(mock.actionsSimulate(id, body)) : post(`/businesses/${id}/actions/simulate`, body),

    stress: (id, body) =>
        MOCK.stress ? fake(mock.stress(id, body)) : post(`/businesses/${id}/stress`, body),

    explain: (id) => (MOCK.explain ? fake(mock.explain(id)) : get(`/businesses/${id}/explain`)),

    reminders: (id, body) =>
        MOCK.reminders ? fake(mock.reminder(body)) : post(`/businesses/${id}/reminders`, body),
};

// Turns any failure into a message the UI can show instead of a blank screen.
export function errorMessage(err) {
    if (err?.response) return `Backend returned an error (${err.response.status}).`;
    return `Backend not reachable at ${API_URL}. Is it running?`;
}