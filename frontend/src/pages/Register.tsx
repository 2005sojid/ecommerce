import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, saveTokens, User } from "../api";

export default function Register({ onRegister }: { onRegister: (u: User) => void }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [err, setErr] = useState("");
  const nav = useNavigate();

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErr("");
    try {
      const { data } = await api.post("/auth/register", { email, password, name });
      saveTokens(data.tokens.access_token, data.tokens.refresh_token);
      onRegister(data.user);
      nav("/");
    } catch (e: any) {
      setErr(e.response?.data?.detail || "Registration failed");
    }
  };

  return (
    <form className="card" onSubmit={submit} style={{ maxWidth: 380 }}>
      <h1>Register</h1>
      <label>Name</label>
      <input className="input" value={name} onChange={(e) => setName(e.target.value)} required />
      <label>Email</label>
      <input className="input" value={email} onChange={(e) => setEmail(e.target.value)} required />
      <label>Password</label>
      <input className="input" type="password" minLength={8} value={password}
             onChange={(e) => setPassword(e.target.value)} required />
      {err && <p className="error">{err}</p>}
      <button className="btn" type="submit" style={{ marginTop: 12 }}>Create account</button>
    </form>
  );
}
