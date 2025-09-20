"use client";

import { useEffect, useRef, useState } from "react";

const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

type Quote = {
  symbol: string;
  last_price?: number;
  timestamp?: string;
  error?: string;
};

type OrderSide = "BUY" | "SELL";
type OrderType = "MARKET" | "LIMIT";

export default function QuotesPage() {
  const [symbols, setSymbols] = useState("RELIANCE,TCS,NIFTY");
  const [quotes, setQuotes] = useState<Quote[]>([]);
  const [loading, setLoading] = useState(false);
  const [liveEnabled, setLiveEnabled] = useState<boolean | null>(null);
  const [message, setMessage] = useState<string>("");

  const [autoRefresh, setAutoRefresh] = useState<boolean>(false);
  const [intervalMs, setIntervalMs] = useState<number>(5000);
  const intervalRef = useRef<NodeJS.Timer | null>(null);

  // Upstox connection state
  const [upstoxConnected, setUpstoxConnected] = useState<boolean>(false);
  const [upstoxValid, setUpstoxValid] = useState<boolean>(false);

  // Paper trading order state
  const [orderSymbol, setOrderSymbol] = useState<string>("RELIANCE");
  const [orderQty, setOrderQty] = useState<number>(1);
  const [orderSide, setOrderSide] = useState<OrderSide>("BUY");
  const [orderType, setOrderType] = useState<OrderType>("MARKET");
  const [orderPrice, setOrderPrice] = useState<string>("");
  const [orderMsg, setOrderMsg] = useState<string>("");
  const orderMsgTimeoutRef = useRef<NodeJS.Timer | null>(null);

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

  async function checkUpstoxStatus() {
    try {
      const res = await fetch(`${backendUrl}/api/v1/auth/upstox/status`);
      const data = await res.json();
      setUpstoxConnected(data.has_token || false);
      setUpstoxValid(data.is_valid || false);
    } catch {
      setUpstoxConnected(false);
      setUpstoxValid(false);
    }
  }

  async function disconnectUpstox() {
    try {
      await fetch(`${backendUrl}/api/v1/auth/upstox/disconnect`, {
        method: "DELETE",
      });
      setUpstoxConnected(false);
      setUpstoxValid(false);
      setMessage("Upstox disconnected successfully");
    } catch {
      setMessage("Failed to disconnect Upstox");
    }
  }

  function connectUpstox() {
    window.open(`${backendUrl}/api/v1/auth/upstox/login`, '_self');
  }

  function showOrderToast(msg: string) {
    setOrderMsg(msg);
    if (orderMsgTimeoutRef.current) {
      clearTimeout(orderMsgTimeoutRef.current as unknown as number);
    }
    orderMsgTimeoutRef.current = setTimeout(() => {
      setOrderMsg("");
    }, 4000) as unknown as NodeJS.Timer;
  }

  async function placeOrder() {
    setOrderMsg("");
    try {
      const payload: Record<string, unknown> = {
        symbol: orderSymbol.trim(),
        quantity: Number(orderQty),
        side: orderSide,
        order_type: orderType,
      };
      if (orderType === "LIMIT") {
        const p = Number(orderPrice);
        if (!Number.isFinite(p) || p <= 0) {
          showOrderToast("Enter valid limit price");
          return;
        }
        payload.price = p;
      }

      const res = await fetch(`${backendUrl}/api/v1/paper/order`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: "Bearer dev-token",
        },
        body: JSON.stringify(payload),
      });

      const data = await res.json();
      if (!res.ok || data.success === false) {
        const serverMsg =
          typeof data?.detail === "string"
            ? data.detail
            : (Array.isArray(data?.detail) && data.detail[0]?.msg) || data?.error;
        showOrderToast(serverMsg || "Order failed");
        return;
      }

      const price = data.execution_price ?? data.price;
      const filled = data.filled_quantity ?? data.quantity;
      showOrderToast(`Order OK: ${orderSide} ${filled} ${orderSymbol} @ ${price}`);
    } catch (error: unknown) {
      showOrderToast("Failed to place order");
    }
  }

  function quickFill(symbol: string) {
    setOrderSymbol(symbol);
    if (orderType === "LIMIT") {
      const md = quotes.find((q) => q.symbol === symbol);
      if (md?.last_price) setOrderPrice(String(md.last_price));
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

  // Initialize: load flag and check Upstox status
  useEffect(() => {
    fetchFlag();
    checkUpstoxStatus();
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

      <div className="mb-4 flex items-center gap-2 flex-wrap">
        <button
          className="border rounded px-3 py-1"
          onClick={fetchFlag}
        >
          Check Live-Data Flag
        </button>
        {liveEnabled !== null && (
          <button 
            className={`border rounded px-3 py-1 ${
              liveEnabled ? "bg-green-100 border-green-500 text-green-800" : "border-gray-400"
            }`} 
            onClick={toggleFlag}
          >
            {liveEnabled ? "✓ Live-Data Enabled" : "Enable Live-Data"}
          </button>
        )}
        {liveEnabled !== null && (
          <span className={`text-sm ml-2 ${liveEnabled ? "text-green-600" : "text-gray-600"}`}>
            Status: {liveEnabled ? "Enabled" : "Disabled"}
          </span>
        )}
        
        {/* Upstox Connection Controls */}
        {upstoxConnected && upstoxValid ? (
          <div className="flex gap-2">
            <button
              className="bg-green-100 border-green-500 text-green-800 border rounded px-3 py-1"
              onClick={checkUpstoxStatus}
            >
              ✓ Upstox Connected
            </button>
            <button
              className="bg-red-100 border-red-400 text-red-800 border rounded px-2 py-1 text-sm"
              onClick={disconnectUpstox}
            >
              Disconnect
            </button>
          </div>
        ) : upstoxConnected && !upstoxValid ? (
          <div className="flex gap-2">
            <button
              className="bg-yellow-100 border-yellow-500 text-yellow-800 border rounded px-3 py-1"
              onClick={checkUpstoxStatus}
            >
              ⚠ Upstox Invalid
            </button>
            <button
              className="bg-red-100 border-red-400 text-red-800 border rounded px-2 py-1 text-sm"
              onClick={disconnectUpstox}
            >
              Disconnect
            </button>
          </div>
        ) : (
          <button
            className="bg-blue-100 border-blue-400 text-blue-800 border rounded px-3 py-1"
            onClick={connectUpstox}
          >
            Connect Upstox
          </button>
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
              <td className="border px-2 py-1">
                <button
                  className="text-blue-600 hover:underline cursor-pointer"
                  onClick={() => quickFill(q.symbol)}
                >
                  {q.symbol}
                </button>
              </td>
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

      {/* Paper Trading Order Ticket */}
      <div className="mt-8 p-4 border rounded-lg bg-gray-50">
        <h2 className="text-lg font-semibold mb-4">Paper Trading Order Ticket</h2>
        
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
          <div>
            <label className="block text-sm mb-1">Symbol</label>
            <input
              className="border rounded px-2 py-1 w-full"
              value={orderSymbol}
              onChange={(e) => setOrderSymbol(e.target.value)}
              placeholder="RELIANCE"
            />
          </div>
          <div>
            <label className="block text-sm mb-1">Quantity</label>
            <input
              type="number"
              className="border rounded px-2 py-1 w-full"
              value={orderQty}
              onChange={(e) => setOrderQty(Number(e.target.value))}
              min="1"
            />
          </div>
          <div>
            <label className="block text-sm mb-1">Side</label>
            <select
              className="border rounded px-2 py-1 w-full"
              value={orderSide}
              onChange={(e) => setOrderSide(e.target.value as OrderSide)}
            >
              <option value="BUY">BUY</option>
              <option value="SELL">SELL</option>
            </select>
          </div>
          <div>
            <label className="block text-sm mb-1">Type</label>
            <select
              className="border rounded px-2 py-1 w-full"
              value={orderType}
              onChange={(e) => setOrderType(e.target.value as OrderType)}
            >
              <option value="MARKET">MARKET</option>
              <option value="LIMIT">LIMIT</option>
            </select>
          </div>
        </div>

        {orderType === "LIMIT" && (
          <div className="mb-4">
            <label className="block text-sm mb-1">Limit Price</label>
            <input
              type="number"
              step="0.01"
              className="border rounded px-2 py-1 w-32"
              value={orderPrice}
              onChange={(e) => setOrderPrice(e.target.value)}
              placeholder="0.00"
            />
          </div>
        )}

        <div className="flex items-center gap-4">
          <button
            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
            onClick={placeOrder}
          >
            Place Paper Order
          </button>
          {orderMsg && (
            <div className={`text-sm px-3 py-1 rounded ${
              orderMsg.includes("OK") ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"
            }`}>
              {orderMsg}
            </div>
          )}
        </div>
        
        <p className="text-xs text-gray-600 mt-2">
          Click on any symbol above to quick-fill the order ticket
        </p>
      </div>
    </div>
  );
}
