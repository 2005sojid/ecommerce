import { useEffect, useState } from "react";
import { Link, Navigate, Route, Routes, useLocation, useNavigate } from "react-router-dom";
import { api, clearTokens, getToken, notificationsApi } from "./api";
import { useAuth } from "./useAuth";
import Home from "./pages/Home";
import Products from "./pages/Products";
import ProductDetail from "./pages/ProductDetail";
import Cart from "./pages/Cart";
import Checkout from "./pages/Checkout";
import Orders from "./pages/Orders";
import OrderDetail from "./pages/OrderDetail";
import FlashSales from "./pages/FlashSales";
import Login from "./pages/Login";
import Register from "./pages/Register";
import AdminDashboard from "./pages/AdminDashboard";
import Wishlist from "./pages/Wishlist";
import Addresses from "./pages/Addresses";
import Notifications from "./pages/Notifications";
import SellerRegister from "./pages/seller/SellerRegister";
import SellerDashboard from "./pages/seller/SellerDashboard";
import SellerProducts from "./pages/seller/SellerProducts";
import SellerOrders from "./pages/seller/SellerOrders";
import SellerSettings from "./pages/seller/SellerSettings";
import SellerStore from "./pages/SellerStore";
import AdminCoupons from "./pages/admin/AdminCoupons";
import Returns from "./pages/Returns";
import AdminReturns from "./pages/admin/AdminReturns";
import AdminReviewsModerate from "./pages/admin/AdminReviewsModerate";
import AdminCategories from "./pages/admin/AdminCategories";
import Chat from "./pages/Chat";

type Role = "customer" | "admin" | "seller";

function RoleGuard({ user, allow, children }: { user: { role: Role } | null; allow: Role[]; children: JSX.Element }) {
  if (!user) return <Navigate to="/login" replace />;
  if (!allow.includes(user.role)) return <Navigate to="/" replace />;
  return children;
}

function initials(name: string): string {
  return name.split(" ").map((s) => s[0]).filter(Boolean).slice(0, 2).join("").toUpperCase();
}

