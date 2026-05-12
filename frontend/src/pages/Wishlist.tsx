import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { wishlistApi } from "../api";

export default function Wishlist() {
  const [items, setItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const load = () => {
    setLoading(true);
    wishlistApi.list().then((d) => {
      setItems(d.items);
      setLoading(false);
    }).catch(() => setLoading(false));
  };

  useEffect(load, []);

  const remove = async (product_id: string) => {
    await wishlistApi.remove(product_id);
    setItems((prev) => prev.filter((i) => i.product_id !== product_id));
  };

  if (loading) return <div>Loading…</div>;

  return (
    <>
      <h1>My Wishlist</h1>
      {items.length === 0 ? (
        <div className="card" style={{ textAlign: "center", padding: 48 }}>
          <h3 style={{ marginBottom: 4 }}>Your wishlist is empty</h3>
          <p className="muted">Save products you love and find them here later.</p>
          <Link to="/products" className="btn" style={{ marginTop: 12 }}>Browse products</Link>
        </div>
      ) : (
        <div className="grid">
          {items.map((i) => (
            <div key={i.id} className="card">
              <strong>{i.product_name}</strong>
              <div className="price">${i.product_price}</div>
              <div className="flex" style={{ marginTop: 12 }}>
                <Link to={`/products/${i.product_id}`} className="btn secondary">View</Link>
                <button className="btn" onClick={() => remove(i.product_id)}>Remove</button>
              </div>
            </div>
          ))}
        </div>
      )}
    </>
  );
}
