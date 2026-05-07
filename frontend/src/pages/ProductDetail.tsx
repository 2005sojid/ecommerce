import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../api";

export default function ProductDetail() {
  const { id } = useParams();
  const [p, setP] = useState<any>(null);
  const [reviews, setReviews] = useState<any[]>([]);
  const [qty, setQty] = useState(1);
  const [msg, setMsg] = useState("");

  useEffect(() => {
    api.get(`/products/${id}`).then((r) => setP(r.data));
    api.get(`/products/${id}/reviews`).then((r) => setReviews(r.data.items));
  }, [id]);

  const addToCart = async () => {
    try {
      await api.post("/cart/items", { product_id: id, quantity: qty });
      setMsg("Added to cart");
    } catch (e: any) {
      setMsg(e.response?.data?.detail || "Error");
    }
  };

  if (!p) return <div>Loading…</div>;

  return (
    <>
      <h1>{p.name}</h1>
      <div className="card">
        <div className="price" style={{ fontSize: 24 }}>${p.price}</div>
        <p>{p.description}</p>
        <div className="muted">Available: {p.available_quantity}</div>
        <div className="muted">
          Rating: {p.average_rating ? p.average_rating.toFixed(2) : "—"} ({p.reviews_count} reviews)
        </div>
        <div className="flex" style={{ marginTop: 12 }}>
          <input className="input" type="number" min={1} value={qty}
                 onChange={(e) => setQty(parseInt(e.target.value || "1"))} style={{ maxWidth: 80 }} />
          <button className="btn" onClick={addToCart}>Add to cart</button>
        </div>
        {msg && <p className="muted">{msg}</p>}
      </div>
      <h2>Reviews</h2>
      {reviews.length === 0 && <p className="muted">No reviews yet.</p>}
      {reviews.map((r) => (
        <div key={r.id} className="card">
          <strong>★ {r.rating}</strong> <span className="muted">{new Date(r.created_at).toLocaleDateString()}</span>
          <p>{r.comment}</p>
        </div>
      ))}
    </>
  );
}
