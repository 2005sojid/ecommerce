import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, saveTokens, User } from "../api";

export default function Register({ onRegister }: { onRegister: (u: User) => void }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [name, setName] = useState("");
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const nav = useNavigate();

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (busy) return;
    setErr("");
    if (password !== confirm) { setErr("Passwords do not match"); return; }
    if (password.length < 8) { setErr("Password must be at least 8 characters"); return; }
    setBusy(true);
    try {
      const { data } = await api.post("/auth/register", { email, password, name });
      saveTokens(data.tokens.access_token, data.tokens.refresh_token);
      onRegister(data.user);
      nav("/");
    } catch (e: any) {
      setErr(e.response?.data?.detail || "Registration failed");
      setBusy(false);
    }
  };

  return (
    <form className="card" onSubmit={submit} style={{ maxWidth: 380 }}>
      <h1>Register</h1>
      <label>Name</label>
      <input className="input" value={name} onChange={(e) => setName(e.target.value)} required />
      <label>Email</label>
      <input className="input" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
      <label>Password</label>
      <input className="input" type="password" minLength={8} value={password}
             onChange={(e) => setPassword(e.target.value)} required />
      <label>Confirm password</label>
      <input className="input" type="password" minLength={8} value={confirm}
             onChange={(e) => setConfirm(e.target.value)} required />
      {err && <p className="error">{err}</p>}
      <button className="btn" type="submit" disabled={busy} style={{ marginTop: 12, opacity: busy ? 0.6 : 1 }}>
        {busy ? "Creating account…" : "Create account"}
      </button>
    </form>
  );
}
