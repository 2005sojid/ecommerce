import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../../api";

const STATUSES = ["pending", "confirmed", "processing", "packed", "shipped", "delivered", "cancelled"];

export default function AdminOrders() {
  const [items, setItems] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");
  const [busyId, setBusyId] = useState<string | null>(null);
  const [draft, setDraft] = useState<Record<string, { status?: string; tracking?: string; reason?: string }>>({});
  const per_page = 25;

  const load = () => {
    setLoading(true);
    const params: any = { page, per_page };
    if (statusFilter) params.status = statusFilter;
    api.get("/admin/orders", { params })
      .then((r) => { setItems(r.data.items); setTotal(r.data.total); })
      .catch((e) => setErr(e.response?.data?.detail || "Failed to load orders"))
      .finally(() => setLoading(false));
  };

  useEffect(load, [page, statusFilter]);

  const update = async (orderId: string) => {
    const d = draft[orderId] || {};
    if (!d.status || busyId) return;
    setBusyId(orderId);
    setErr("");
    try {
      const body: any = { status: d.status };
      if (d.tracking?.trim()) body.tracking_number = d.tracking.trim();
      if (d.reason?.trim()) body.reason = d.reason.trim();
      await api.patch(`/orders/${orderId}/status`, body);
      setDraft((s) => ({ ...s, [orderId]: {} }));
      load();
    } catch (e: any) {
      setErr(e.response?.data?.detail || "Failed to update order");
    } finally {
      setBusyId(null);
    }
  };

  return (
    <>
      <h1>Manage Orders</h1>
      {err && <p className="error">{err}</p>}
      <div className="card flex" style={{ gap: 8, alignItems: "center" }}>
        <label>Status</label>
        <select className="input" value={statusFilter} onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}>
          <option value="">All</option>
          {STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
        <span className="muted">Total: {total}</span>
      </div>
      {loading ? (
        <p className="muted">Loading…</p>
      ) : items.length === 0 ? (
        <p className="muted">No orders.</p>
      ) : (
        <div className="card">
          <table style={{ width: "100%" }}>
            <thead>
              <tr>
                <th align="left">Order</th>
                <th align="left">User</th>
                <th align="left">Status</th>
                <th align="right">Total</th>
                <th align="left">Created</th>
                <th align="left">Update</th>
              </tr>
            </thead>
            <tbody>
              {items.map((o) => {
                const d = draft[o.id] || {};
                return (
                  <tr key={o.id}>
                    <td><Link to={`/orders/${o.id}`}>{o.id}</Link></td>
                    <td className="muted">{o.user_id?.slice(0, 8)}</td>
                    <td><span className={`badge ${o.status}`}>{o.status}</span></td>
                    <td align="right">${Number(o.total_amount).toFixed(2)}</td>
                    <td>{o.created_at ? new Date(o.created_at).toLocaleString() : ""}</td>
                    <td>
                      <div className="flex" style={{ gap: 6, flexWrap: "wrap" }}>
                        <select className="input" value={d.status || ""} style={{ maxWidth: 130 }}
                                onChange={(e) => setDraft((s) => ({ ...s, [o.id]: { ...s[o.id], status: e.target.value } }))}>
                          <option value="">-- new status --</option>
                          {STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
                        </select>
                        <input className="input" placeholder="Tracking #" value={d.tracking || ""}
                               onChange={(e) => setDraft((s) => ({ ...s, [o.id]: { ...s[o.id], tracking: e.target.value } }))}
                               style={{ maxWidth: 130 }} />
                        <button className="btn" disabled={!d.status || busyId === o.id} onClick={() => update(o.id)}>
                          {busyId === o.id ? "…" : "Apply"}
                        </button>
                      </div>
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
