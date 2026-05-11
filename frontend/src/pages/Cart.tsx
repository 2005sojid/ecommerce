import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api";

export default function Cart() {
  const [cart, setCart] = useState<any>(null);
  const nav = useNavigate();

  const load = () => {
    api.get("/cart").then((r) => setCart(r.data)).catch(() => setCart({ items: [], total: 0 }));
  };
  useEffect(load, []);

  const update = async (pid: string, qty: number, variantId?: string | null) => {
    const qs = variantId ? `?variant_id=${variantId}` : "";
    await api.patch(`/cart/items/${pid}${qs}`, { quantity: qty });
    load();
  };
  const remove = async (pid: string, variantId?: string | null) => {
    const qs = variantId ? `?variant_id=${variantId}` : "";
    await api.delete(`/cart/items/${pid}${qs}`);
    load();
  };
  const clear = async () => {
    await api.delete("/cart");
    load();
  };

  if (!cart) return <div>Loading…</div>;
  if (cart.items.length === 0) return <p>Your cart is empty.</p>;

  return (
    <>
      <h1>Cart</h1>
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
                       onChange={(e) => update(it.product_id, parseInt(e.target.value || "0"), it.variant_id)}
                       style={{ width: 70 }} />
              </td>
              <td className="price">${it.line_total}</td>
              <td><button className="btn danger" onClick={() => remove(it.product_id, it.variant_id)}>×</button></td>
            </tr>
          ))}
        </tbody>
      </table>
      <h3>Total: ${cart.total}</h3>
      <div className="flex">
        <button className="btn" onClick={() => nav("/checkout")}>Checkout</button>
        <button className="btn secondary" onClick={clear}>Clear cart</button>
      </div>
    </>
  );
}
