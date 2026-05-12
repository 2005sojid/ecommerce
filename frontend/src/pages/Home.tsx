import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, wishlistApi } from "../api";
import ProductCard from "../components/ProductCard";
import { useAuth } from "../useAuth";

type Cat = { id: string; name: string; slug: string; parent_id: string | null };

export default function Home() {
  const [items, setItems] = useState<any[] | null>(null);
  const [cats, setCats] = useState<Cat[]>([]);
  const [flash, setFlash] = useState<any[]>([]);
  const [stats, setStats] = useState<{ products: number; sellers: number }>({ products: 0, sellers: 0 });
  const [wishIds, setWishIds] = useState<Set<string>>(new Set());
  const { user } = useAuth();
  const canShop = user?.role === "customer";

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
    if (canShop) wishlistApi.ids().then((ids) => setWishIds(new Set(ids))).catch(() => {});
    api.get("/products?per_page=8&sort_by=created_at&sort_order=desc")
      .then((r) => { setItems(r.data.items); setStats((s) => ({ ...s, products: r.data.total })); })
      .catch(() => setItems([]));
    api.get<Cat[]>("/categories").then((r) => setCats(Array.isArray(r.data) ? r.data : [])).catch(() => {});
    api.get("/flash-sales/active").then((r) => setFlash(r.data)).catch(() => {});
  }, [canShop]);

  return (
    <>
      {/* Category pill row */}
      {cats.length > 0 && (
        <div className="pill-tabs scroll-x">
          <Link to="/products" className="pill active">All</Link>
          {cats.map((c) => (
            <Link key={c.id} to={`/products?category=${c.id}`} className="pill">{c.name}</Link>
          ))}
          <Link to="/flash-sales" className="pill">Flash sales <span style={{ color: "#ef4444" }}>⚡</span></Link>
          <Link to="/products?sort_by=created_at&sort_order=desc" className="pill">New arrivals</Link>
        </div>
      )}

      {/* Hero card */}
      <section className="hero">
        <div>
          <h1>Your marketplace, one click away</h1>
          <p>Discover {stats.products || "500+"} products from verified sellers. Free shipping on orders over $50. Flash sales daily.</p>
          <Link to="/flash-sales" className="btn">⚡ Shop flash sales</Link>
        </div>
        <div className="hero-stats">
          <div className="hero-stat"><strong>{stats.products || "500+"}</strong><span>Products</span></div>
          <div className="hero-stat"><strong>{stats.sellers || "25"}</strong><span>Sellers</span></div>
          <div className="hero-stat"><strong>4.8</strong><span>Avg rating</span></div>
        </div>
      </section>

      {/* Flash sales */}
      {flash.length > 0 && (
        <>
          <div className="section-header">
            <h2><span style={{ color: "#ef4444" }}>⚡</span> Flash sales</h2>
            <Link to="/flash-sales" className="muted">View all →</Link>
          </div>
          <div className="grid">
            {flash.slice(0, 3).map((s) => {
              const pct = s.original_price > 0
                ? Math.round((1 - Number(s.sale_price) / Number(s.original_price)) * 100)
                : 0;
              return (
                <Link key={s.id} to="/flash-sales" className="product-card">
                  <div className="product-image">
                    {pct > 0 && <span className="discount-badge">-{pct}%</span>}
                    {s.product_image_url
                      ? <img src={s.product_image_url} alt={s.product_name || ""} />
                      : <span className="product-image-placeholder">⚡</span>}
                  </div>
                  <div className="product-body">
                    <strong>{s.product_name || "Flash deal"}</strong>
                    <div className="muted" style={{ marginTop: 4 }}>
                      Stock left: <strong style={{ color: "var(--fg)" }}>{s.remaining_stock}</strong> / {s.initial_stock}
                    </div>
                    <div style={{ marginTop: 6 }}>
                      <span className="price">${s.sale_price}</span> <s className="muted">${s.original_price}</s>
                    </div>
                  </div>
                </Link>
              );
            })}
          </div>
        </>
      )}

      {/* Featured products */}
      <div className="section-header">
        <h2>⭐ Featured products</h2>
        <Link to="/products" className="muted">View all →</Link>
      </div>

      {items === null && (
        <div className="grid">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="product-card">
              <div className="skeleton" style={{ aspectRatio: "1 / 1" }} />
              <div className="product-body">
                <div className="skeleton" style={{ height: 16, width: "70%", marginBottom: 8 }} />
                <div className="skeleton" style={{ height: 16, width: "40%" }} />
              </div>
            </div>
          ))}
        </div>
      )}

      {items !== null && items.length === 0 && (
        <div className="card" style={{ textAlign: "center", padding: 40 }}>
          <p className="muted">No products available yet.</p>
        </div>
      )}

      {items !== null && items.length > 0 && (
        <div className="grid">
          {items.map((p, idx) => (
            <ProductCard
              key={p.id}
              product={p}
              featured={idx < 2}
              wishlisted={wishIds.has(p.id)}
              onWishlistToggle={canShop ? () => toggleWish(p.id) : undefined}
            />
          ))}
        </div>
      )}
    </>
  );
}
