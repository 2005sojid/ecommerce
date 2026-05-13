import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api";

export default function Cart() {
  const [cart, setCart] = useState<any>(null);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const nav = useNavigate();

  const load = () => {
    api.get("/cart").then((r) => setCart(r.data)).catch(() => setCart({ items: [], total: 0 }));
  };
  useEffect(load, []);

  const update = async (pid: string, qty: number, variantId?: string | null) => {
    if (busy) return;
    setErr("");
    setBusy(true);
    try {
      const qs = variantId ? `?variant_id=${variantId}` : "";
      if (qty <= 0) {
        await api.delete(`/cart/items/${pid}${qs}`);
      } else {
        await api.patch(`/cart/items/${pid}${qs}`, { quantity: qty });
      }
      load();
    } catch (e: any) {
      setErr(e.response?.data?.detail || "Could not update cart");
    } finally {
      setBusy(false);
    }
  };

  const remove = async (pid: string, variantId?: string | null) => {
    if (busy) return;
    setBusy(true);
    setErr("");
    try {
      const qs = variantId ? `?variant_id=${variantId}` : "";
      await api.delete(`/cart/items/${pid}${qs}`);
      load();
    } catch (e: any) {
      setErr(e.response?.data?.detail || "Could not remove item");
    } finally {
      setBusy(false);
    }
  };

  const clear = async () => {
    if (busy) return;
    if (!window.confirm("Clear all items from cart?")) return;
    setBusy(true);
    setErr("");
    try {
      await api.delete("/cart");
      load();
    } catch (e: any) {
      setErr(e.response?.data?.detail || "Could not clear cart");
    } finally {
      setBusy(false);
    }
  };

  if (!cart) return <div>Loading…</div>;
  if (cart.items.length === 0) return <p>Your cart is empty.</p>;

  return (
    <>
      <h1>Cart</h1>
      {err && <p className="error">{err}</p>}
      <table className="card">
        <thead>
          <tr><th>Product</th><th>Price</th><th>Qty</th><th>Total</th><th></th></tr>
        </thead>
        <tbody>
          {cart.items.map((it: any) => (
            <tr key={`${it.product_id}:${it.variant_id || ""}`}>
              <td>{it.name}{it.variant_name ? ` — ${it.variant_name}` : ""}</td>
              <td>${it.price}</td>
              <td>
                <input className="input" type="number" min={0} value={it.quantity}
                       disabled={busy}
                       onChange={(e) => update(it.product_id, parseInt(e.target.value || "0"), it.variant_id)}
                       style={{ width: 70 }} />
              </td>
              <td className="price">${it.line_total}</td>
              <td><button className="btn danger" disabled={busy} onClick={() => remove(it.product_id, it.variant_id)}>×</button></td>
            </tr>
          ))}
        </tbody>
      </table>
      <h3>Total: ${cart.total}</h3>
      <div className="flex">
        <button className="btn" onClick={() => nav("/checkout")} disabled={busy}>Checkout</button>
        <button className="btn secondary" onClick={clear} disabled={busy}>Clear cart</button>
      </div>
    </>
  );
}
