import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api, chatApi, imagesApi, reviewsApi, wishlistApi, type ProductImage } from "../api";

type Variant = {
  id: string;
  sku: string;
  variant_name: string;
  attributes: Record<string, any> | null;
  price: number;
  stock_quantity: number;
  reserved_quantity: number;
};

export default function ProductDetail() {
  const { id } = useParams();
  const [p, setP] = useState<any>(null);
  const [reviews, setReviews] = useState<any[]>([]);
  const [variants, setVariants] = useState<Variant[]>([]);
  const [selectedVariantId, setSelectedVariantId] = useState<string>("");
  const [qty, setQty] = useState(1);
  const [msg, setMsg] = useState("");
  const [inWishlist, setInWishlist] = useState(false);
  const [contacting, setContacting] = useState(false);
  const [images, setImages] = useState<ProductImage[]>([]);
  const [mainImageUrl, setMainImageUrl] = useState<string | null>(null);
  const [votedIds, setVotedIds] = useState<Set<string>>(new Set());
  const hasToken = !!localStorage.getItem("access_token");
  const navigate = useNavigate();

  const messageSeller = async () => {
    if (!p?.seller_id || contacting) return;
    if (!hasToken) { navigate("/login"); return; }
    setContacting(true);
    try {
      await chatApi.start(p.seller_id);
      navigate("/chat");
    } catch (e: any) {
      setMsg(e.response?.data?.detail || "Could not start conversation");
    } finally {
      setContacting(false);
    }
  };

  useEffect(() => {
    if (!id) return;
    api.get(`/products/${id}`).then((r) => {
      setP(r.data);
      if (r.data?.image_url) setMainImageUrl(r.data.image_url);
    });
    api.get(`/products/${id}/reviews`).then((r) => setReviews(r.data.items));
    api.get<Variant[]>(`/products/${id}/variants`).then((r) => {
      setVariants(r.data);
      if (r.data.length > 0) setSelectedVariantId(r.data[0].id);
    }).catch(() => {});
    imagesApi.list(id).then((imgs) => {
      setImages(imgs);
      if (imgs.length > 0) setMainImageUrl(imgs[0].url);
    }).catch(() => {});
    if (hasToken) {
      wishlistApi.ids().then((ids) => setInWishlist(ids.includes(id))).catch(() => {});
    }
  }, [id]);

  const toggleVote = async (reviewId: string) => {
    if (!hasToken) return;
    try {
      if (votedIds.has(reviewId)) {
        const { helpful_count } = await reviewsApi.unvote(reviewId);
        setReviews((rs) => rs.map((r) => r.id === reviewId ? { ...r, helpful_count } : r));
        setVotedIds((s) => { const n = new Set(s); n.delete(reviewId); return n; });
      } else {
        const { helpful_count } = await reviewsApi.vote(reviewId, 1);
        setReviews((rs) => rs.map((r) => r.id === reviewId ? { ...r, helpful_count } : r));
        setVotedIds((s) => new Set(s).add(reviewId));
      }
    } catch {}
  };

  const toggleWishlist = async () => {
    if (!id) return;
    try {
      if (inWishlist) {
        await wishlistApi.remove(id);
        setInWishlist(false);
      } else {
        await wishlistApi.add(id);
        setInWishlist(true);
      }
    } catch {
      setMsg("Could not update wishlist");
    }
  };

  const addToCart = async () => {
    try {
      const body: any = { product_id: id, quantity: qty };
      if (selectedVariantId) body.variant_id = selectedVariantId;
      await api.post("/cart/items", body);
      setMsg("Added to cart");
    } catch (e: any) {
      setMsg(e.response?.data?.detail || "Error");
    }
  };

  if (!p) return <div>Loading…</div>;

  const showVariantPicker = variants.length > 1;
  const selectedVariant = variants.find((v) => v.id === selectedVariantId);

  return (
    <>
      <h1>{p.name}</h1>
      {(images.length > 0 || mainImageUrl) && (
        <div className="card">
          {mainImageUrl && (
            <img src={mainImageUrl} alt={p.name} style={{ width: "100%", maxHeight: 320, objectFit: "contain", borderRadius: 6 }} />
          )}
          {images.length > 1 && (
            <div className="flex" style={{ gap: 6, marginTop: 8, flexWrap: "wrap" }}>
              {images.map((img) => (
                <img
                  key={img.id}
                  src={img.url}
                  alt={img.alt || ""}
                  onClick={() => setMainImageUrl(img.url)}
                  style={{ width: 64, height: 64, objectFit: "cover", cursor: "pointer", borderRadius: 4, border: mainImageUrl === img.url ? "2px solid #1976d2" : "1px solid #ddd" }}
                />
              ))}
            </div>
          )}
        </div>
      )}
      <div className="card">
        <div className="price" style={{ fontSize: 24 }}>${p.price}</div>
        <p>{p.description}</p>
        {p.seller_store_name && p.seller_slug && (
          <div className="muted" style={{ marginBottom: 6 }}>
            Sold by <Link to={`/store/${p.seller_slug}`}>{p.seller_store_name}</Link>
            {" · "}
            <button className="btn secondary" onClick={messageSeller} disabled={contacting} style={{ padding: "2px 8px", fontSize: 13 }}>
              {contacting ? "Opening…" : "Message seller"}
            </button>
          </div>
        )}
        <div className="muted">Available: {p.available_quantity}</div>
        <div className="muted">
          Rating: {p.average_rating ? p.average_rating.toFixed(2) : "—"} ({p.reviews_count} reviews)
        </div>
        {showVariantPicker && (
          <div style={{ marginTop: 12 }}>
            <label className="muted">Variant: </label>
            <select
              className="input"
              value={selectedVariantId}
              onChange={(e) => setSelectedVariantId(e.target.value)}
            >
              {variants.map((v) => (
                <option key={v.id} value={v.id}>{v.variant_name}</option>
              ))}
            </select>
            {selectedVariant && (
              <div className="muted" style={{ marginTop: 6 }}>
                {selectedVariant.variant_name} · ${selectedVariant.price.toFixed(2)} · Stock: {selectedVariant.stock_quantity - selectedVariant.reserved_quantity}
              </div>
            )}
          </div>
        )}
        <div className="flex" style={{ marginTop: 12 }}>
          <input className="input" type="number" min={1} value={qty}
                 onChange={(e) => setQty(parseInt(e.target.value || "1"))} style={{ maxWidth: 80 }} />
          <button className="btn" onClick={addToCart}>Add to cart</button>
          {hasToken && (
            <button className="btn secondary" onClick={toggleWishlist}>
              {inWishlist ? "♥ Saved" : "♡ Save"}
            </button>
          )}
        </div>
        {msg && <p className="muted">{msg}</p>}
      </div>
      <h2>Reviews</h2>
      {reviews.length === 0 && <p className="muted">No reviews yet.</p>}
      {reviews.map((r) => (
        <div key={r.id} className="card">
          <div className="flex" style={{ gap: 8, alignItems: "center" }}>
            <strong>★ {r.rating}</strong>
            {r.verified_purchase && <span style={{ background: "#e0f5e9", color: "#1b5e20", borderRadius: 4, padding: "1px 6px", fontSize: 12 }}>✓ Verified purchase</span>}
            <span className="muted">{new Date(r.created_at).toLocaleDateString()}</span>
          </div>
          <p>{r.comment}</p>
          {r.seller_response && (
            <div style={{ background: "#f5f5f5", borderLeft: "3px solid #1976d2", padding: 8, marginTop: 6 }}>
              <strong style={{ fontSize: 13 }}>Seller response:</strong>
              <div style={{ fontSize: 14 }}>{r.seller_response}</div>
            </div>
          )}
          <div style={{ marginTop: 6 }}>
            {hasToken && (
              <button className="btn secondary" onClick={() => toggleVote(r.id)} style={{ padding: "2px 8px", fontSize: 13 }}>
                👍 {r.helpful_count ?? 0}
              </button>
            )}
            {!hasToken && <span className="muted" style={{ fontSize: 13 }}>👍 {r.helpful_count ?? 0}</span>}
          </div>
        </div>
      ))}
    </>
  );
}
