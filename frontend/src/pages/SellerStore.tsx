import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { chatApi, sellerApi, type Seller } from "../api";
import ProductCard from "../components/ProductCard";
import { useAuth } from "../useAuth";

export default function SellerStore() {
  const { slug } = useParams<{ slug: string }>();
  const [seller, setSeller] = useState<Seller | null>(null);
  const [products, setProducts] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(true);
  const [contacting, setContacting] = useState(false);
  const navigate = useNavigate();
  const hasToken = !!localStorage.getItem("access_token");
  const { user } = useAuth();
  const canContact = !user || user.role === "customer";
  const per_page = 12;

  const contactSeller = async () => {
    if (!seller || contacting) return;
    if (!hasToken) { navigate("/login"); return; }
    setContacting(true);
    try {
      await chatApi.start(seller.id);
      navigate("/chat");
    } catch (e: any) {
      setErr(e.response?.data?.detail || "Could not start conversation");
    } finally {
      setContacting(false);
    }
  };

  useEffect(() => {
    if (!slug) return;
    setLoading(true);
    Promise.all([sellerApi.publicStore(slug), sellerApi.publicProducts(slug, page, per_page)])
      .then(([s, p]) => { setSeller(s); setProducts(p.items); setTotal(p.total); })
      .catch((e) => setErr(e.response?.data?.detail || "Store not found"))
      .finally(() => setLoading(false));
  }, [slug, page]);

  if (loading) return <p className="muted">Loading...</p>;
  if (err) return <p className="error">{err}</p>;
  if (!seller) return null;

  return (
    <>
      {seller.banner_url && (
        <div style={{ width: "100%", height: 180, overflow: "hidden", borderRadius: 8, marginBottom: 12 }}>
          <img src={seller.banner_url} alt="banner" style={{ width: "100%", height: "100%", objectFit: "cover" }} />
        </div>
      )}
      <div className="card flex" style={{ gap: 16, alignItems: "center" }}>
        {seller.logo_url && (
          <img src={seller.logo_url} alt="logo" style={{ width: 64, height: 64, borderRadius: 8, objectFit: "cover" }} />
        )}
        <div>
          <h1 style={{ margin: 0 }}>{seller.store_name}</h1>
          {seller.is_verified && <span className="muted">Verified</span>}
          {seller.description && <p className="muted" style={{ marginTop: 4 }}>{seller.description}</p>}
        </div>
        {canContact && (
          <span style={{ marginLeft: "auto" }}>
            <button className="btn" onClick={contactSeller} disabled={contacting}>
              {contacting ? "Opening…" : "Contact seller"}
            </button>
          </span>
        )}
      </div>

      <h2 style={{ marginTop: 16 }}>Products</h2>
      <div className="muted">Total: {total}</div>
      {products.length === 0 ? (
        <p className="muted">No products yet.</p>
      ) : (
        <div className="grid">
          {products.map((p) => (
            <ProductCard key={p.id} product={p} />
          ))}
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
