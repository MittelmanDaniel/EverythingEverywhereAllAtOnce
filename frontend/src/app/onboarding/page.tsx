"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { getConnections } from "@/lib/api";

const SERVICES = [
  { key: "github", name: "GitHub", icon: "🐙", desc: "Repos, stars, contributions" },
  { key: "youtube", name: "YouTube", icon: "▶️", desc: "Playlists, subscriptions" },
  { key: "goodreads", name: "Goodreads", icon: "📚", desc: "Reading lists, shelves" },
];

export default function OnboardingPage() {
  const router = useRouter();
  const [connections, setConnections] = useState<Record<string, string>>({});
  const [polling, setPolling] = useState(true);

  useEffect(() => {
    let active = true;
    async function poll() {
      while (active) {
        try {
          const data = await getConnections();
          const map: Record<string, string> = {};
          for (const c of data.connections) {
            map[c.service] = c.status;
          }
          setConnections(map);
        } catch {}
        await new Promise((r) => setTimeout(r, 3000));
      }
    }
    poll();
    return () => { active = false; };
  }, []);

  const connectedCount = Object.keys(connections).length;

  return (
    <main className="flex min-h-screen items-center justify-center px-6">
      <div className="w-full max-w-lg">
        <h1 className="text-2xl font-bold mb-2">Connect Your Accounts</h1>
        <p className="text-gray-400 mb-8 text-sm">
          Install the Chrome extension and connect your accounts to get started.
        </p>

        <div className="border border-gray-800 rounded-lg p-5 mb-6 bg-[#111]">
          <h2 className="font-semibold mb-2">Step 1: Install Extension</h2>
          <p className="text-sm text-gray-400 mb-3">
            Load the extension in Chrome:
          </p>
          <ol className="text-sm text-gray-500 list-decimal list-inside space-y-1">
            <li>Open <code className="text-gray-300">chrome://extensions</code></li>
            <li>Enable &quot;Developer mode&quot;</li>
            <li>Click &quot;Load unpacked&quot; → select the <code className="text-gray-300">extension/dist</code> folder</li>
          </ol>
        </div>

        <div className="border border-gray-800 rounded-lg p-5 mb-6 bg-[#111]">
          <h2 className="font-semibold mb-3">Step 2: Connect Services</h2>
          <p className="text-sm text-gray-400 mb-4">
            Log in to the extension popup and click &quot;Connect&quot; for each service.
          </p>
          <div className="space-y-3">
            {SERVICES.map((s) => (
              <div key={s.key} className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className="text-xl">{s.icon}</span>
                  <div>
                    <div className="text-sm font-medium">{s.name}</div>
                    <div className="text-xs text-gray-500">{s.desc}</div>
                  </div>
                </div>
                <span className={`text-xs px-2 py-1 rounded ${
                  connections[s.key]
                    ? "bg-green-500/10 text-green-400 border border-green-500/20"
                    : "bg-gray-800 text-gray-500"
                }`}>
                  {connections[s.key] ? "Connected" : "Waiting..."}
                </span>
              </div>
            ))}
          </div>
        </div>

        <button
          onClick={() => router.push("/dashboard")}
          disabled={connectedCount === 0}
          className="w-full py-3 bg-indigo-500 hover:bg-indigo-600 disabled:opacity-30 disabled:cursor-not-allowed text-white rounded-lg font-medium transition-colors"
        >
          {connectedCount > 0
            ? `Continue with ${connectedCount} service${connectedCount > 1 ? "s" : ""}`
            : "Connect at least one service to continue"}
        </button>
      </div>
    </main>
  );
}
