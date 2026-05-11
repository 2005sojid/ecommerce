import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { notificationsApi, type Notification } from "../api";

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

  const load = () => {
    setLoading(true);
    notificationsApi.list().then((d) => {
      setItems(d.items);
      setLoading(false);
    }).catch(() => setLoading(false));
  };

  useEffect(load, []);

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
        <span className="spacer" />
        {items.some((n) => !n.is_read) && (
          <button className="btn secondary" onClick={markAll}>Mark all read</button>
        )}
      </div>
      {items.length === 0 ? (
        <p className="muted">No notifications yet.</p>
      ) : (
        <div className="grid">
          {items.map((n) => (
            <div key={n.id} className="card">
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
