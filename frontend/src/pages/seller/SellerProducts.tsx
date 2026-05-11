import { useEffect, useState } from "react";
import { api, imagesApi, sellerApi, type ProductImage } from "../../api";

type Category = { id: string; name: string };

const slugify = (s: string) =>
  s.toLowerCase().trim().replace(/[^a-z0-9]+/g, "-").replace(/-+/g, "-").replace(/^-|-$/g, "");

export default function SellerProducts() {
  const [items, setItems] = useState<any[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(true);
  const [imagesExpanded, setImagesExpanded] = useState<Record<string, boolean>>({});
  const [imagesByProduct, setImagesByProduct] = useState<Record<string, ProductImage[]>>({});
  const [imgForm, setImgForm] = useState<Record<string, { url: string; alt: string; position: string }>>({});

  const loadImages = async (productId: string) => {
    try {
      const list = await imagesApi.list(productId);
      setImagesByProduct((s) => ({ ...s, [productId]: list }));
    } catch {}
  };

  const toggleImages = (productId: string) => {
    setImagesExpanded((s) => {
      const next = { ...s, [productId]: !s[productId] };
      if (next[productId] && !imagesByProduct[productId]) loadImages(productId);
      return next;
    });
    if (!imgForm[productId]) {
      setImgForm((s) => ({ ...s, [productId]: { url: "", alt: "", position: "0" } }));
    }
  };

  const addImage = async (productId: string, e: React.FormEvent) => {
    e.preventDefault();
    const f = imgForm[productId];
    if (!f || !f.url) return;
    try {
      await imagesApi.add(productId, { url: f.url, alt: f.alt || null, position: parseInt(f.position || "0", 10) });
      setImgForm((s) => ({ ...s, [productId]: { url: "", alt: "", position: "0" } }));
      await loadImages(productId);
    } catch (e: any) {
      setErr(e.response?.data?.detail || "Failed to add image");
    }
  };

  const removeImage = async (productId: string, imageId: string) => {
    try {
      await imagesApi.remove(productId, imageId);
      await loadImages(productId);
    } catch (e: any) {
      setErr(e.response?.data?.detail || "Failed to remove image");
    }
  };

  const [form, setForm] = useState({
    name: "",
    description: "",
    price: "",
    category_id: "",
    image_url: "",
    initial_quantity: "0",
  });

  const load = async () => {
    setLoading(true);
    try {
      const data = await sellerApi.products(1, 100);
      setItems(data.items);
    } catch (e: any) {
      setErr(e.response?.data?.detail || "Failed to load");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    api.get("/categories").then((r) => setCategories(r.data)).catch(() => {});
  }, []);

  const reset = () => {
    setForm({ name: "", description: "", price: "", category_id: "", image_url: "", initial_quantity: "0" });
    setEditingId(null);
    setShowForm(false);
  };

  const startEdit = (p: any) => {
    setEditingId(p.id);
    setForm({
      name: p.name,
      description: p.description || "",
      price: String(p.price),
      category_id: p.category_id,
      image_url: p.image_url || "",
      initial_quantity: "0",
    });
    setShowForm(true);
  };

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErr("");
    try {
      if (editingId) {
        await sellerApi.updateProduct(editingId, {
          name: form.name,
          description: form.description || null,
          price: form.price,
          category_id: form.category_id,
          image_url: form.image_url || null,
        });
      } else {
        await sellerApi.createProduct({
          name: form.name,
          slug: slugify(form.name) + "-" + Math.random().toString(36).slice(2, 7),
          description: form.description || null,
          price: form.price,
          category_id: form.category_id,
          image_url: form.image_url || null,
          is_active: true,
          initial_quantity: parseInt(form.initial_quantity || "0", 10),
        });
      }
      reset();
      await load();
    } catch (e: any) {
      setErr(e.response?.data?.detail || "Failed to save product");
    }
  };

  const onDelete = async (id: string) => {
    if (!confirm("Delete this product?")) return;
    try {
      await sellerApi.deleteProduct(id);
      await load();
    } catch (e: any) {
      setErr(e.response?.data?.detail || "Failed to delete");
    }
  };

  return (
    <>
      <h1>My Products</h1>
      {err && <p className="error">{err}</p>}
      <div style={{ marginBottom: 12 }}>
        {!showForm && <button className="btn" onClick={() => setShowForm(true)}>Add Product</button>}
      </div>

      {showForm && (
        <form className="card" onSubmit={submit} style={{ marginBottom: 16 }}>
          <h2>{editingId ? "Edit product" : "Add product"}</h2>
          <div className="grid" style={{ gap: 8 }}>
            <label>Name *
              <input className="input" value={form.name} required maxLength={255}
                onChange={(e) => setForm({ ...form, name: e.target.value })} />
            </label>
            <label>Description
              <textarea className="input" value={form.description} rows={3}
                onChange={(e) => setForm({ ...form, description: e.target.value })} />
            </label>
            <label>Price *
              <input className="input" type="number" step="0.01" min="0.01" value={form.price} required
                onChange={(e) => setForm({ ...form, price: e.target.value })} />
            </label>
            <label>Category *
              <select className="input" value={form.category_id} required
                onChange={(e) => setForm({ ...form, category_id: e.target.value })}>
                <option value="">-- select --</option>
                {categories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
              </select>
            </label>
            <label>Image URL
              <input className="input" value={form.image_url}
                onChange={(e) => setForm({ ...form, image_url: e.target.value })} />
            </label>
            {!editingId && (
              <label>Initial quantity
                <input className="input" type="number" min="0" value={form.initial_quantity}
                  onChange={(e) => setForm({ ...form, initial_quantity: e.target.value })} />
              </label>
            )}
          </div>
          <div className="flex" style={{ gap: 8, marginTop: 12 }}>
            <button className="btn" type="submit">{editingId ? "Save" : "Create"}</button>
            <button className="btn secondary" type="button" onClick={reset}>Cancel</button>
          </div>
        </form>
      )}

      {loading ? (
        <p className="muted">Loading...</p>
      ) : items.length === 0 ? (
        <p className="muted">No products yet.</p>
      ) : (
        <div className="grid">
          {items.map((p) => (
            <div key={p.id} className="card">
              <strong>{p.name}{!p.is_active && <span className="muted"> (inactive)</span>}</strong>
              <div className="muted">{p.description?.slice(0, 80)}</div>
              <div className="price">${p.price}</div>
              <div className="flex" style={{ gap: 8, marginTop: 8 }}>
                <button className="btn secondary" onClick={() => startEdit(p)}>Edit</button>
                <button className="btn secondary" onClick={() => onDelete(p.id)}>Delete</button>
                <button className="btn secondary" onClick={() => toggleImages(p.id)}>
                  {imagesExpanded[p.id] ? "Hide images" : "Manage images"}
                </button>
              </div>
              {imagesExpanded[p.id] && (
                <div style={{ marginTop: 10, borderTop: "1px solid #eee", paddingTop: 10 }}>
                  <div className="flex" style={{ gap: 8, flexWrap: "wrap" }}>
                    {(imagesByProduct[p.id] || []).map((img) => (
                      <div key={img.id} style={{ position: "relative" }}>
                        <img src={img.url} alt={img.alt || ""} style={{ width: 80, height: 80, objectFit: "cover", border: "1px solid #ddd" }} />
                        <button
                          className="btn secondary"
                          onClick={() => removeImage(p.id, img.id)}
                          style={{ position: "absolute", top: 0, right: 0, padding: "0 6px" }}
                          title="Remove">×</button>
                      </div>
                    ))}
                    {(!imagesByProduct[p.id] || imagesByProduct[p.id].length === 0) && (
                      <span className="muted">No images yet.</span>
                    )}
                  </div>
                  <form onSubmit={(e) => addImage(p.id, e)} className="flex" style={{ gap: 8, marginTop: 10, flexWrap: "wrap" }}>
                    <input
                      className="input"
                      placeholder="Image URL"
                      value={imgForm[p.id]?.url || ""}
                      onChange={(e) => setImgForm((s) => ({ ...s, [p.id]: { ...(s[p.id] || { url: "", alt: "", position: "0" }), url: e.target.value } }))}
                      required
                      style={{ minWidth: 220 }}
                    />
                    <input
                      className="input"
                      placeholder="Alt"
                      value={imgForm[p.id]?.alt || ""}
                      onChange={(e) => setImgForm((s) => ({ ...s, [p.id]: { ...(s[p.id] || { url: "", alt: "", position: "0" }), alt: e.target.value } }))}
                      style={{ maxWidth: 160 }}
                    />
                    <input
                      className="input"
                      type="number"
                      placeholder="Pos"
                      value={imgForm[p.id]?.position || "0"}
                      onChange={(e) => setImgForm((s) => ({ ...s, [p.id]: { ...(s[p.id] || { url: "", alt: "", position: "0" }), position: e.target.value } }))}
                      style={{ maxWidth: 80 }}
                    />
                    <button className="btn" type="submit">Add</button>
                  </form>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </>
  );
}
