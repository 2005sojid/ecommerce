import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api";

export default function Checkout() {
  const [addr, setAddr] = useState("");
  const [err, setErr] = useState("");
  const nav = useNavigate();

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErr("");
    try {
      const { data } = await api.post("/orders", { shipping_address: addr });
      nav(`/orders/${data.id}`);
    } catch (e: any) {
      setErr(e.response?.data?.detail || "Checkout failed");
    }
  };

  return (
    <>
      <h1>Checkout</h1>
      <form className="card" onSubmit={submit}>
        <label>Shipping address</label>
        <textarea className="input" rows={3} value={addr} onChange={(e) => setAddr(e.target.value)} required />
        {err && <p className="error">{err}</p>}
        <button className="btn" type="submit" style={{ marginTop: 12 }}>Place order</button>
      </form>
    </>
  );
}
