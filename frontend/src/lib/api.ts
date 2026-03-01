const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function apiFetch(path: string, options: RequestInit = {}) {
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_URL}${path}`, { ...options, headers });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || "Request failed");
  }

  return res.json();
}

export async function login(email: string, password: string) {
  const data = await apiFetch("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  localStorage.setItem("token", data.access_token);
  return data;
}

export async function signup(email: string, password: string) {
  const data = await apiFetch("/api/auth/signup", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  localStorage.setItem("token", data.access_token);
  return data;
}

export async function getMe() {
  return apiFetch("/api/auth/me");
}

export async function getConnections() {
  return apiFetch("/api/connections");
}

export async function triggerCollection(service: string) {
  return apiFetch(`/api/connections/${service}/collect`, { method: "POST" });
}

export async function getAnalysis() {
  return apiFetch("/api/analysis");
}

export async function refreshAnalysis() {
  return apiFetch("/api/analysis/refresh", { method: "POST" });
}
