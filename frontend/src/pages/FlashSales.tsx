import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, addressApi, formatAddress, type Address } from "../api";
import { useAuth } from "../useAuth";

export default function FlashSales() {
  const [sales, setSales] = useState<any[]>([]);
  const [addresses, setAddresses] = useState<Address[]>([]);
  const [selectedAddrId, setSelectedAddrId] = useState<string>("");
  const [msg, setMsg] = useState("");
  const [claimingId, setClaimingId] = useState<string | null>(null);
  const { user } = useAuth();
  const nav = useNavigate();

  const load = () => api.get("/flash-sales/active").then((r) => setSales(r.data)).catch(() => {});

  useEffect(() => {
    load();
    const t = setInterval(load, 10000);
    return () => clearInterval(t);
  }, []);

  useEffect(() => {
    if (user?.role !== "customer") return;
    addressApi.list().then((list) => {
      setAddresses(list);
      const def = list.find((a) => a.is_default) || list[0];
      if (def) setSelectedAddrId(def.id);
    }).catch(() => {});
  }, [user]);

  const claim = async (saleId: string) => {
    if (claimingId) return;
    setMsg("");
    if (!user) { nav("/login"); return; }
    if (user.role !== "customer") { setMsg("Only customers can claim flash sales"); return; }
    const selected = addresses.find((a) => a.id === selectedAddrId);
    if (!selected) {
      setMsg("Please add a shipping address first");
      nav("/addresses");
      return;
    }
    setClaimingId(saleId);
    try {
      const { data } = await api.post(`/flash-sales/${saleId}/claim`, { shipping_address: formatAddress(selected) });
      setSales((cur) => cur.map((s) => s.id === saleId ? { ...s, remaining_stock: data.remaining_stock } : s));
      nav(`/orders/${data.order_id}`);
    } catch (e: any) {
      setMsg(e.response?.data?.detail || "Failed");
    } finally {
      setClaimingId(null);
    }
  };

  return (
    <>
      <h1>⚡ Flash Sales</h1>
      {user?.role === "customer" && addresses.length > 0 && (
        <div className="card" style={{ marginBottom: 12 }}>
          <label>Ship to</label>
          <select className="input" value={selectedAddrId} onChange={(e) => setSelectedAddrId(e.target.value)}>
            {addresses.map((a) => (
              <option key={a.id} value={a.id}>
                {(a.label || a.recipient_name) + " — " + a.line1 + ", " + a.city}
              </option>
            ))}
          </select>
        </div>
      )}
      {msg && <p className="error">{msg}</p>}
      {sales.length === 0 && <p className="muted">No active flash sales right now.</p>}
      <div className="grid">
        {sales.map((s) => {
          const pct = s.original_price > 0
            ? Math.round((1 - Number(s.sale_price) / Number(s.original_price)) * 100)
            : 0;
          const isClaiming = claimingId === s.id;
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
                <button className="btn" onClick={() => claim(s.id)}
                        disabled={s.remaining_stock <= 0 || isClaiming || !!claimingId}
                        style={{ width: "100%", opacity: (isClaiming || s.remaining_stock <= 0) ? 0.6 : 1 }}>
                  {isClaiming ? "Claiming…" : "Claim"}
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </>
  );
}
