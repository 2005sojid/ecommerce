import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, wishlistApi } from "../api";

type Cat = { id: string; name: string; slug: string; parent_id: string | null; children?: Cat[] };

function flatten(nodes: Cat[], depth = 0, out: { id: string; name: string; depth: number }[] = []) {
  for (const n of nodes) {
    out.push({ id: n.id, name: n.name, depth });
    if (n.children && n.children.length) flatten(n.children, depth + 1, out);
  }
  return out;
}

export default function Products() {
  const [items, setItems] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [minPrice, setMinPrice] = useState("");
  const [maxPrice, setMaxPrice] = useState("");
  const [categoryId, setCategoryId] = useState("");
  const [sort, setSort] = useState("created_at:desc");
  const [categories, setCategories] = useState<{ id: string; name: string; depth: number }[]>([]);
  const [wishIds, setWishIds] = useState<Set<string>>(new Set());
  const hasToken = !!localStorage.getItem("access_token");

  useEffect(() => {
    if (hasToken) {
      wishlistApi.ids().then((ids) => setWishIds(new Set(ids))).catch(() => {});
    }
    api.get("/categories").then((r) => setCategories(flatten(r.data))).catch(() => {});
  }, []);

  const toggleWish = async (e: React.MouseEvent, product_id: string) => {
    e.preventDefault();
    e.stopPropagation();
    try {
      if (wishIds.has(product_id)) {
        await wishlistApi.remove(product_id);
        setWishIds((prev) => { const n = new Set(prev); n.delete(product_id); return n; });
      } else {
        await wishlistApi.add(product_id);
        setWishIds((prev) => new Set(prev).add(product_id));
      }
    } catch {}
  };

  const load = () => {
    const [sort_by, sort_order] = sort.split(":");
    const params: any = { page, per_page: 12, sort_by, sort_order };
    if (search) params.search = search;
    if (minPrice) params.min_price = minPrice;
    if (maxPrice) params.max_price = maxPrice;
    if (categoryId) params.category_id = categoryId;
    api.get("/products", { params }).then((r) => {
      setItems(r.data.items);
      setTotal(r.data.total);
    });
  };

  useEffect(load, [page]);

  return (
    <>
      <h1>Products</h1>
      <div className="card flex" style={{ marginBottom: 8 }}>
        <label>Category
          <select className="input" value={categoryId} onChange={(e) => { setCategoryId(e.target.value); setPage(1); setTimeout(load, 0); }}>
            <option value="">All</option>
            {categories.map((c) => (
              <option key={c.id} value={c.id}>{"  ".repeat(c.depth)}{c.name}</option>
            ))}
          </select>
        </label>
        <label>Sort by
          <select className="input" value={sort} onChange={(e) => { setSort(e.target.value); setPage(1); setTimeout(load, 0); }}>
            <option value="created_at:desc">Newest</option>
            <option value="price:asc">Price: low to high</option>
            <option value="price:desc">Price: high to low</option>
            <option value="name:asc">Name: A → Z</option>
          </select>
        </label>
      </div>
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
          <Link key={p.id} to={`/products/${p.id}`} className="card" style={{ position: "relative" }}>
            {hasToken && (
              <button
                className="btn secondary"
                onClick={(e) => toggleWish(e, p.id)}
                style={{ position: "absolute", top: 8, right: 8, padding: "2px 8px" }}
              >
                {wishIds.has(p.id) ? "♥" : "♡"}
              </button>
            )}
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
