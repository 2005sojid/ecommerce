import { useEffect, useState } from "react";
import { couponsApi, type Coupon } from "../../api";

type FormState = {
  code: string;
  discount_type: "percent" | "fixed";
  discount_value: string;
  scope: "platform" | "seller";
  min_order_amount: string;
  max_uses: string;
  valid_from: string;
  valid_to: string;
  is_active: boolean;
};

const emptyForm: FormState = {
  code: "",
  discount_type: "percent",
  discount_value: "",
  scope: "platform",
  min_order_amount: "",
  max_uses: "",
  valid_from: "",
  valid_to: "",
  is_active: true,
};

export default function AdminCoupons() {
  const [items, setItems] = useState<Coupon[]>([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [form, setForm] = useState<FormState>(emptyForm);

  const load = async () => {
    setLoading(true);
    try {
      const data = await couponsApi.list(1, 50);
      setItems(data.items || []);
    } catch (e: any) {
      setErr(e.response?.data?.detail || "Failed to load coupons");
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

  const startEdit = (c: Coupon) => {
    setEditingId(c.id);
    setForm({
      code: c.code,
      discount_type: c.discount_type,
      discount_value: String(c.discount_value),
      scope: c.scope,
      min_order_amount: c.min_order_amount != null ? String(c.min_order_amount) : "",
      max_uses: c.max_uses != null ? String(c.max_uses) : "",
      valid_from: c.valid_from ? c.valid_from.slice(0, 16) : "",
      valid_to: c.valid_to ? c.valid_to.slice(0, 16) : "",
      is_active: c.is_active,
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
    const payload: any = {
      code: form.code.trim(),
      discount_type: form.discount_type,
      discount_value: Number(form.discount_value),
      scope: form.scope,
      min_order_amount: form.min_order_amount ? Number(form.min_order_amount) : null,
      max_uses: form.max_uses ? Number(form.max_uses) : null,
      valid_from: form.valid_from ? new Date(form.valid_from).toISOString() : null,
      valid_to: form.valid_to ? new Date(form.valid_to).toISOString() : null,
      is_active: form.is_active,
    };
    try {
      if (editingId) {
        await couponsApi.update(editingId, payload);
      } else {
        await couponsApi.create(payload);
      }
      cancelForm();
      await load();
    } catch (e: any) {
      setErr(e.response?.data?.detail || "Failed to save coupon");
    }
  };

  const onDelete = async (id: string) => {
    if (!confirm("Delete this coupon?")) return;
    try {
      await couponsApi.remove(id);
      await load();
    } catch (e: any) {
      setErr(e.response?.data?.detail || "Failed to delete");
    }
  };

  return (
    <>
      <h1>Coupons</h1>
      {err && <p className="error">{err}</p>}

      <div style={{ marginBottom: 16 }}>
        {!showForm && <button className="btn" onClick={startAdd}>+ Add coupon</button>}
      </div>

      {loading ? (
        <p className="muted">Loading...</p>
      ) : items.length === 0 ? (
        <p className="muted">No coupons yet.</p>
      ) : (
        <table className="card">
          <thead>
            <tr>
              <th>Code</th>
              <th>Discount</th>
              <th>Scope</th>
              <th>Uses</th>
              <th>Active</th>
              <th>Valid to</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {items.map((c) => (
              <tr key={c.id}>
                <td><strong>{c.code}</strong></td>
                <td>
                  {c.discount_type === "percent" ? `${c.discount_value}%` : `$${c.discount_value}`}
                </td>
                <td>{c.scope}</td>
                <td>{c.used_count}{c.max_uses != null ? ` / ${c.max_uses}` : ""}</td>
                <td>{c.is_active ? "Yes" : "No"}</td>
                <td>{c.valid_to ? new Date(c.valid_to).toLocaleDateString() : "—"}</td>
                <td>
                  <div className="flex" style={{ gap: 8 }}>
                    <button className="btn secondary" onClick={() => startEdit(c)}>Edit</button>
                    <button className="btn secondary" onClick={() => onDelete(c.id)}>Delete</button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {showForm && (
        <form className="card" onSubmit={submit} style={{ marginTop: 16 }}>
          <h2>{editingId ? "Edit coupon" : "Add coupon"}</h2>
          <div className="grid" style={{ gap: 8 }}>
            <label>Code *
              <input className="input" value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value })} required maxLength={50} />
            </label>
            <label>Discount type *
              <select className="input" value={form.discount_type} onChange={(e) => setForm({ ...form, discount_type: e.target.value as "percent" | "fixed" })}>
                <option value="percent">Percent (%)</option>
                <option value="fixed">Fixed ($)</option>
              </select>
            </label>
            <label>Discount value *
              <input className="input" type="number" step="0.01" min="0" value={form.discount_value} onChange={(e) => setForm({ ...form, discount_value: e.target.value })} required />
            </label>
            <label>Scope *
              <select className="input" value={form.scope} onChange={(e) => setForm({ ...form, scope: e.target.value as "platform" | "seller" })}>
                <option value="platform">Platform</option>
                <option value="seller">Seller</option>
              </select>
            </label>
            <label>Minimum order amount
              <input className="input" type="number" step="0.01" min="0" value={form.min_order_amount} onChange={(e) => setForm({ ...form, min_order_amount: e.target.value })} />
            </label>
            <label>Max uses (blank = unlimited)
              <input className="input" type="number" min="1" value={form.max_uses} onChange={(e) => setForm({ ...form, max_uses: e.target.value })} />
            </label>
            <label>Valid from
              <input className="input" type="datetime-local" value={form.valid_from} onChange={(e) => setForm({ ...form, valid_from: e.target.value })} />
            </label>
            <label>Valid to
              <input className="input" type="datetime-local" value={form.valid_to} onChange={(e) => setForm({ ...form, valid_to: e.target.value })} />
            </label>
            <label className="flex" style={{ gap: 8, alignItems: "center" }}>
              <input type="checkbox" checked={form.is_active} onChange={(e) => setForm({ ...form, is_active: e.target.checked })} />
              Active
            </label>
          </div>
          <div className="flex" style={{ gap: 8, marginTop: 12 }}>
            <button className="btn" type="submit">{editingId ? "Save changes" : "Create coupon"}</button>
            <button className="btn secondary" type="button" onClick={cancelForm}>Cancel</button>
          </div>
        </form>
      )}
    </>
  );
}
