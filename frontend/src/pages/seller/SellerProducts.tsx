import { useEffect, useRef, useState } from "react";
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
  const [uploadProgress, setUploadProgress] = useState<Record<string, number>>({});
  const [uploadErr, setUploadErr] = useState<Record<string, string>>({});
  const [primaryUploadPct, setPrimaryUploadPct] = useState(0);
  const fileInputRefs = useRef<Record<string, HTMLInputElement | null>>({});

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
  };

  const uploadFiles = async (productId: string, files: FileList | null) => {
    if (!files || files.length === 0) return;
    setUploadErr((s) => ({ ...s, [productId]: "" }));
    const list = Array.from(files);
    for (const file of list) {
      try {
        setUploadProgress((s) => ({ ...s, [productId]: 0 }));
        await imagesApi.upload(productId, file, {
          alt: file.name,
          onProgress: (pct) => setUploadProgress((s) => ({ ...s, [productId]: pct })),
        });
      } catch (e: any) {
        setUploadErr((s) => ({ ...s, [productId]: e.response?.data?.detail || `Failed to upload ${file.name}` }));
      }
    }
    setUploadProgress((s) => ({ ...s, [productId]: 0 }));
    await loadImages(productId);
  };

  const onDropFiles = (productId: string, e: React.DragEvent) => {
    e.preventDefault();
    uploadFiles(productId, e.dataTransfer.files);
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
            <label>Primary image
              {editingId ? (
                <>
                  {form.image_url && (
                    <img
                      src={form.image_url}
                      alt=""
                      onError={(e) => { (e.target as HTMLImageElement).style.opacity = "0.25"; }}
                      style={{ marginTop: 8, width: 200, height: 150, objectFit: "cover", borderRadius: 6, border: "1px solid var(--border)" }}
                    />
                  )}
                  <label className="dropzone" style={{ marginTop: 8, display: "block" }}>
                    <input
                      type="file"
                      accept="image/jpeg,image/png,image/webp,image/gif"
                      onChange={async (e) => {
                        const file = e.target.files?.[0];
                        if (!file || !editingId) return;
                        try {
                          setPrimaryUploadPct(0);
                          const img = await imagesApi.upload(editingId, file, {
                            alt: file.name,
                            onProgress: setPrimaryUploadPct,
                          });
                          await sellerApi.updateProduct(editingId, { image_url: img.url });
                          setForm((s) => ({ ...s, image_url: img.url }));
                          setPrimaryUploadPct(0);
                        } catch (er: any) {
                          setErr(er.response?.data?.detail || "Upload failed");
                          setPrimaryUploadPct(0);
                        }
                      }}
                    />
                    {primaryUploadPct > 0 ? `Uploading… ${primaryUploadPct}%` : "Click to upload primary image"}
                  </label>
                  {primaryUploadPct > 0 && (
                    <div className="upload-progress"><div className="upload-progress-bar" style={{ width: `${primaryUploadPct}%` }} /></div>
                  )}
                </>
              ) : (
                <div className="muted" style={{ fontSize: 12, marginTop: 4 }}>
                  Save the product first, then upload images from the "Manage images" panel below.
                </div>
              )}
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
        <div className="stack">
          {items.map((p) => (
            <div key={p.id} className="card">
              <div className="seller-row">
                {p.image_url ? (
                  <img
                    src={p.image_url}
                    alt={p.name}
                    onError={(e) => { (e.target as HTMLImageElement).style.opacity = "0.2"; }}
                    className="seller-row-thumb"
                  />
                ) : (
                  <div className="seller-row-thumb placeholder">📦</div>
                )}
                <div className="seller-row-body">
                  <strong>{p.name}{!p.is_active && <span className="muted"> (inactive)</span>}</strong>
                  <div className="muted">{p.description?.slice(0, 120)}</div>
                  <div className="price">${p.price}</div>
                </div>
                <div className="seller-row-actions">
                  <button className="btn secondary" onClick={() => startEdit(p)}>Edit</button>
                  <button className="btn secondary" onClick={() => onDelete(p.id)}>Delete</button>
                  <button className="btn secondary" onClick={() => toggleImages(p.id)}>
                    {imagesExpanded[p.id] ? "Hide images" : "Manage images"}
                  </button>
                </div>
              </div>
              {imagesExpanded[p.id] && (
                <div style={{ marginTop: 10, borderTop: "1px solid var(--border)", paddingTop: 10 }}>
                  <div className="flex" style={{ gap: 8, flexWrap: "wrap" }}>
                    {(imagesByProduct[p.id] || []).map((img) => (
                      <div key={img.id} style={{ position: "relative" }}>
                        <img src={img.url} alt={img.alt || ""} style={{ width: 88, height: 88, objectFit: "cover", border: "1px solid var(--border)", borderRadius: 6 }} />
                        <div className="flex" style={{ gap: 4, position: "absolute", top: 4, right: 4 }}>
                          <button
                            className="btn secondary"
                            title="Set as primary"
                            onClick={async () => {
                              try {
                                await sellerApi.updateProduct(p.id, { image_url: img.url });
                                await load();
                              } catch (er: any) { setErr(er.response?.data?.detail || "Failed"); }
                            }}
                            style={{ padding: "0 6px", fontSize: 11 }}
                          >★</button>
                          <button
                            className="btn danger"
                            onClick={() => removeImage(p.id, img.id)}
                            style={{ padding: "0 6px" }}
                            title="Remove">×</button>
                        </div>
                      </div>
                    ))}
                    {(!imagesByProduct[p.id] || imagesByProduct[p.id].length === 0) && (
                      <span className="muted">No images yet — upload below.</span>
                    )}
                  </div>
                  <label
                    className="dropzone"
                    style={{ marginTop: 12, display: "block" }}
                    onDragOver={(e) => { e.preventDefault(); (e.currentTarget as HTMLElement).classList.add("active"); }}
                    onDragLeave={(e) => (e.currentTarget as HTMLElement).classList.remove("active")}
                    onDrop={(e) => { (e.currentTarget as HTMLElement).classList.remove("active"); onDropFiles(p.id, e); }}
                  >
                    <input
                      ref={(el) => { fileInputRefs.current[p.id] = el; }}
                      type="file"
                      accept="image/jpeg,image/png,image/webp,image/gif"
                      multiple
                      onChange={(e) => { uploadFiles(p.id, e.target.files); e.target.value = ""; }}
                    />
                    {uploadProgress[p.id] && uploadProgress[p.id] > 0
                      ? `Uploading… ${uploadProgress[p.id]}%`
                      : "Drag images here, or click to select (JPEG/PNG/WebP/GIF, max 5 MB)"}
                  </label>
                  {uploadProgress[p.id] && uploadProgress[p.id] > 0 && (
                    <div className="upload-progress"><div className="upload-progress-bar" style={{ width: `${uploadProgress[p.id]}%` }} /></div>
                  )}
                  {uploadErr[p.id] && <p className="error">{uploadErr[p.id]}</p>}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </>
  );
}
