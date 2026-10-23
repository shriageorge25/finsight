import axios from "axios";
import { API_URL } from "../config";

// One shared axios instance so every component talks to the backend the same way.
export const client = axios.create({ baseURL: API_URL, timeout: 15000 });