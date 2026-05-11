import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { sellerApi, type Seller } from "../../api";

export default function SellerDashboard() {
  const [seller, setSeller] = useState<Seller | null>(null);
  const [analytics, setAnalytics] = useState<any>(null);
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([sellerApi.me(), sellerApi.analytics()])
      .then(([s, a]) => { setSeller(s); setAnalytics(a); })
      .catch((e) => setErr(e.response?.data?.detail || "Failed to load dashboard"))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p className="muted">Loading...</p>;
  if (err) return <p className="error">{err}</p>;
  if (!seller) return null;

  return (
    <>
      <h1>Seller Dashboard</h1>
      <div className="card">
        <div className="flex" style={{ justifyContent: "space-between", alignItems: "center" }}>
          <div>
            <strong>{seller.store_name}</strong>
            <div className="muted">/{seller.slug}{seller.is_verified ? " - Verified" : ""}</div>
          </div>
          <Link to={`/store/${seller.slug}`} className="btn secondary">View store</Link>
        </div>
      </div>

      <div className="grid" style={{ marginTop: 16, gridTemplateColumns: "repeat(3, 1fr)", gap: 12 }}>
        <div className="card">
          <div className="muted">Revenue</div>
          <div className="price">${analytics?.revenue_total?.toFixed(2) ?? "0.00"}</div>
        </div>
        <div className="card">
          <div className="muted">Orders</div>
          <div className="price">{analytics?.orders_count ?? 0}</div>
        </div>
        <div className="card">
          <div className="muted">Products</div>
          <div className="price">{analytics?.products_count ?? 0}</div>
        </div>
      </div>

      {analytics?.top_products?.length > 0 && (
        <div className="card" style={{ marginTop: 16 }}>
          <h2>Top Products</h2>
          <table style={{ width: "100%" }}>
            <thead>
              <tr><th align="left">Product</th><th align="right">Units</th><th align="right">Revenue</th></tr>
            </thead>
            <tbody>
              {analytics.top_products.map((p: any) => (
                <tr key={p.product_id}>
                  <td>{p.name}</td>
                  <td align="right">{p.units_sold}</td>
                  <td align="right">${p.revenue.toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="flex" style={{ gap: 8, marginTop: 16 }}>
        <Link to="/seller/products" className="btn">Manage Products</Link>
        <Link to="/seller/orders" className="btn secondary">Orders</Link>
        <Link to="/seller/settings" className="btn secondary">Edit Profile</Link>
      </div>
    </>
  );
}
