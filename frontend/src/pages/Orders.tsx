import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";

export default function Orders() {
  const [items, setItems] = useState<any[] | null>(null);
  useEffect(() => {
    api.get("/orders?per_page=20").then((r) => setItems(r.data.items)).catch(() => setItems([]));
  }, []);

  return (
    <>
      <h1>My Orders</h1>

      {items === null && (
        <div className="card">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="skeleton" style={{ height: 28, marginBottom: 10 }} />
          ))}
        </div>
      )}

      {items !== null && items.length === 0 && (
        <div className="card" style={{ textAlign: "center", padding: 48 }}>
          <h3 style={{ marginBottom: 4 }}>No orders yet</h3>
          <p className="muted">When you place an order, it will appear here.</p>
          <Link to="/products" className="btn" style={{ marginTop: 12 }}>Start shopping</Link>
        </div>
      )}

      {items !== null && items.length > 0 && (
        <table>
          <thead>
            <tr>
              <th>Order</th>
              <th>Status</th>
              <th>Total</th>
              <th>Date</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {items.map((o) => (
              <tr key={o.id}>
                <td><code>{o.id.slice(0, 8)}</code></td>
                <td><span className={`badge ${o.status}`}>{o.status}</span></td>
                <td className="price">${o.total_amount}</td>
                <td className="muted">{new Date(o.created_at).toLocaleString()}</td>
                <td><Link to={`/orders/${o.id}`}>Track →</Link></td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </>
  );
}
