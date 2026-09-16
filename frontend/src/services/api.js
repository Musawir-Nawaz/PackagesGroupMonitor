const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

async function get(path, params = {}) {
  const url = new URL(`${API_BASE_URL}${path}`);
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      url.searchParams.set(key, value);
    }
  });
  const res = await fetch(url);
  if (!res.ok) throw new Error(`${path} failed: ${res.status}`);
  return res.json();
}

async function post(path, params = {}) {
  const url = new URL(`${API_BASE_URL}${path}`);
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      url.searchParams.set(key, value);
    }
  });
  const res = await fetch(url, { method: "POST" });
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(body?.detail || `${path} failed: ${res.status}`);
  }
  return res.json();
}

export const getHealth = () => get("/api/health");

export const getDashboardSummary = (period = "7d") => get("/api/dashboard/summary", { period });
export const getDashboardTrends = (period = "30d") => get("/api/dashboard/trends", { period });

export const getSentimentBreakdown = () => get("/api/sentiment");
export const getTopicBreakdown = () => get("/api/topics");

export const getComments = (filters = {}) => get("/api/comments", filters);
export const getComment = (id) => get(`/api/comments/${id}`);

export const getAlerts = (params = {}) => get("/api/alerts", params);
export const getAlert = (id) => get(`/api/alerts/${id}`);

export const runCollection = (platform) => post("/api/collection/run", { platform });
export const getCollectionStatus = (limit = 20) => get("/api/collection/status", { limit });
