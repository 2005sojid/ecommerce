import { useEffect, useState } from "react";
import { reviewsApi } from "../../api";

type AdminReview = {
  id: string;
  user_id: string;
  product_id: string;
  rating: number;
  comment: string | null;
  is_approved: boolean;
  created_at: string;
  helpful_count: number;
};

export default function AdminReviewsModerate() {
  const [items, setItems] = useState<AdminReview[]>([]);
  const [approvedFilter, setApprovedFilter] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [msg, setMsg] = useState("");

  const load = () => {
    setLoading(true);
    const approved = approvedFilter === "" ? undefined : approvedFilter === "true";
    reviewsApi
      .adminList(1, 50, approved)
      .then((d: any) => {
        setItems(d.items);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  };

  useEffect(load, [approvedFilter]);

  const moderate = async (r: AdminReview, is_approved: boolean) => {
    try {
      await reviewsApi.adminModerate(r.id, is_approved);
      load();
    } catch (e: any) {
      setMsg(e.response?.data?.detail || "Error");
    }
  };

  return (
    <>
      <h1>Admin · Reviews</h1>
      <div className="flex" style={{ marginBottom: 12 }}>
        <label>Status:</label>
        <select className="input" value={approvedFilter} onChange={(e) => setApprovedFilter(e.target.value)}>
          <option value="">All</option>
          <option value="true">Approved</option>
          <option value="false">Rejected</option>
        </select>
      </div>
      {msg && <p className="muted">{msg}</p>}
      {loading ? (
        <p>Loading…</p>
      ) : items.length === 0 ? (
        <p className="muted">No reviews.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Rating</th>
              <th>Comment</th>
              <th>Product</th>
              <th>User</th>
              <th>Status</th>
              <th>Helpful</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {items.map((r) => (
              <tr key={r.id}>
                <td>{"★".repeat(r.rating)}</td>
                <td>{r.comment || "—"}</td>
                <td>{r.product_id.slice(0, 8)}…</td>
                <td>{r.user_id.slice(0, 8)}…</td>
                <td>
                  <span className={r.is_approved ? "badge" : "badge muted"}>
                    {r.is_approved ? "Approved" : "Rejected"}
                  </span>
                </td>
                <td>{r.helpful_count}</td>
                <td>
                  <div className="flex">
                    <button className="btn" onClick={() => moderate(r, true)} disabled={r.is_approved}>Approve</button>
                    <button className="btn secondary" onClick={() => moderate(r, false)} disabled={!r.is_approved}>Reject</button>
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
