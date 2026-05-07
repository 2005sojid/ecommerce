import { Link, Route, Routes, useNavigate } from "react-router-dom";
import { clearTokens } from "./api";
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
        <Link to="/cart">Cart</Link>
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
        </Routes>
      </div>
    </>
  );
}
