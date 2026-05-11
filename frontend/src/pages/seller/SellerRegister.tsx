import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { sellerApi } from "../../api";

export default function SellerRegister() {
  const nav = useNavigate();
  const [form, setForm] = useState({
    store_name: "",
    description: "",
    logo_url: "",
    banner_url: "",
  });
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErr("");
    setBusy(true);
    try {
      await sellerApi.register({
        store_name: form.store_name,
        description: form.description || null,
        logo_url: form.logo_url || null,
        banner_url: form.banner_url || null,
      });
      nav("/seller/dashboard");
      window.location.reload();
    } catch (e: any) {
      setErr(e.response?.data?.detail || "Failed to register seller");
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      <h1>Become a Seller</h1>
      {err && <p className="error">{err}</p>}
      <form className="card" onSubmit={submit}>
        <div className="grid" style={{ gap: 8 }}>
          <label>Store name *
            <input className="input" value={form.store_name} required maxLength={150}
              onChange={(e) => setForm({ ...form, store_name: e.target.value })} />
          </label>
          <label>Description
            <textarea className="input" value={form.description} rows={4}
              onChange={(e) => setForm({ ...form, description: e.target.value })} />
          </label>
          <label>Logo URL
            <input className="input" value={form.logo_url}
              onChange={(e) => setForm({ ...form, logo_url: e.target.value })} />
          </label>
          <label>Banner URL
            <input className="input" value={form.banner_url}
              onChange={(e) => setForm({ ...form, banner_url: e.target.value })} />
          </label>
        </div>
        <div className="flex" style={{ gap: 8, marginTop: 12 }}>
          <button className="btn" type="submit" disabled={busy}>{busy ? "Creating..." : "Create seller profile"}</button>
        </div>
      </form>
    </>
  );
}
