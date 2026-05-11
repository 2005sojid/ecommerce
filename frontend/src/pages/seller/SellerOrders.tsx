import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { sellerApi } from "../../api";

export default function SellerOrders() {
  const [items, setItems] = useState<any[]>([]);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");
  const per_page = 20;

  useEffect(() => {
    setLoading(true);
    sellerApi.orders(page, per_page)
      .then((d) => { setItems(d.items); setTotal(d.total); })
      .catch((e) => setErr(e.response?.data?.detail || "Failed to load orders"))
      .finally(() => setLoading(false));
  }, [page]);

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
                <th></th>
              </tr>
            </thead>
            <tbody>
              {items.map((o) => (
                <tr key={o.id}>
                  <td>{o.id}</td>
                  <td>{o.status}</td>
                  <td align="right">${o.total_amount.toFixed(2)}</td>
                  <td>{o.created_at ? new Date(o.created_at).toLocaleString() : ""}</td>
                  <td><Link to={`/orders/${o.id}`} className="btn secondary">View</Link></td>
                </tr>
              ))}
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
