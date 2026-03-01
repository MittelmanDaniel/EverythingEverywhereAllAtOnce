"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getAnalysis, getConnections, getMe, triggerCollection, refreshAnalysis } from "@/lib/api";

type PathNotTaken = {
  id: string;
  category: string;
  title: string;
  description: string;
  evidence_json: string;
  source_service: string;
  confidence: number;
  timeline_date: string | null;
};

type Connection = {
  service: string;
  status: string;
  last_collected_at: string | null;
};

const CATEGORY_STYLES: Record<string, { label: string; color: string; bg: string }> = {
  abandoned_project: { label: "Abandoned Project", color: "text-orange-400", bg: "bg-orange-500/10 border-orange-500/20" },
  forgotten_interest: { label: "Forgotten Interest", color: "text-purple-400", bg: "bg-purple-500/10 border-purple-500/20" },
  dormant_period: { label: "Quiet Period", color: "text-blue-400", bg: "bg-blue-500/10 border-blue-500/20" },
};

const SERVICE_ICONS: Record<string, string> = {
  github: "🐙",
  youtube: "▶️",
  goodreads: "📚",
};

export default function DashboardPage() {
  const router = useRouter();
  const [paths, setPaths] = useState<PathNotTaken[]>([]);
  const [connections, setConnections] = useState<Connection[]>([]);
  const [status, setStatus] = useState("pending");
  const [loading, setLoading] = useState(true);
  const [email, setEmail] = useState("");

  useEffect(() => {
    checkAuth();
  }, []);

  useEffect(() => {
    if (!email) return;
    fetchData();
    // Poll while collecting
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, [email]);

  async function checkAuth() {
    try {
      const user = await getMe();
      setEmail(user.email);
    } catch {
      router.push("/login");
    }
  }

  async function fetchData() {
    try {
      const [analysisData, connData] = await Promise.all([getAnalysis(), getConnections()]);
      setPaths(analysisData.paths);
      setStatus(analysisData.status);
      setConnections(connData.connections);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  async function handleCollect() {
    for (const conn of connections) {
      if (conn.status === "connected" || conn.status === "collected") {
        await triggerCollection(conn.service);
      }
    }
    fetchData();
  }

  async function handleRefresh() {
    await refreshAnalysis();
    fetchData();
  }

  function handleLogout() {
    localStorage.removeItem("token");
    router.push("/");
  }

  if (loading) {
    return (
      <main className="flex min-h-screen items-center justify-center">
        <p className="text-gray-500">Loading your paths...</p>
      </main>
    );
  }

  return (
    <main className="min-h-screen">
      {/* Header */}
      <header className="border-b border-gray-800 px-6 py-4">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <h1 className="text-lg font-semibold bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">
            Everything Everywhere
          </h1>
          <div className="flex items-center gap-4">
            <div className="flex gap-2">
              {connections.map((c) => (
                <span
                  key={c.service}
                  className={`text-xs px-2 py-1 rounded border ${
                    c.status === "collecting"
                      ? "border-yellow-500/30 text-yellow-400 bg-yellow-500/10"
                      : c.status === "collected"
                      ? "border-green-500/30 text-green-400 bg-green-500/10"
                      : c.status === "error"
                      ? "border-red-500/30 text-red-400 bg-red-500/10"
                      : "border-gray-700 text-gray-400"
                  }`}
                >
                  {SERVICE_ICONS[c.service]} {c.service}
                </span>
              ))}
            </div>
            <button
              onClick={handleLogout}
              className="text-xs text-gray-500 hover:text-gray-300"
            >
              Log out
            </button>
          </div>
        </div>
      </header>

      <div className="max-w-4xl mx-auto px-6 py-8">
        {/* Status banner */}
        {status === "collecting" && (
          <div className="mb-8 p-4 rounded-lg border border-yellow-500/20 bg-yellow-500/5 text-center">
            <p className="text-yellow-400 text-sm">
              Agents are exploring your accounts... This may take a few minutes.
            </p>
          </div>
        )}

        {status === "pending" && connections.length === 0 && (
          <div className="mb-8 p-4 rounded-lg border border-gray-800 bg-[#111] text-center">
            <p className="text-gray-400 mb-3">No accounts connected yet.</p>
            <button
              onClick={() => router.push("/onboarding")}
              className="px-4 py-2 bg-indigo-500 hover:bg-indigo-600 text-white rounded-lg text-sm"
            >
              Connect Accounts
            </button>
          </div>
        )}

        {connections.length > 0 && (
          <div className="mb-8 flex gap-3">
            <button
              onClick={handleCollect}
              className="px-4 py-2 border border-gray-700 hover:border-gray-500 text-gray-300 rounded-lg text-sm transition-colors"
            >
              Collect Data
            </button>
            <button
              onClick={handleRefresh}
              className="px-4 py-2 border border-gray-700 hover:border-gray-500 text-gray-300 rounded-lg text-sm transition-colors"
            >
              Re-analyze
            </button>
          </div>
        )}

        {/* Timeline */}
        {paths.length > 0 && (
          <div>
            <h2 className="text-xl font-bold mb-6">Paths Not Taken</h2>
            <div className="relative">
              {/* Timeline line */}
              <div className="absolute left-6 top-0 bottom-0 w-px bg-gray-800" />

              <div className="space-y-6">
                {paths.map((path) => {
                  const style = CATEGORY_STYLES[path.category] || CATEGORY_STYLES.forgotten_interest;
                  return (
                    <div key={path.id} className="relative pl-16">
                      {/* Timeline dot */}
                      <div className="absolute left-4 top-6 w-4 h-4 rounded-full border-2 border-gray-700 bg-[#0a0a0a]" />

                      <div className="border border-gray-800 rounded-lg p-5 bg-[#111] hover:border-gray-700 transition-colors">
                        <div className="flex items-start justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <span className="text-lg">{SERVICE_ICONS[path.source_service] || "🔍"}</span>
                            <span className={`text-xs px-2 py-0.5 rounded border ${style.bg} ${style.color}`}>
                              {style.label}
                            </span>
                          </div>
                          {path.timeline_date && (
                            <span className="text-xs text-gray-600">{path.timeline_date}</span>
                          )}
                        </div>
                        <h3 className="font-semibold mb-2">{path.title}</h3>
                        <p className="text-sm text-gray-400 leading-relaxed">{path.description}</p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}

        {paths.length === 0 && status === "ready" && (
          <div className="text-center py-20">
            <p className="text-gray-500 text-lg">No paths found yet.</p>
            <p className="text-gray-600 text-sm mt-2">Try collecting data from your connected services.</p>
          </div>
        )}
      </div>
    </main>
  );
}
