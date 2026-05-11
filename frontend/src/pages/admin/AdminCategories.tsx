import { useEffect, useMemo, useState } from "react";
import { categoriesApi, type Category } from "../../api";

type FormState = { name: string; slug: string; parent_id: string };

const emptyForm: FormState = { name: "", slug: "", parent_id: "" };

const slugify = (s: string) =>
  s.toLowerCase().trim().replace(/[^a-z0-9]+/g, "-").replace(/-+/g, "-").replace(/^-|-$/g, "");

type FlatCat = Category & { depth: number };

function flattenTree(nodes: any[], depth = 0, out: FlatCat[] = []): FlatCat[] {
  for (const n of nodes) {
    out.push({ id: n.id, name: n.name, slug: n.slug, parent_id: n.parent_id, depth });
    if (n.children && n.children.length) flattenTree(n.children, depth + 1, out);
  }
  return out;
}

export default function AdminCategories() {
  const [items, setItems] = useState<FlatCat[]>([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [form, setForm] = useState<FormState>(emptyForm);

  const load = async () => {
    setLoading(true);
    setErr("");
    try {
      const tree = await categoriesApi.list();
      setItems(flattenTree(tree as any));
    } catch (e: any) {
      setErr(e.response?.data?.detail || "Failed to load categories");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const parentOptions = useMemo(() => items.filter((c) => c.id !== editingId), [items, editingId]);

  const startAdd = () => {
    setEditingId(null);
    setForm(emptyForm);
    setShowForm(true);
  };

  const startEdit = (c: FlatCat) => {
    setEditingId(c.id);
    setForm({ name: c.name, slug: c.slug, parent_id: c.parent_id || "" });
    setShowForm(true);
  };

  const cancel = () => {
    setShowForm(false);
    setEditingId(null);
    setForm(emptyForm);
  };

  const onNameBlur = () => {
    if (!form.slug && form.name) {
      setForm({ ...form, slug: slugify(form.name) });
    }
  };

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErr("");
    const payload: Partial<Category> = {
      name: form.name,
      slug: form.slug || slugify(form.name),
      parent_id: form.parent_id || null,
    };
    try {
      if (editingId) {
        await categoriesApi.update(editingId, payload);
      } else {
        await categoriesApi.create(payload);
      }
      cancel();
      await load();
    } catch (e: any) {
      setErr(e.response?.data?.detail || "Failed to save category");
    }
  };

  const onDelete = async (id: string) => {
    if (!confirm("Delete this category?")) return;
    try {
      await categoriesApi.remove(id);
      await load();
    } catch (e: any) {
      setErr(e.response?.data?.detail || "Failed to delete");
    }
  };

  return (
    <>
      <h1>Admin · Categories</h1>
      {err && <p className="error">{err}</p>}

      <div style={{ marginBottom: 12 }}>
        {!showForm && <button className="btn" onClick={startAdd}>+ Add category</button>}
      </div>

      {showForm && (
        <form className="card" onSubmit={submit} style={{ marginBottom: 16 }}>
          <h2>{editingId ? "Edit category" : "Add category"}</h2>
          <div className="grid" style={{ gap: 8 }}>
            <label>Name *
              <input className="input" value={form.name} required maxLength={100}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                onBlur={onNameBlur} />
            </label>
            <label>Slug *
              <input className="input" value={form.slug} required maxLength={120}
                onChange={(e) => setForm({ ...form, slug: e.target.value })} />
            </label>
            <label>Parent
              <select className="input" value={form.parent_id}
                onChange={(e) => setForm({ ...form, parent_id: e.target.value })}>
                <option value="">— (root) —</option>
                {parentOptions.map((c) => (
                  <option key={c.id} value={c.id}>
                    {"  ".repeat(c.depth)}{c.name}
                  </option>
                ))}
              </select>
            </label>
          </div>
          <div className="flex" style={{ gap: 8, marginTop: 12 }}>
            <button className="btn" type="submit">{editingId ? "Save changes" : "Create"}</button>
            <button className="btn secondary" type="button" onClick={cancel}>Cancel</button>
          </div>
        </form>
      )}

      {loading ? (
        <p className="muted">Loading...</p>
      ) : items.length === 0 ? (
        <p className="muted">No categories yet.</p>
      ) : (
        <div className="card">
          {items.map((c) => (
            <div key={c.id} className="flex" style={{ justifyContent: "space-between", alignItems: "center", padding: "6px 0", borderBottom: "1px solid #eee" }}>
              <div style={{ paddingLeft: c.depth * 20 }}>
                <strong>{c.name}</strong> <span className="muted">/{c.slug}</span>
              </div>
              <div className="flex" style={{ gap: 8 }}>
                <button className="btn secondary" onClick={() => startEdit(c)}>Edit</button>
                <button className="btn secondary" onClick={() => onDelete(c.id)}>Delete</button>
              </div>
            </div>
          ))}
        </div>
      )}
    </>
  );
}
