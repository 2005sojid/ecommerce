import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, sellerApi } from "../../api";

const NEXT_STATUS: Record<string, { value: string; label: string } | null> = {
  pending: { value: "confirmed", label: "Confirm" },
  confirmed: { value: "processing", label: "Process" },
  processing: { value: "packed", label: "Pack" },
  packed: { value: "shipped", label: "Ship" },
  shipped: null,
  delivered: null,
  cancelled: null,
};

export default function SellerOrders() {
  const [items, setItems] = useState<any[]>([]);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");
  const [busyId, setBusyId] = useState<string | null>(null);
  const [tracking, setTracking] = useState<Record<string, string>>({});
  const per_page = 20;

  const load = () => {
    setLoading(true);
    sellerApi.orders(page, per_page)
      .then((d) => { setItems(d.items); setTotal(d.total); })
      .catch((e) => setErr(e.response?.data?.detail || "Failed to load orders"))
      .finally(() => setLoading(false));
  };

  useEffect(load, [page]);

  const advance = async (orderId: string, currentStatus: string) => {
    const next = NEXT_STATUS[currentStatus];
    if (!next || busyId) return;
    setBusyId(orderId);
    setErr("");
    try {
      const body: any = { status: next.value };
      if (next.value === "shipped" && tracking[orderId]?.trim()) body.tracking_number = tracking[orderId].trim();
      await api.patch(`/orders/${orderId}/status`, body);
      load();
    } catch (e: any) {
      setErr(e.response?.data?.detail || "Failed to update order");
    } finally {
      setBusyId(null);
    }
  };

  return (
    <>
      <h1>Seller Orders</h1>
      {err && <p className="error">{err}</p>}
      <div className="muted">Total: {total}</div>
      {loading ? (
        <p className="muted">Loading...</p>
      ) : items.length === 0 ? (
        <p className="muted">No orders yet.</p>
      ) : (
        <div className="card">
          <table style={{ width: "100%" }}>
            <thead>
              <tr>
                <th align="left">Order</th>
                <th align="left">Status</th>
                <th align="right">Total</th>
                <th align="left">Created</th>
                <th align="left">Action</th>
              </tr>
            </thead>
            <tbody>
              {items.map((o) => {
                const next = NEXT_STATUS[o.status];
                return (
                  <tr key={o.id}>
                    <td><Link to={`/orders/${o.id}`}>{o.id}</Link></td>
                    <td><span className={`badge ${o.status}`}>{o.status}</span></td>
                    <td align="right">${Number(o.total_amount).toFixed(2)}</td>
                    <td>{o.created_at ? new Date(o.created_at).toLocaleString() : ""}</td>
                    <td>
                      {next ? (
                        <div className="flex" style={{ gap: 6 }}>
                          {next.value === "shipped" && (
                            <input
                              className="input"
                              placeholder="Tracking #"
                              value={tracking[o.id] || ""}
                              onChange={(e) => setTracking((s) => ({ ...s, [o.id]: e.target.value }))}
                              style={{ maxWidth: 140 }}
                            />
                          )}
                          <button className="btn" disabled={busyId === o.id} onClick={() => advance(o.id, o.status)}>
                            {busyId === o.id ? "…" : next.label}
                          </button>
                        </div>
                      ) : (
                        <span className="muted">—</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
      <div className="flex" style={{ marginTop: 12, gap: 8 }}>
        <button className="btn secondary" disabled={page <= 1} onClick={() => setPage(page - 1)}>Prev</button>
        <span>Page {page}</span>
        <button className="btn secondary" disabled={page * per_page >= total} onClick={() => setPage(page + 1)}>Next</button>
      </div>
    </>
  );
}
