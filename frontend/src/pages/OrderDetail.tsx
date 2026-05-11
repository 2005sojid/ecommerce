import { useEffect, useRef, useState } from "react";
import { useParams } from "react-router-dom";
import { api, getToken } from "../api";

export default function OrderDetail() {
  const { id } = useParams();
  const [order, setOrder] = useState<any>(null);
  const [liveEvents, setLiveEvents] = useState<any[]>([]);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    api.get(`/orders/${id}`).then((r) => setOrder(r.data));

    const token = getToken();
    if (!token) return;
    const proto = window.location.protocol === "https:" ? "wss" : "ws";
    const ws = new WebSocket(`${proto}://${window.location.host}/ws/orders/${id}?token=${token}`);
    wsRef.current = ws;
    ws.onmessage = (m) => {
      const data = JSON.parse(m.data);
      setLiveEvents((prev) => [...prev, data]);
      if (data.event === "status_changed") {
        setOrder((o: any) => (o ? { ...o, status: data.new_status } : o));
      }
    };

    const interval = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) ws.send("ping");
    }, 25000);
    return () => {
      clearInterval(interval);
      ws.close();
    };
  }, [id]);

  if (!order) return <div>Loading…</div>;

  return (
    <>
      <h1>Order <code>{order.id}</code></h1>
      <div className="card">
        Status: <span className={`badge ${order.status}`}>{order.status}</span>
        {order.tracking_number && <p>Tracking: <code>{order.tracking_number}</code></p>}
        <p>Total: <span className="price">${order.total_amount}</span></p>
        <p className="muted">Shipping: {order.shipping_address}</p>
        <p className="muted">Created: {new Date(order.created_at).toLocaleString()}</p>
      </div>

      <h3>Items</h3>
      <table className="card">
        <thead><tr><th>Product</th><th>Qty</th><th>Unit price</th></tr></thead>
        <tbody>
          {order.items?.map((it: any, idx: number) => (
            <tr key={`${it.product_id}:${it.variant_id || ""}:${idx}`}>
              <td>
                <code>{it.product_id.slice(0, 8)}…</code>
                {it.variant_name ? ` — ${it.variant_name}` : ""}
              </td>
              <td>{it.quantity}</td>
              <td>${it.unit_price}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <h3>Status history</h3>
      <table className="card">
        <thead><tr><th>From</th><th>To</th><th>Time</th></tr></thead>
        <tbody>
          {order.events?.map((e: any, i: number) => (
            <tr key={i}>
              <td>{e.from_status || "—"}</td>
              <td>{e.to_status}</td>
              <td>{new Date(e.timestamp).toLocaleString()}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <h3>🟢 Live updates (WebSocket)</h3>
      <div className="card">
        {liveEvents.length === 0 && <p className="muted">Waiting for updates…</p>}
        {liveEvents.map((e, i) => (
          <div key={i}>
            <code>{e.timestamp?.slice(11, 19)}</code> — {e.event}: {e.from_status || "—"} → <strong>{e.new_status || e.current_status}</strong>
          </div>
        ))}
      </div>
    </>
  );
}
