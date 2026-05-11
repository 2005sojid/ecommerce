import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { api, getToken } from "../api";

export default function AdminDashboard() {
  const today = new Date().toISOString().slice(0, 10);
  const [daily, setDaily] = useState<any>(null);
  const [top, setTop] = useState<any[]>([]);
  const [low, setLow] = useState<any[]>([]);
  const [live, setLive] = useState<any[]>([]);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    api.get(`/admin/analytics/daily?date=${today}`).then((r) => setDaily(r.data));
    api.get("/admin/analytics/top-products?days=30&limit=5").then((r) => setTop(r.data));
    api.get("/admin/inventory/low-stock?threshold=20").then((r) => setLow(r.data));

    const token = getToken();
    if (!token) return;
    const proto = window.location.protocol === "https:" ? "wss" : "ws";
    const ws = new WebSocket(`${proto}://${window.location.host}/ws/inventory?token=${token}`);
    wsRef.current = ws;
    ws.onmessage = (m) => setLive((prev) => [JSON.parse(m.data), ...prev].slice(0, 30));
    const interval = setInterval(() => ws.readyState === WebSocket.OPEN && ws.send("ping"), 25000);
    return () => { clearInterval(interval); ws.close(); };
  }, [today]);

  return (
    <>
      <h1>Admin dashboard</h1>

      <div className="card flex" style={{ gap: 12 }}>
        <Link className="btn secondary" to="/admin/coupons">Manage coupons</Link>
        <Link className="btn secondary" to="/admin/returns">Manage returns</Link>
      </div>

      <h3>Today's sales ({today})</h3>
      {daily && (
        <div className="card flex" style={{ gap: 32 }}>
          <div><div className="muted">Orders</div><strong>{daily.order_count}</strong></div>
          <div><div className="muted">Revenue</div><strong className="price">${daily.total_revenue}</strong></div>
          <div><div className="muted">Customers</div><strong>{daily.unique_customers}</strong></div>
          <div><div className="muted">Source</div><span className="badge">{daily.source}</span></div>
        </div>
      )}

      <h3>Top products (30d)</h3>
      <table className="card">
        <thead><tr><th>Product</th><th>Units</th><th>Revenue</th></tr></thead>
        <tbody>
          {top.map((t) => (
            <tr key={t.product_id}><td>{t.name}</td><td>{t.units_sold}</td><td className="price">${t.revenue}</td></tr>
          ))}
        </tbody>
      </table>

      <h3>Low stock (&lt; 20)</h3>
      <table className="card">
        <thead><tr><th>Product</th><th>Available</th><th>Reserved</th></tr></thead>
        <tbody>
          {low.map((l) => (
            <tr key={l.product_id}><td>{l.name}</td><td>{l.available}</td><td>{l.reserved}</td></tr>
          ))}
        </tbody>
      </table>

      <h3>🟢 Live inventory feed (WebSocket)</h3>
      <div className="card">
        {live.length === 0 && <p className="muted">No events yet — try a checkout or flash sale claim.</p>}
        {live.map((e, i) => (
          <div key={i}>
            <code>{e.timestamp?.slice(11, 19)}</code> — product <code>{e.product_id?.slice(0, 8)}</code> →
            <strong> {e.new_quantity}</strong> ({e.source})
          </div>
        ))}
      </div>
    </>
  );
}
