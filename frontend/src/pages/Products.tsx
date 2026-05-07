import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";

export default function Products() {
  const [items, setItems] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [minPrice, setMinPrice] = useState("");
  const [maxPrice, setMaxPrice] = useState("");

  const load = () => {
    const params: any = { page, per_page: 12 };
    if (search) params.search = search;
    if (minPrice) params.min_price = minPrice;
    if (maxPrice) params.max_price = maxPrice;
    api.get("/products", { params }).then((r) => {
      setItems(r.data.items);
      setTotal(r.data.total);
    });
  };

  useEffect(load, [page]);

  return (
    <>
      <h1>Products</h1>
      <div className="card flex">
        <input className="input" placeholder="Search…" value={search}
               onChange={(e) => setSearch(e.target.value)} />
        <input className="input" placeholder="Min $" value={minPrice}
               onChange={(e) => setMinPrice(e.target.value)} style={{ maxWidth: 120 }} />
        <input className="input" placeholder="Max $" value={maxPrice}
               onChange={(e) => setMaxPrice(e.target.value)} style={{ maxWidth: 120 }} />
        <button className="btn" onClick={() => { setPage(1); load(); }}>Search</button>
      </div>
      <div className="muted">Total: {total}</div>
      <div className="grid">
        {items.map((p) => (
          <Link key={p.id} to={`/products/${p.id}`} className="card">
            <strong>{p.name}</strong>
            <div className="muted">{p.description?.slice(0, 60)}…</div>
            <div className="price">${p.price}</div>
          </Link>
        ))}
      </div>
      <div className="flex" style={{ marginTop: 12 }}>
        <button className="btn secondary" disabled={page <= 1} onClick={() => setPage(page - 1)}>Prev</button>
        <span>Page {page}</span>
        <button className="btn secondary" disabled={items.length < 12} onClick={() => setPage(page + 1)}>Next</button>
      </div>
    </>
  );
}
