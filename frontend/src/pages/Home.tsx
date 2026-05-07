import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";

export default function Home() {
  const [items, setItems] = useState<any[]>([]);
  useEffect(() => {
    api.get("/products?per_page=8&sort_by=created_at&sort_order=desc").then((r) => setItems(r.data.items));
  }, []);
  return (
    <>
      <h1>Featured Products</h1>
      <div className="grid">
        {items.map((p) => (
          <Link key={p.id} to={`/products/${p.id}`} className="card">
            <strong>{p.name}</strong>
            <div className="price">${p.price}</div>
          </Link>
        ))}
      </div>
    </>
  );
}
