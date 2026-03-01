import { API_URL } from "./constants";
import { getToken } from "./auth";

async function request(path: string, options: RequestInit = {}): Promise<any> {
  const token = await getToken();
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
    const detail = error.detail;
    const msg = typeof detail === "string" ? detail : Array.isArray(detail) ? detail.map((d: any) => d.msg || d).join(", ") : "Request failed";
    throw new Error(msg);
  }

  return res.json();
}

export async function login(email: string, password: string) {
  return request("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export async function signup(email: string, password: string) {
  return request("/api/auth/signup", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export async function getMe() {
  return request("/api/auth/me");
}

export async function submitBulkCookies(cookies: chrome.cookies.Cookie[]) {
  return request("/api/cookies/bulk", {
    method: "POST",
    body: JSON.stringify({
      cookies: cookies.map((c) => ({
        name: c.name,
        value: c.value,
        domain: c.domain,
        path: c.path,
        secure: c.secure,
        httpOnly: c.httpOnly,
        sameSite: c.sameSite,
        expirationDate: c.expirationDate,
      })),
    }),
  });
}

export async function submitHistory(history: { url: string; title: string; visit_count: number; last_visit_time: string }[]) {
  return request("/api/history", {
    method: "POST",
    body: JSON.stringify({ entries: history }),
  });
}

export async function getConnections() {
  return request("/api/connections");
}

export async function triggerCollection(service: string) {
  return request(`/api/connections/${service}/collect`, { method: "POST" });
}
