import { useEffect, useState } from "react";
import { returnsApi, type ReturnReq } from "../../api";

export default function AdminReturns() {
  const [items, setItems] = useState<ReturnReq[]>([]);
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [msg, setMsg] = useState("");

  const load = () => {
    setLoading(true);
    returnsApi
      .adminList(1, 50, statusFilter || undefined)
      .then((d) => {
        setItems(d.items);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  };

  useEffect(load, [statusFilter]);

  const approve = async (r: ReturnReq) => {
    const amt = window.prompt("Refund amount?", r.refund_amount?.toString() || "0");
    if (amt == null) return;
    const refund_amount = parseFloat(amt);
    if (isNaN(refund_amount)) {
      setMsg("Invalid amount");
      return;
    }
    try {
      await returnsApi.adminUpdate(r.id, { status: "approved", refund_amount });
      load();
    } catch (e: any) {
      setMsg(e.response?.data?.detail || "Error");
    }
  };

  const reject = async (r: ReturnReq) => {
    try {
      await returnsApi.adminUpdate(r.id, { status: "rejected" });
      load();
    } catch (e: any) {
      setMsg(e.response?.data?.detail || "Error");
    }
  };

  const refunded = async (r: ReturnReq) => {
    try {
      await returnsApi.adminUpdate(r.id, { status: "refunded" });
      load();
    } catch (e: any) {
      setMsg(e.response?.data?.detail || "Error");
    }
  };

  return (
    <>
      <h1>Admin · Returns</h1>
      <div className="flex" style={{ marginBottom: 12 }}>
        <label>Status:</label>
        <select className="input" value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
          <option value="">All</option>
          <option value="pending">Pending</option>
          <option value="approved">Approved</option>
          <option value="rejected">Rejected</option>
          <option value="refunded">Refunded</option>
        </select>
      </div>
      {msg && <p className="muted">{msg}</p>}
      {loading ? (
        <p>Loading…</p>
      ) : items.length === 0 ? (
        <p className="muted">No returns.</p>
      ) : (
        <table className="table">
          <thead>
            <tr>
              <th>Order</th>
              <th>User</th>
              <th>Status</th>
              <th>Reason</th>
              <th>Refund</th>
              <th>Date</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {items.map((r) => (
              <tr key={r.id}>
                <td>{r.order_id}</td>
                <td>{r.user_id.slice(0, 8)}…</td>
                <td>{r.status}</td>
                <td>{r.reason}</td>
                <td>{r.refund_amount != null ? `$${r.refund_amount}` : "—"}</td>
                <td>{new Date(r.created_at).toLocaleDateString()}</td>
                <td>
                  <div className="flex">
                    <button className="btn" onClick={() => approve(r)}>Approve</button>
                    <button className="btn secondary" onClick={() => reject(r)}>Reject</button>
                    <button className="btn" onClick={() => refunded(r)}>Mark Refunded</button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </>
  );
}
