import { useEffect, useState } from "react";
import { addressApi, formatAddress, type Address } from "../api";

type FormState = {
  label: string;
  recipient_name: string;
  line1: string;
  line2: string;
  city: string;
  state: string;
  postal_code: string;
  country: string;
  phone: string;
  is_default: boolean;
};

const emptyForm: FormState = {
  label: "",
  recipient_name: "",
  line1: "",
  line2: "",
  city: "",
  state: "",
  postal_code: "",
  country: "US",
  phone: "",
  is_default: false,
};

export default function Addresses() {
  const [items, setItems] = useState<Address[]>([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [form, setForm] = useState<FormState>(emptyForm);

  const load = async () => {
    setLoading(true);
    try {
      const data = await addressApi.list();
      setItems(data);
    } catch (e: any) {
      setErr(e.response?.data?.detail || "Failed to load addresses");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const startAdd = () => {
    setEditingId(null);
    setForm(emptyForm);
    setShowForm(true);
  };

  const startEdit = (a: Address) => {
    setEditingId(a.id);
    setForm({
      label: a.label || "",
      recipient_name: a.recipient_name,
      line1: a.line1,
      line2: a.line2 || "",
      city: a.city,
      state: a.state || "",
      postal_code: a.postal_code,
      country: a.country,
      phone: a.phone || "",
      is_default: a.is_default,
    });
    setShowForm(true);
  };

  const cancelForm = () => {
    setShowForm(false);
    setEditingId(null);
    setForm(emptyForm);
  };

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErr("");
    const payload: Partial<Address> = {
      label: form.label || null,
      recipient_name: form.recipient_name,
      line1: form.line1,
      line2: form.line2 || null,
      city: form.city,
      state: form.state || null,
      postal_code: form.postal_code,
      country: form.country.toUpperCase(),
      phone: form.phone || null,
      is_default: form.is_default,
    };
    try {
      if (editingId) {
        await addressApi.update(editingId, payload);
      } else {
        await addressApi.create(payload);
      }
      cancelForm();
      await load();
    } catch (e: any) {
      setErr(e.response?.data?.detail || "Failed to save address");
    }
  };

  const onDelete = async (id: string) => {
    if (!confirm("Delete this address?")) return;
    try {
      await addressApi.remove(id);
      await load();
    } catch (e: any) {
      setErr(e.response?.data?.detail || "Failed to delete");
    }
  };

  const onSetDefault = async (id: string) => {
    try {
      await addressApi.setDefault(id);
      await load();
    } catch (e: any) {
      setErr(e.response?.data?.detail || "Failed to set default");
    }
  };

  return (
    <>
      <h1>My Addresses</h1>
      {err && <p className="error">{err}</p>}
      {loading ? (
        <p className="muted">Loading...</p>
      ) : items.length === 0 ? (
        <p className="muted">You have no saved addresses yet.</p>
      ) : (
        <div className="grid" style={{ gap: 12 }}>
          {items.map((a) => (
            <div key={a.id} className="card">
              <div className="flex" style={{ justifyContent: "space-between", alignItems: "center" }}>
                <strong>{a.label || a.recipient_name}</strong>
                {a.is_default && <span className="muted" style={{ border: "1px solid #ccc", padding: "2px 8px", borderRadius: 4 }}>Default</span>}
              </div>
              <pre style={{ whiteSpace: "pre-wrap", fontFamily: "inherit", margin: "8px 0" }}>{formatAddress(a)}</pre>
              <div className="flex" style={{ gap: 8 }}>
                <button className="btn secondary" onClick={() => startEdit(a)}>Edit</button>
                <button className="btn secondary" onClick={() => onDelete(a.id)}>Delete</button>
                {!a.is_default && <button className="btn" onClick={() => onSetDefault(a.id)}>Set default</button>}
              </div>
            </div>
          ))}
        </div>
      )}

      <div style={{ marginTop: 16 }}>
        {!showForm && <button className="btn" onClick={startAdd}>Add new address</button>}
      </div>

      {showForm && (
        <form className="card" onSubmit={submit} style={{ marginTop: 16 }}>
          <h2>{editingId ? "Edit address" : "Add address"}</h2>
          <div className="grid" style={{ gap: 8 }}>
            <label>Label (e.g. Home, Work)
              <input className="input" value={form.label} onChange={(e) => setForm({ ...form, label: e.target.value })} maxLength={50} />
            </label>
            <label>Recipient name *
              <input className="input" value={form.recipient_name} onChange={(e) => setForm({ ...form, recipient_name: e.target.value })} required maxLength={150} />
            </label>
            <label>Address line 1 *
              <input className="input" value={form.line1} onChange={(e) => setForm({ ...form, line1: e.target.value })} required maxLength={255} />
            </label>
            <label>Address line 2
              <input className="input" value={form.line2} onChange={(e) => setForm({ ...form, line2: e.target.value })} maxLength={255} />
            </label>
            <label>City *
              <input className="input" value={form.city} onChange={(e) => setForm({ ...form, city: e.target.value })} required maxLength={100} />
            </label>
            <label>State / Region
              <input className="input" value={form.state} onChange={(e) => setForm({ ...form, state: e.target.value })} maxLength={100} />
            </label>
            <label>Postal code *
              <input className="input" value={form.postal_code} onChange={(e) => setForm({ ...form, postal_code: e.target.value })} required maxLength={20} />
            </label>
            <label>Country (2-char ISO) *
              <input
                className="input"
                value={form.country}
                onChange={(e) => setForm({ ...form, country: e.target.value.toUpperCase() })}
                required
                maxLength={2}
                minLength={2}
                style={{ textTransform: "uppercase" }}
              />
            </label>
            <label>Phone
              <input className="input" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} maxLength={30} />
            </label>
            <label className="flex" style={{ gap: 8, alignItems: "center" }}>
              <input type="checkbox" checked={form.is_default} onChange={(e) => setForm({ ...form, is_default: e.target.checked })} />
              Set as default
            </label>
          </div>
          <div className="flex" style={{ gap: 8, marginTop: 12 }}>
            <button className="btn" type="submit">{editingId ? "Save changes" : "Add address"}</button>
            <button className="btn secondary" type="button" onClick={cancelForm}>Cancel</button>
          </div>
        </form>
      )}
    </>
  );
}
