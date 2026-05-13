import { useEffect, useState } from "react";
import { sellerApi } from "../../api";

export default function SellerSettings() {
  const [form, setForm] = useState({ store_name: "", description: "", logo_url: "", banner_url: "" });
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");
  const [msg, setMsg] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    sellerApi.me()
      .then((s) => setForm({
        store_name: s.store_name,
        description: s.description || "",
        logo_url: s.logo_url || "",
        banner_url: s.banner_url || "",
      }))
      .catch((e) => setErr(e.response?.data?.detail || "Failed to load"))
      .finally(() => setLoading(false));
  }, []);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (busy) return;
    setErr(""); setMsg("");
    setBusy(true);
    try {
      await sellerApi.update({
        store_name: form.store_name,
        description: form.description || null,
        logo_url: form.logo_url || null,
        banner_url: form.banner_url || null,
      });
      setMsg("Saved");
    } catch (e: any) {
      setErr(e.response?.data?.detail || "Failed to save");
    } finally {
      setBusy(false);
    }
  };

  if (loading) return <p className="muted">Loading...</p>;

  return (
    <>
      <h1>Seller Settings</h1>
      {err && <p className="error">{err}</p>}
      {msg && <p className="muted">{msg}</p>}
      <form className="card" onSubmit={submit}>
        <div className="grid" style={{ gap: 8 }}>
          <label>Store name *
            <input className="input" value={form.store_name} required maxLength={150}
              onChange={(e) => setForm({ ...form, store_name: e.target.value })} />
          </label>
          <label>Description
            <textarea className="input" rows={4} value={form.description}
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
          <button className="btn" type="submit" disabled={busy} style={{ opacity: busy ? 0.6 : 1 }}>
            {busy ? "Saving…" : "Save"}
          </button>
        </div>
      </form>
    </>
  );
}
