import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, addressApi, couponsApi, formatAddress, type Address } from "../api";

export default function Checkout() {
  const [addresses, setAddresses] = useState<Address[]>([]);
  const [selectedId, setSelectedId] = useState<string>("");
  const [showManual, setShowManual] = useState(false);
  const [addr, setAddr] = useState("");
  const [err, setErr] = useState("");
  const [loaded, setLoaded] = useState(false);
  const [cartTotal, setCartTotal] = useState<number>(0);
  const [couponCode, setCouponCode] = useState("");
  const [couponMsg, setCouponMsg] = useState("");
  const [discount, setDiscount] = useState<number>(0);
  const nav = useNavigate();

  useEffect(() => {
    (async () => {
      try {
        const list = await addressApi.list();
        setAddresses(list);
        const def = list.find((a) => a.is_default) || list[0];
        if (def) setSelectedId(def.id);
      } catch {}
      try {
        const r = await api.get("/cart");
        setCartTotal(Number(r.data.total || 0));
      } catch {}
      setLoaded(true);
    })();
  }, []);

  const applyCoupon = async () => {
    setCouponMsg("");
    setDiscount(0);
    if (!couponCode.trim()) { setCouponMsg("Enter a code"); return; }
    try {
      const res = await couponsApi.validate(couponCode.trim(), cartTotal);
      if (res.valid) {
        setDiscount(Number(res.discount_amount));
        setCouponMsg(`Applied: -$${Number(res.discount_amount).toFixed(2)}`);
      } else {
        setCouponMsg(res.message || "Invalid coupon");
      }
    } catch (e: any) {
      setCouponMsg(e.response?.data?.detail || "Could not validate coupon");
    }
  };

  const selected = addresses.find((a) => a.id === selectedId) || null;

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErr("");
    let shipping_address = "";
    if (addr.trim()) {
      shipping_address = addr;
    } else if (selected) {
      shipping_address = formatAddress(selected);
    } else {
      shipping_address = addr;
    }
    try {
      const body: any = { shipping_address };
      if (discount > 0 && couponCode.trim()) body.coupon_code = couponCode.trim();
      const { data } = await api.post("/orders", body);
      nav(`/orders/${data.id}`);
    } catch (e: any) {
      setErr(e.response?.data?.detail || "Checkout failed");
    }
  };

  if (!loaded) {
    return (
      <>
        <h1>Checkout</h1>
        <p className="muted">Loading...</p>
      </>
    );
  }

  const hasSaved = addresses.length > 0;

  return (
    <>
      <h1>Checkout</h1>
      <form className="card" onSubmit={submit}>
        {hasSaved ? (
          <>
            <label>Shipping address</label>
            <select
              className="input"
              value={selectedId}
              onChange={(e) => setSelectedId(e.target.value)}
            >
              {addresses.map((a) => (
                <option key={a.id} value={a.id}>
                  {(a.label || a.recipient_name) + " — " + a.line1 + ", " + a.city}
                </option>
              ))}
            </select>
            {selected && (
              <pre className="muted" style={{ whiteSpace: "pre-wrap", fontFamily: "inherit", marginTop: 8 }}>
                {formatAddress(selected)}
              </pre>
            )}
            <div style={{ marginTop: 8 }}>
              <button
                type="button"
                className="btn secondary"
                onClick={() => setShowManual((v) => !v)}
              >
                {showManual ? "Use selected address" : "+ Use a different address"}
              </button>
            </div>
            {showManual && (
              <div style={{ marginTop: 8 }}>
                <label>Enter address manually (overrides selection)</label>
                <textarea
                  className="input"
                  rows={3}
                  value={addr}
                  onChange={(e) => setAddr(e.target.value)}
                />
              </div>
            )}
          </>
        ) : (
          <>
            <label>Shipping address</label>
            <textarea
              className="input"
              rows={3}
              value={addr}
              onChange={(e) => setAddr(e.target.value)}
              required
            />
            <p className="muted" style={{ marginTop: 8 }}>
              Tip: save addresses on the Addresses page for faster checkout
            </p>
          </>
        )}
        <div style={{ marginTop: 16, borderTop: "1px solid #eee", paddingTop: 12 }}>
          <label>Coupon code</label>
          <div className="flex" style={{ gap: 8 }}>
            <input
              className="input"
              placeholder="Enter code"
              value={couponCode}
              onChange={(e) => setCouponCode(e.target.value)}
              style={{ flex: 1 }}
            />
            <button type="button" className="btn secondary" onClick={applyCoupon}>Apply</button>
          </div>
          {couponMsg && <p className="muted" style={{ marginTop: 4 }}>{couponMsg}</p>}
          {cartTotal > 0 && (
            <div className="muted" style={{ marginTop: 8 }}>
              Subtotal: ${cartTotal.toFixed(2)}
              {discount > 0 && <> &nbsp;·&nbsp; Discount: -${discount.toFixed(2)} &nbsp;·&nbsp; <strong>Total: ${Math.max(0, cartTotal - discount).toFixed(2)}</strong></>}
            </div>
          )}
        </div>
        {err && <p className="error">{err}</p>}
        <button className="btn" type="submit" style={{ marginTop: 12 }}>Place order</button>
      </form>
    </>
  );
}
