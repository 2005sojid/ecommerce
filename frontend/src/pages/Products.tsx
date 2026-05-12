import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { api, wishlistApi } from "../api";
import ProductCard from "../components/ProductCard";
import { useAuth } from "../useAuth";

type Cat = { id: string; name: string; slug: string; parent_id: string | null; children?: Cat[] };

function flatten(nodes: Cat[], depth = 0, out: { id: string; name: string; depth: number }[] = []) {
  for (const n of nodes) {
    out.push({ id: n.id, name: n.name, depth });
    if (n.children && n.children.length) flatten(n.children, depth + 1, out);
  }
  return out;
}

export default function Products() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [items, setItems] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState(searchParams.get("search") || "");
  const [searchInput, setSearchInput] = useState(searchParams.get("search") || "");
  const [minPrice, setMinPrice] = useState("");
  const [maxPrice, setMaxPrice] = useState("");
  const [appliedMin, setAppliedMin] = useState("");
  const [appliedMax, setAppliedMax] = useState("");
  const [categoryId, setCategoryId] = useState(searchParams.get("category") || "");
  const [sort, setSort] = useState("created_at:desc");
  const [categories, setCategories] = useState<{ id: string; name: string; depth: number }[]>([]);
  const [wishIds, setWishIds] = useState<Set<string>>(new Set());
  const { user } = useAuth();
  const canShop = user?.role === "customer";

  useEffect(() => {
    if (canShop) {
      wishlistApi.ids().then((ids) => setWishIds(new Set(ids))).catch(() => {});
    }
    api.get("/categories").then((r) => setCategories(flatten(r.data))).catch(() => {});
  }, []);

  useEffect(() => {
    const urlCat = searchParams.get("category") || "";
    const urlSearch = searchParams.get("search") || "";
    if (urlCat !== categoryId) { setCategoryId(urlCat); setPage(1); }
    if (urlSearch !== search) { setSearch(urlSearch); setSearchInput(urlSearch); setPage(1); }
  }, [searchParams]);

  const toggleWish = async (product_id: string) => {
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

  useEffect(() => {
    const [sort_by, sort_order] = sort.split(":");
    const params: any = { page, per_page: 12, sort_by, sort_order };
    if (search) params.search = search;
    if (appliedMin) params.min_price = appliedMin;
    if (appliedMax) params.max_price = appliedMax;
    if (categoryId) params.category_id = categoryId;
    api.get("/products", { params }).then((r) => {
      setItems(r.data.items);
      setTotal(r.data.total);
    });
  }, [page, sort, categoryId, search, appliedMin, appliedMax]);

  const updateUrl = (next: { category?: string; search?: string }) => {
    const params: Record<string, string> = {};
    const cat = next.category ?? categoryId;
    const q = next.search ?? search;
    if (cat) params.category = cat;
    if (q) params.search = q;
    setSearchParams(params);
  };

  const selectCategory = (id: string) => {
    setCategoryId(id);
    setPage(1);
    updateUrl({ category: id });
  };

  const applyFilters = () => {
    setPage(1);
    setSearch(searchInput);
    setAppliedMin(minPrice);
    setAppliedMax(maxPrice);
    updateUrl({ search: searchInput });
  };

  return (
    <>
      <h1>Products</h1>

      {categories.length > 0 && (
        <div className="pill-tabs scroll-x">
          <button
            className={`pill ${!categoryId ? "active" : ""}`}
            onClick={() => selectCategory("")}
          >All</button>
          {categories.map((c) => (
            <button
              key={c.id}
              className={`pill ${categoryId === c.id ? "active" : ""}`}
              onClick={() => selectCategory(c.id)}
            >{c.name}</button>
          ))}
        </div>
      )}

      <div className="filter-bar card">
        <select className="input" value={sort} onChange={(e) => { setSort(e.target.value); setPage(1); }} style={{ maxWidth: 180 }}>
          <option value="created_at:desc">Newest</option>
          <option value="price:asc">Price: low to high</option>
          <option value="price:desc">Price: high to low</option>
          <option value="name:asc">Name: A → Z</option>
        </select>
        <input className="input" placeholder="Search products, brands…" value={searchInput}
               onChange={(e) => setSearchInput(e.target.value)}
               onKeyDown={(e) => e.key === "Enter" && applyFilters()}
               style={{ flex: "1 1 220px" }} />
        <input className="input" placeholder="Min $" value={minPrice}
               onChange={(e) => setMinPrice(e.target.value)} style={{ maxWidth: 100 }} />
        <input className="input" placeholder="Max $" value={maxPrice}
               onChange={(e) => setMaxPrice(e.target.value)} style={{ maxWidth: 100 }} />
        <button className="btn" onClick={applyFilters}>Apply</button>
      </div>

      <div className="muted" style={{ margin: "12px 0" }}>
        {total} {total === 1 ? "product" : "products"}
        {search && <> matching <strong style={{ color: "var(--fg)" }}>"{search}"</strong></>}
      </div>

      {items.length === 0 ? (
        <div className="card" style={{ textAlign: "center", padding: 40 }}>
          <p className="muted">No products found.</p>
        </div>
      ) : (
        <div className="grid">
          {items.map((p) => (
            <ProductCard
              key={p.id}
              product={p}
              wishlisted={wishIds.has(p.id)}
              onWishlistToggle={canShop ? () => toggleWish(p.id) : undefined}
            />
          ))}
        </div>
      )}

      <div className="flex" style={{ marginTop: 16, justifyContent: "center" }}>
        <button className="btn secondary" disabled={page <= 1} onClick={() => setPage(page - 1)}>Prev</button>
        <span className="muted">Page {page}</span>
        <button className="btn secondary" disabled={items.length < 12} onClick={() => setPage(page + 1)}>Next</button>
      </div>
    </>
  );
}
