import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api";

export default function FlashSales() {
  const [sales, setSales] = useState<any[]>([]);
  const [msg, setMsg] = useState("");
  const nav = useNavigate();

  useEffect(() => {
    api.get("/flash-sales/active").then((r) => setSales(r.data));
  }, []);

  const claim = async (saleId: string) => {
    setMsg("");
    try {
      const { data } = await api.post(`/flash-sales/${saleId}/claim`, { shipping_address: "Default flash address" });
      nav(`/orders/${data.order_id}`);
    } catch (e: any) {
      setMsg(e.response?.data?.detail || "Failed");
    }
  };

  return (
    <>
      <h1>⚡ Flash Sales</h1>
      {msg && <p className="error">{msg}</p>}
      {sales.length === 0 && <p className="muted">No active flash sales right now.</p>}
      <div className="grid">
        {sales.map((s) => {
          const pct = s.original_price > 0
            ? Math.round((1 - Number(s.sale_price) / Number(s.original_price)) * 100)
            : 0;
          return (
            <div key={s.id} className="product-card">
              <div className="product-image">
                {pct > 0 && <span className="discount-badge">-{pct}%</span>}
                {s.product_image_url ? (
                  <img src={s.product_image_url} alt={s.product_name || ""} />
                ) : (
                  <span className="product-image-placeholder">⚡</span>
                )}
              </div>
              <div className="product-body">
                <strong>{s.product_name || "Unnamed product"}</strong>
                <div style={{ marginTop: 6 }}>
                  <span className="price">${s.sale_price}</span>{" "}
                  <s className="muted">${s.original_price}</s>
                </div>
                <div className="muted" style={{ marginTop: 4 }}>
                  Stock left: <strong style={{ color: "var(--fg)" }}>{s.remaining_stock}</strong> / {s.initial_stock}
                </div>
                <div className="muted" style={{ marginBottom: 12 }}>
                  Until: {new Date(s.end_at).toLocaleString()}
                </div>
                <button className="btn" onClick={() => claim(s.id)} disabled={s.remaining_stock <= 0} style={{ width: "100%" }}>
                  Claim
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </>
  );
}