export default function App() {
  const { user, setUser, loading } = useAuth();
  const nav = useNavigate();
  const location = useLocation();
  const [searchVal, setSearchVal] = useState("");

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    setSearchVal(params.get("search") || "");
  }, [location.search]);
  const [notifCount, setNotifCount] = useState(0);
  const [cartCount, setCartCount] = useState(0);
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    if (!user) { setNotifCount(0); setCartCount(0); return; }
    if (user.role !== "customer" && user.role !== "seller") return;

    const refresh = () => notificationsApi.unreadCount().then(setNotifCount).catch(() => {});
    refresh();

    const token = getToken();
    if (!token) return;
    const proto = window.location.protocol === "https:" ? "wss" : "ws";
    const ws = new WebSocket(`${proto}://${window.location.host}/ws/user?token=${token}`);
    ws.onmessage = (evt) => {
      try {
        const data = JSON.parse(evt.data);
        if (data.event === "notification") refresh();
      } catch {}
    };
    ws.onerror = () => {};
    const ping = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) ws.send("ping");
    }, 25000);
    const fallback = setInterval(refresh, 60000);
    return () => { clearInterval(ping); clearInterval(fallback); ws.close(); };
  }, [user]);

  useEffect(() => {
    if (user?.role === "customer" || user?.role === "seller") {
      notificationsApi.unreadCount().then(setNotifCount).catch(() => {});
    }
  }, [location.pathname]);

  useEffect(() => {
    if (user?.role !== "customer") { setCartCount(0); return; }
    api.get("/cart").then((r) => {
      const total = r.data?.items?.reduce((a: number, i: any) => a + (i.quantity || 0), 0) || 0;
      setCartCount(total);
    }).catch(() => {});
  }, [user, location.pathname]);

  const logout = () => {
    clearTokens();
    setUser(null);
    setMenuOpen(false);
    nav("/");
  };

  const onSearch = (e: React.FormEvent) => {
    e.preventDefault();
    nav(searchVal ? `/products?search=${encodeURIComponent(searchVal)}` : "/products");
  };

  const isCustomer = user?.role === "customer";
  const isSeller = user?.role === "seller";
  const isAdmin = user?.role === "admin";

  return (
    <>
      <header className="topbar">
        <div className="topbar-inner">
          <Link to="/" className="brand">
            <span className="brand-icon" aria-hidden>🛍</span>
            <span className="brand-name">ShopSphere</span>
          </Link>

          <form className="searchbar" onSubmit={onSearch}>
            <button type="submit" className="searchbar-btn" aria-label="Search">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="11" cy="11" r="7" />
                <path d="m20 20-3.5-3.5" />
              </svg>
            </button>
            <input
              type="text"
              placeholder="Search products, brands, sellers…"
              value={searchVal}
              onChange={(e) => setSearchVal(e.target.value)}
            />
          </form>

          <div className="topbar-actions">
            {isCustomer && (
              <Link to="/wishlist" className="topbar-link">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>
                <span>Wishlist</span>
              </Link>
            )}
            {(!user || isCustomer) && (
              <Link to="/cart" className="topbar-link badge-wrap">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="9" cy="21" r="1.6"/><circle cx="18" cy="21" r="1.6"/><path d="M2 3h2l3 14h13l3-10H6"/></svg>
                <span>Cart</span>
                {cartCount > 0 && <em className="count-badge">{cartCount}</em>}
              </Link>
            )}
            {(isCustomer || isSeller) && (
              <Link to="/notifications" className="topbar-link badge-wrap icon-only" aria-label="Notifications">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10.3 21a2 2 0 0 0 3.4 0"/></svg>
                {notifCount > 0 && <em className="count-badge">{notifCount}</em>}
              </Link>
            )}
            {loading ? null : user ? (
              <div className="user-menu">
                <button className="avatar" onClick={() => setMenuOpen((o) => !o)} aria-label="Account menu">
                  {initials(user.name)}
                </button>
                {menuOpen && (
                  <div className="user-dropdown" onMouseLeave={() => setMenuOpen(false)}>
                    <div className="user-dropdown-header">
                      <strong>{user.name}</strong>
                      <span className="muted">{user.role}</span>
                    </div>
                    {isCustomer && <Link to="/orders" onClick={() => setMenuOpen(false)}>My Orders</Link>}
                    {isCustomer && <Link to="/addresses" onClick={() => setMenuOpen(false)}>Addresses</Link>}
                    {isCustomer && <Link to="/returns" onClick={() => setMenuOpen(false)}>Returns</Link>}
                    {(isCustomer || isSeller) && <Link to="/chat" onClick={() => setMenuOpen(false)}>Messages</Link>}
                    {isCustomer && <Link to="/sell" onClick={() => setMenuOpen(false)}>Become a seller</Link>}
                    {isSeller && <Link to="/seller/dashboard" onClick={() => setMenuOpen(false)}>Seller dashboard</Link>}
                    {isAdmin && <Link to="/admin/dashboard" onClick={() => setMenuOpen(false)}>Admin dashboard</Link>}
                    <button className="dropdown-logout" onClick={logout}>Logout</button>
                  </div>
                )}
              </div>
            ) : (
              <>
                <Link to="/login" className="topbar-link">Login</Link>
                <Link to="/register" className="btn" style={{ padding: "7px 14px" }}>Register</Link>
              </>
            )}
          </div>
        </div>
      </header>

      <div className="container">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/products" element={<Products />} />
          <Route path="/products/:id" element={<ProductDetail />} />
          <Route path="/cart" element={loading ? null : <RoleGuard user={user} allow={["customer"]}><Cart /></RoleGuard>} />
          <Route path="/checkout" element={loading ? null : <RoleGuard user={user} allow={["customer"]}><Checkout /></RoleGuard>} />
          <Route path="/orders" element={loading ? null : <RoleGuard user={user} allow={["customer"]}><Orders /></RoleGuard>} />
          <Route path="/orders/:id" element={loading ? null : <RoleGuard user={user} allow={["customer", "admin"]}><OrderDetail /></RoleGuard>} />
          <Route path="/flash-sales" element={<FlashSales />} />
          <Route path="/login" element={<Login onLogin={setUser} />} />
          <Route path="/register" element={<Register onRegister={setUser} />} />
          <Route path="/admin/dashboard" element={loading ? null : <RoleGuard user={user} allow={["admin"]}><AdminDashboard /></RoleGuard>} />
          <Route path="/wishlist" element={loading ? null : <RoleGuard user={user} allow={["customer"]}><Wishlist /></RoleGuard>} />
          <Route path="/addresses" element={loading ? null : <RoleGuard user={user} allow={["customer"]}><Addresses /></RoleGuard>} />
          <Route path="/notifications" element={loading ? null : <RoleGuard user={user} allow={["customer", "seller"]}><Notifications /></RoleGuard>} />
          <Route path="/sell" element={loading ? null : <RoleGuard user={user} allow={["customer"]}><SellerRegister /></RoleGuard>} />
          <Route path="/seller/dashboard" element={loading ? null : <RoleGuard user={user} allow={["seller"]}><SellerDashboard /></RoleGuard>} />
          <Route path="/seller/products" element={loading ? null : <RoleGuard user={user} allow={["seller"]}><SellerProducts /></RoleGuard>} />
          <Route path="/seller/orders" element={loading ? null : <RoleGuard user={user} allow={["seller"]}><SellerOrders /></RoleGuard>} />
          <Route path="/seller/settings" element={loading ? null : <RoleGuard user={user} allow={["seller"]}><SellerSettings /></RoleGuard>} />
          <Route path="/store/:slug" element={<SellerStore />} />
          <Route path="/admin/coupons" element={loading ? null : <RoleGuard user={user} allow={["admin"]}><AdminCoupons /></RoleGuard>} />
          <Route path="/returns" element={loading ? null : <RoleGuard user={user} allow={["customer"]}><Returns /></RoleGuard>} />
          <Route path="/admin/returns" element={loading ? null : <RoleGuard user={user} allow={["admin"]}><AdminReturns /></RoleGuard>} />
          <Route path="/admin/reviews" element={loading ? null : <RoleGuard user={user} allow={["admin"]}><AdminReviewsModerate /></RoleGuard>} />
          <Route path="/admin/categories" element={loading ? null : <RoleGuard user={user} allow={["admin"]}><AdminCategories /></RoleGuard>} />
          <Route path="/chat" element={loading ? null : <RoleGuard user={user} allow={["customer", "seller"]}><Chat /></RoleGuard>} />
        </Routes>
      </div>
    </>
  );
}
