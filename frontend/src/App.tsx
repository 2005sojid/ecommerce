import { useEffect, useState } from "react";
import { Link, Route, Routes, useNavigate } from "react-router-dom";
import { clearTokens, notificationsApi } from "./api";
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

function BellLink() {
  const [count, setCount] = useState(0);
  useEffect(() => {
    let cancelled = false;
    const tick = () => {
      notificationsApi.unreadCount().then((c) => {
        if (!cancelled) setCount(c);
      }).catch(() => {});
    };
    tick();
    const id = setInterval(tick, 30000);
    return () => { cancelled = true; clearInterval(id); };
  }, []);
  return <Link to="/notifications">🔔{count > 0 && <span> ({count})</span>}</Link>;
}

export default function App() {
  const { user, setUser, loading } = useAuth();
  const nav = useNavigate();

  const logout = () => {
    clearTokens();
    setUser(null);
    nav("/");
  };

  return (
    <>
      <nav className="nav">
        <Link to="/"><strong>Shop</strong></Link>
        <Link to="/products">Products</Link>
        <Link to="/flash-sales">Flash Sales</Link>
        {user && <Link to="/orders">My Orders</Link>}
        {user && <Link to="/wishlist">Wishlist</Link>}
        {user && <Link to="/addresses">Addresses</Link>}
        {user && <Link to="/returns">Returns</Link>}
        {user && <Link to="/chat">Messages</Link>}
        {user && <BellLink />}
        <Link to="/cart">Cart</Link>
        {user?.role === "seller" && <Link to="/seller/dashboard">Seller</Link>}
        {user?.role === "customer" && <Link to="/sell">Sell</Link>}
        {user?.role === "admin" && <Link to="/admin/dashboard">Admin</Link>}
        <span className="spacer" />
        {loading ? null : user ? (
          <>
            <span className="muted">Hi, {user.name}</span>
            <button className="btn secondary" onClick={logout}>Logout</button>
          </>
        ) : (
          <>
            <Link to="/login">Login</Link>
            <Link to="/register">Register</Link>
          </>
        )}
      </nav>

      <div className="container">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/products" element={<Products />} />
          <Route path="/products/:id" element={<ProductDetail />} />
          <Route path="/cart" element={<Cart />} />
          <Route path="/checkout" element={<Checkout />} />
          <Route path="/orders" element={<Orders />} />
          <Route path="/orders/:id" element={<OrderDetail />} />
          <Route path="/flash-sales" element={<FlashSales />} />
          <Route path="/login" element={<Login onLogin={setUser} />} />
          <Route path="/register" element={<Register onRegister={setUser} />} />
          <Route path="/admin/dashboard" element={<AdminDashboard />} />
          <Route path="/wishlist" element={<Wishlist />} />
          <Route path="/addresses" element={<Addresses />} />
          <Route path="/notifications" element={<Notifications />} />
          <Route path="/sell" element={<SellerRegister />} />
          <Route path="/seller/dashboard" element={<SellerDashboard />} />
          <Route path="/seller/products" element={<SellerProducts />} />
          <Route path="/seller/orders" element={<SellerOrders />} />
          <Route path="/seller/settings" element={<SellerSettings />} />
          <Route path="/store/:slug" element={<SellerStore />} />
          <Route path="/admin/coupons" element={<AdminCoupons />} />
          <Route path="/returns" element={<Returns />} />
          <Route path="/admin/returns" element={<AdminReturns />} />
          <Route path="/admin/reviews" element={<AdminReviewsModerate />} />
          <Route path="/admin/categories" element={<AdminCategories />} />
          <Route path="/chat" element={<Chat />} />
        </Routes>
      </div>
    </>
  );
}
