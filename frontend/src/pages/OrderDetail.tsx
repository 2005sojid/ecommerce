import { useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api, getToken, returnsApi } from "../api";
import { useAuth } from "../useAuth";

export default function OrderDetail() {
  const { id } = useParams();
  const [order, setOrder] = useState<any>(null);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const [actionMsg, setActionMsg] = useState("");
  const [returnReason, setReturnReason] = useState("");
  const [showReturn, setShowReturn] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectRef = useRef<number | null>(null);
  const closedRef = useRef(false);
  const { user } = useAuth();
  const nav = useNavigate();

  const load = () => {
    api.get(`/orders/${id}`).then((r) => setOrder(r.data)).catch((e) => setErr(e.response?.data?.detail || "Could not load order"));
  };

  useEffect(() => {
    if (!id) return;
    load();
    closedRef.current = false;

    const connect = () => {
      const token = getToken();
      if (!token) return;
      const proto = window.location.protocol === "https:" ? "wss" : "ws";
      const ws = new WebSocket(`${proto}://${window.location.host}/ws/orders/${id}?token=${token}`);
      wsRef.current = ws;
      ws.onmessage = (m) => {
        try {
          const data = JSON.parse(m.data);
          if (data.event === "status_changed") {
            setOrder((o: any) => (o ? { ...o, status: data.new_status } : o));
          }
        } catch {}
      };
      ws.onclose = () => {
        if (closedRef.current) return;
        reconnectRef.current = window.setTimeout(connect, 3000);
      };
      ws.onerror = () => {};
    };
    connect();

    const interval = setInterval(() => {
      const ws = wsRef.current;
      if (ws && ws.readyState === WebSocket.OPEN) ws.send("ping");
    }, 25000);

    return () => {
      closedRef.current = true;
      clearInterval(interval);
      if (reconnectRef.current) window.clearTimeout(reconnectRef.current);
      wsRef.current?.close();
    };
  }, [id]);

  const cancelOrder = async () => {
    if (busy || !order) return;
    if (!window.confirm("Cancel this order?")) return;
    setBusy(true);
    setActionMsg("");
    try {
      const { data } = await api.patch(`/orders/${order.id}/status`, { status: "cancelled", reason: "Customer cancelled" });
      setOrder((o: any) => ({ ...o, status: data.status }));
      setActionMsg("Order cancelled");
    } catch (e: any) {
      setActionMsg(e.response?.data?.detail || "Could not cancel");
    } finally {
      setBusy(false);
    }
  };

  const submitReturn = async (e: React.FormEvent) => {
    e.preventDefault();
    if (busy || !order) return;
    if (!returnReason.trim()) { setActionMsg("Please provide a reason"); return; }
    setBusy(true);
    setActionMsg("");
    try {
      await returnsApi.create(order.id, returnReason.trim());
      setActionMsg("Return request submitted");
      setShowReturn(false);
      setReturnReason("");
      nav("/returns");
    } catch (e: any) {
      setActionMsg(e.response?.data?.detail || "Could not submit return");
    } finally {
      setBusy(false);
    }
  };

  if (err) return <p className="error">{err}</p>;
  if (!order) return <div>Loading…</div>;

  const isCustomerOwner = user?.role === "customer" && order.user_id === user.id;
  const canCancel = isCustomerOwner && order.status === "pending";
  const canReturn = isCustomerOwner && (order.status === "delivered" || order.status === "shipped");

  return (
    <>
      <h1>Order <code>{order.id}</code></h1>
      <div className="card">
        Status: <span className={`badge ${order.status}`}>{order.status}</span>
        {order.tracking_number && <p>Tracking: <code>{order.tracking_number}</code></p>}
        <p>Total: <span className="price">${order.total_amount}</span></p>
        <p className="muted">Shipping: {order.shipping_address}</p>
        <p className="muted">Created: {new Date(order.created_at).toLocaleString()}</p>
        <div className="flex" style={{ gap: 8, marginTop: 8 }}>
          {canCancel && (
            <button className="btn danger" onClick={cancelOrder} disabled={busy}>
              {busy ? "Cancelling…" : "Cancel order"}
            </button>
          )}
          {canReturn && !showReturn && (
            <button className="btn secondary" onClick={() => setShowReturn(true)}>Request return</button>
          )}
        </div>
        {showReturn && (
          <form onSubmit={submitReturn} style={{ marginTop: 12 }}>
            <label>Reason for return</label>
            <textarea className="input" rows={3} value={returnReason} onChange={(e) => setReturnReason(e.target.value)} required />
            <div className="flex" style={{ gap: 8, marginTop: 8 }}>
              <button className="btn" type="submit" disabled={busy}>{busy ? "Submitting…" : "Submit return"}</button>
              <button className="btn secondary" type="button" onClick={() => setShowReturn(false)} disabled={busy}>Cancel</button>
            </div>
          </form>
        )}
        {actionMsg && <p className="muted" style={{ marginTop: 8 }}>{actionMsg}</p>}
      </div>

      <h3>Items</h3>
      <table className="card">
        <thead><tr><th>Product</th><th>Qty</th><th>Unit price</th></tr></thead>
        <tbody>
          {order.items?.map((it: any, idx: number) => (
            <tr key={`${it.product_id}:${it.variant_id || ""}:${idx}`}>
              <td>
                {it.product_name || <code>{it.product_id.slice(0, 8)}</code>}
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
    </>
  );
}
