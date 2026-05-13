import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { returnsApi, type ReturnReq } from "../api";

export default function Returns() {
  const [items, setItems] = useState<ReturnReq[]>([]);
  const [orderId, setOrderId] = useState("");
  const [reason, setReason] = useState("");
  const [msg, setMsg] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [params] = useSearchParams();

  const load = () => {
    setLoading(true);
    returnsApi.list().then((d) => {
      setItems(d.items);
      setLoading(false);
    }).catch(() => setLoading(false));
  };

  useEffect(load, []);

  useEffect(() => {
    const oid = params.get("order_id");
    if (oid) setOrderId(oid);
  }, [params]);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (busy) return;
    setMsg("");
    if (!orderId.trim() || !reason.trim()) {
      setMsg("Order ID and reason are required");
      return;
    }
    setBusy(true);
    try {
      await returnsApi.create(orderId.trim(), reason.trim());
      setOrderId("");
      setReason("");
      setMsg("Return request submitted");
      load();
    } catch (e: any) {
      setMsg(e.response?.data?.detail || "Error submitting return");
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      <h1>Returns</h1>
      <div className="card">
        <h2>Request a Return</h2>
        <p className="muted" style={{ fontSize: 13 }}>
          Tip: open the order from "My Orders" and click "Request return" to prefill this form.
        </p>
        <form onSubmit={submit}>
          <div className="flex" style={{ marginBottom: 8 }}>
            <input
              className="input"
              placeholder="Order ID"
              value={orderId}
              onChange={(e) => setOrderId(e.target.value)}
            />
          </div>
          <div style={{ marginBottom: 8 }}>
            <textarea
              className="input"
              placeholder="Reason"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              rows={3}
              style={{ width: "100%" }}
            />
          </div>
          <button className="btn" type="submit" disabled={busy} style={{ opacity: busy ? 0.6 : 1 }}>
            {busy ? "Submitting…" : "Submit"}
          </button>
          {msg && <p className="muted">{msg}</p>}
        </form>
      </div>

      <h2>My Returns</h2>
      {loading ? (
        <p>Loading…</p>
      ) : items.length === 0 ? (
        <p className="muted">No return requests yet.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Order</th>
              <th>Status</th>
              <th>Reason</th>
              <th>Refund</th>
              <th>Date</th>
            </tr>
          </thead>
          <tbody>
            {items.map((r) => (
              <tr key={r.id}>
                <td><code>{r.order_id}</code></td>
                <td><span className={`badge ${r.status}`}>{r.status}</span></td>
                <td>{r.reason}</td>
                <td className="price">{r.refund_amount != null ? `$${r.refund_amount}` : "—"}</td>
                <td className="muted">{new Date(r.created_at).toLocaleDateString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </>
  );
}
