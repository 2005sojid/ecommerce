import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, saveTokens, User } from "../api";

export default function Login({ onLogin }: { onLogin: (u: User) => void }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState("");
  const nav = useNavigate();

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErr("");
    try {
      const { data } = await api.post("/auth/login", { email, password });
      saveTokens(data.access_token, data.refresh_token);
      const me = await api.get<User>("/auth/me");
      onLogin(me.data);
      nav("/");
    } catch (e: any) {
      setErr(e.response?.data?.detail || "Login failed");
    }
  };

  return (
    <form className="card" onSubmit={submit} style={{ maxWidth: 380 }}>
      <h1>Login</h1>
      <label>Email</label>
      <input className="input" value={email} onChange={(e) => setEmail(e.target.value)} required />
      <label>Password</label>
      <input className="input" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
      {err && <p className="error">{err}</p>}
      <button className="btn" type="submit" style={{ marginTop: 12 }}>Sign in</button>
      <p className="muted">Try: customer1@example.com / password123</p>
    </form>
  );
}
