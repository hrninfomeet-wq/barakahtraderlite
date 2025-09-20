"use client";

import { useEffect, useRef, useState } from "react";

const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

type Quote = {
  symbol: string;
  last_price?: number;
  timestamp?: string;
  error?: string;
};

export default function QuotesPage() {
  const [symbols, setSymbols] = useState("RELIANCE,TCS,NIFTY");
  const [quotes, setQuotes] = useState<Quote[]>([]);
  const [loading, setLoading] = useState(false);
  const [liveEnabled, setLiveEnabled] = useState<boolean | null>(null);
  const [message, setMessage] = useState<string>("");

  const [autoRefresh, setAutoRefresh] = useState<boolean>(false);
  const [intervalMs, setIntervalMs] = useState<number>(5000);
  const intervalRef = useRef<NodeJS.Timer | null>(null);

  async function fetchFlag() {
    try {
      const res = await fetch(`${backendUrl}/api/v1/system/config/live-data`);
      const data = await res.json();
      setLiveEnabled(Boolean(data.enabled));
    } catch {
      setMessage("Failed to read live-data flag");
    }
  }

  async function toggleFlag() {
    if (liveEnabled === null) return;
    try {
      const res = await fetch(`${backendUrl}/api/v1/system/config/live-data`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ provider: "upstox", enabled: !liveEnabled }),
      });
      const data = await res.json();
      setLiveEnabled(Boolean(data.enabled));
    } catch {
      setMessage("Failed to toggle live-data flag");
    }
  }

  async function fetchQuotes() {
    setLoading(true);
    setMessage("");
    try {
      const qs = encodeURIComponent(symbols);
      const res = await fetch(
        `${backendUrl}/api/v1/market-data/batch?symbols=${qs}`
      );
      const data = await res.json();
      const items: Quote[] = (data.symbols_returned || []).map((s: string) => {
        const md = data.data?.[s];
        return {
          symbol: s,
          last_price: md?.last_price,
          timestamp: md?.timestamp,
        };
      });

      // Include missing symbols with error
      const req = (data.symbols_requested || []) as string[];
      const ret = new Set<string>(data.symbols_returned || []);
      req.forEach((s) => {
        if (!ret.has(s)) items.push({ symbol: s, error: "no data" });
      });

      setQuotes(items);
    } catch (error: unknown) {
      setMessage("Failed to fetch quotes");
    } finally {
      setLoading(false);
    }
  }

  // Initialize: load flag and first quotes
  useEffect(() => {
    fetchFlag();
    // Do not auto-fetch quotes on mount to avoid flashing; user can click Fetch
  }, []);

  // Auto-refresh management
  useEffect(() => {
    if (autoRefresh) {
      if (intervalRef.current) clearInterval(intervalRef.current as unknown as number);
      const id = setInterval(() => {
        fetchQuotes();
      }, Math.max(1000, intervalMs));
      intervalRef.current = id as unknown as NodeJS.Timer;
      return () => {
        if (intervalRef.current) clearInterval(intervalRef.current as unknown as number);
        intervalRef.current = null;
      };
    }
    // If turning off auto-refresh
    if (intervalRef.current) {
      clearInterval(intervalRef.current as unknown as number);
      intervalRef.current = null;
    }
    return undefined;
  }, [autoRefresh, intervalMs, symbols]);

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <h1 className="text-xl font-semibold mb-4">Live Quotes (Paper Mode)</h1>

      <div className="mb-4 flex items-center gap-2">
        <button
          className="border rounded px-3 py-1"
          onClick={fetchFlag}
        >
          Check Live-Data Flag
        </button>
        {liveEnabled !== null && (
          <button className="border rounded px-3 py-1" onClick={toggleFlag}>
            {liveEnabled ? "Disable Live-Data" : "Enable Live-Data"}
          </button>
        )}
        {liveEnabled !== null && (
          <span className="text-sm ml-2">
            Status: {liveEnabled ? "Enabled" : "Disabled"}
          </span>
        )}
      </div>

      <div className="mb-4">
        <label className="block text-sm mb-1">Symbols (comma-separated)</label>
        <input
          className="border rounded px-3 py-2 w-full"
          value={symbols}
          onChange={(e) => setSymbols(e.target.value)}
          placeholder="RELIANCE,TCS,NIFTY"
        />
      </div>

      <div className="mb-4 flex items-center gap-3">
        <button
          className="border rounded px-4 py-2"
          onClick={fetchQuotes}
          disabled={loading}
        >
          {loading ? "Loading..." : "Fetch Quotes"}
        </button>
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={autoRefresh}
            onChange={(e) => setAutoRefresh(e.target.checked)}
          />
          Auto-refresh
        </label>
        <select
          className="border rounded px-2 py-1 text-sm"
          value={intervalMs}
          onChange={(e) => setIntervalMs(Number(e.target.value))}
        >
          <option value={2000}>2s</option>
          <option value={5000}>5s</option>
          <option value={10000}>10s</option>
        </select>
      </div>

      {message && <div className="text-red-600 mb-2">{message}</div>}

      <table className="w-full border-collapse">
        <thead>
          <tr>
            <th className="border px-2 py-1 text-left">Symbol</th>
            <th className="border px-2 py-1 text-right">Last Price</th>
            <th className="border px-2 py-1">Timestamp</th>
            <th className="border px-2 py-1">Status</th>
          </tr>
        </thead>
        <tbody>
          {quotes.map((q) => (
            <tr key={q.symbol}>
              <td className="border px-2 py-1">{q.symbol}</td>
              <td className="border px-2 py-1 text-right">
                {q.last_price !== undefined ? q.last_price.toFixed(2) : "-"}
              </td>
              <td className="border px-2 py-1">
                {q.timestamp ? new Date(q.timestamp).toLocaleTimeString() : "-"}
              </td>
              <td className="border px-2 py-1">
                {q.error ? q.error : "ok"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
