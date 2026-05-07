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
        {sales.map((s) => (
          <div key={s.id} className="card">
            <code>{s.product_id.slice(0, 8)}</code>
            <div className="price">${s.sale_price} <s className="muted">${s.original_price}</s></div>
            <div className="muted">Stock left: <strong>{s.remaining_stock}</strong> / {s.initial_stock}</div>
            <div className="muted">Until: {new Date(s.end_at).toLocaleString()}</div>
            <button className="btn" onClick={() => claim(s.id)} disabled={s.remaining_stock <= 0}>Claim</button>
          </div>
        ))}
      </div>
    </>
  );
}
