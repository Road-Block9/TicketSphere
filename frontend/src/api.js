/**
 * Central API Client for Flask Backend
 * Communicates with Flask REST endpoints (default: http://127.0.0.1:5000)
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:5000";

async function request(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`;
  try {
    const response = await fetch(url, options);
    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
      const errorMsg = data.message || `Request failed with status ${response.status}`;
      throw new Error(errorMsg);
    }
    return data;
  } catch (err) {
    if (err.name === "TypeError" && err.message.includes("fetch")) {
      throw new Error(
        `Unable to connect to Flask API server at ${API_BASE_URL}. Ensure the backend is running via 'python src/flask_app.py'.`
      );
    }
    throw err;
  }
}

export const api = {
  // Health check
  async getHealth() {
    return request("/api/health");
  },

  // Analytics KPIs
  async getKpis() {
    return request("/api/analytics/kpis");
  },

  // Tickets list with query filters
  async getTickets(params = {}) {
    const query = new URLSearchParams();
    if (params.limit) query.append("limit", params.limit);
    if (params.status) query.append("status", params.status);
    if (params.category) query.append("category", params.category);
    if (params.priority) query.append("priority", params.priority);
    if (params.search) query.append("search", params.search);

    const queryString = query.toString();
    const endpoint = `/api/tickets${queryString ? `?${queryString}` : ""}`;
    return request(endpoint);
  },

  // CSV File upload ingestion
  async uploadCsv(file) {
    const formData = new FormData();
    formData.append("file", file);

    const url = `${API_BASE_URL}/api/ingest/csv`;
    try {
      const response = await fetch(url, {
        method: "POST",
        body: formData,
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(data.message || `Upload failed with status ${response.status}`);
      }
      return data;
    } catch (err) {
      if (err.name === "TypeError" && err.message.includes("fetch")) {
        throw new Error(`Unable to connect to Flask server at ${API_BASE_URL}.`);
      }
      throw err;
    }
  },

  // Trigger API Ingestion
  async triggerApiIngest(apiUrl, apiKey) {
    return request("/api/ingest/api", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ api_url: apiUrl, api_key: apiKey }),
    });
  },

  // GenAI Management Report
  async generateAiReport() {
    return request("/api/ai/report", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    });
  },
};
