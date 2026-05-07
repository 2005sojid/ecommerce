import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";

export default function Orders() {
  const [items, setItems] = useState<any[]>([]);
  useEffect(() => {
    api.get("/orders?per_page=20").then((r) => setItems(r.data.items));
  }, []);
  return (
    <>
      <h1>My Orders</h1>
      <table className="card">
        <thead><tr><th>ID</th><th>Status</th><th>Total</th><th>Date</th><th></th></tr></thead>
        <tbody>
          {items.map((o) => (
            <tr key={o.id}>
              <td><code>{o.id}</code></td>
              <td><span className={`badge ${o.status}`}>{o.status}</span></td>
              <td className="price">${o.total_amount}</td>
              <td>{new Date(o.created_at).toLocaleString()}</td>
              <td><Link to={`/orders/${o.id}`}>Track →</Link></td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  );
}
