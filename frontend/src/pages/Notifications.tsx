import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { getToken, notificationsApi, type Notification } from "../api";

function relativeDate(iso: string): string {
  const d = new Date(iso);
  const diff = (Date.now() - d.getTime()) / 1000;
  if (diff < 60) return "just now";
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  if (diff < 604800) return `${Math.floor(diff / 86400)}d ago`;
  return d.toLocaleDateString();
}

export default function Notifications() {
  const [items, setItems] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);
  const wsRef = useRef<WebSocket | null>(null);

  const load = () => {
    setLoading(true);
    notificationsApi.list().then((d) => {
      setItems(d.items);
      setLoading(false);
    }).catch(() => setLoading(false));
  };

  useEffect(() => {
    load();
    const token = getToken();
    if (!token) return;
    const proto = window.location.protocol === "https:" ? "wss" : "ws";
    const ws = new WebSocket(`${proto}://${window.location.host}/ws/user?token=${token}`);
    wsRef.current = ws;
    ws.onmessage = (evt) => {
      try {
        const data = JSON.parse(evt.data);
        if (data.event === "notification") {
          const incoming: Notification = {
            id: data.id,
            type: data.type,
            title: data.title,
            body: data.body,
            link: data.link,
            is_read: !!data.is_read,
            created_at: data.created_at,
          };
          setItems((prev) => prev.some((n) => n.id === incoming.id) ? prev : [incoming, ...prev]);
        }
      } catch {}
    };
    const ping = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) ws.send("ping");
    }, 25000);
    return () => { clearInterval(ping); ws.close(); };
  }, []);

  const markOne = async (id: string) => {
    await notificationsApi.markRead(id);
    setItems((prev) => prev.map((n) => n.id === id ? { ...n, is_read: true } : n));
  };

  const markAll = async () => {
    await notificationsApi.markAllRead();
    setItems((prev) => prev.map((n) => ({ ...n, is_read: true })));
  };

  if (loading) return <div>Loading…</div>;

  return (
    <>
      <div className="flex" style={{ alignItems: "center" }}>
        <h1>Notifications</h1>
        <span style={{ flex: 1 }} />
        {items.some((n) => !n.is_read) && (
          <button className="btn secondary" onClick={markAll}>Mark all read</button>
        )}
      </div>
      {items.length === 0 ? (
        <div className="card" style={{ textAlign: "center", padding: 48 }}>
          <h3 style={{ marginBottom: 4 }}>You're all caught up</h3>
          <p className="muted">When something happens we'll show it here.</p>
        </div>
      ) : (
        <div className="stack">
          {items.map((n) => (
            <div key={n.id} className="card" style={{ borderLeft: n.is_read ? undefined : "3px solid var(--primary)" }}>
              <strong>{n.title}</strong>
              {n.body && <div className="muted">{n.body}</div>}
              <div className="muted" style={{ marginTop: 6 }}>{relativeDate(n.created_at)}</div>
              <div className="flex" style={{ marginTop: 12 }}>
                {n.link && <Link to={n.link} className="btn secondary">View</Link>}
                {!n.is_read && <button className="btn" onClick={() => markOne(n.id)}>Mark read</button>}
              </div>
            </div>
          ))}
        </div>
      )}
    </>
  );
}
