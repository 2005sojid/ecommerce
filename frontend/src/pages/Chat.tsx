import { useEffect, useRef, useState } from "react";
import { api, chatApi, Conversation, Message } from "../api";

export default function Chat() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [body, setBody] = useState("");
  const [sending, setSending] = useState(false);
  const [currentUserId, setCurrentUserId] = useState<string | null>(null);
  const pollRef = useRef<number | null>(null);

  const loadConversations = () => {
    chatApi.conversations().then(setConversations).catch(() => {});
  };

  const loadMessages = (id: string) => {
    chatApi.messages(id).then((d: { items: Message[]; total: number }) => {
      setMessages([...d.items].reverse());
    }).catch(() => {});
  };

  useEffect(() => {
    loadConversations();
    api.get<{ id: string }>("/auth/me").then((r) => setCurrentUserId(r.data.id)).catch(() => {});
  }, []);

  useEffect(() => {
    if (!activeId) return;
    loadMessages(activeId);
    pollRef.current = window.setInterval(() => {
      loadMessages(activeId);
      loadConversations();
    }, 5000);
    return () => {
      if (pollRef.current !== null) {
        window.clearInterval(pollRef.current);
        pollRef.current = null;
      }
    };
  }, [activeId]);

  const send = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeId || !body.trim() || sending) return;
    setSending(true);
    try {
      await chatApi.send(activeId, body.trim());
      setBody("");
      loadMessages(activeId);
      loadConversations();
    } finally {
      setSending(false);
    }
  };

  return (
    <>
      <h1>Messages</h1>
      <div style={{ display: "flex", gap: 16 }}>
        <div style={{ flex: 1 }} className="card">
          <h3>Conversations</h3>
          {conversations.length === 0 ? (
            <p className="muted">No conversations yet.</p>
          ) : (
            <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
              {conversations.map((c) => (
                <li
                  key={c.id}
                  onClick={() => setActiveId(c.id)}
                  style={{
                    padding: 12,
                    borderBottom: "1px solid var(--border)",
                    cursor: "pointer",
                    borderRadius: 8,
                    background: c.id === activeId ? "var(--bg-elev-2)" : "transparent",
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between" }}>
                    <strong>{c.seller_store_name || c.buyer_name || "Conversation"}</strong>
                    {c.unread_count > 0 && (
                      <em className="count-badge" style={{ position: "static", border: 0 }}>{c.unread_count}</em>
                    )}
                  </div>
                  <div className="muted" style={{ fontSize: 13, marginTop: 4, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                    {c.last_message || "No messages yet"}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
        <div style={{ flex: 1 }} className="card">
          {!activeId ? (
            <p className="muted">Select a conversation to view messages.</p>
          ) : (
            <>
              <div style={{ minHeight: 300, maxHeight: 400, overflowY: "auto", display: "flex", flexDirection: "column", gap: 8, padding: 8 }}>
                {messages.map((m) => {
                  const mine = currentUserId !== null && m.sender_user_id === currentUserId;
                  return (
                    <div
                      key={m.id}
                      style={{
                        alignSelf: mine ? "flex-end" : "flex-start",
                        background: mine ? "var(--primary)" : "var(--bg-elev-2)",
                        color: mine ? "#fff" : "var(--fg)",
                        padding: "10px 14px",
                        borderRadius: 14,
                        maxWidth: "75%",
                        border: mine ? "0" : "1px solid var(--border)",
                      }}
                    >
                      <div>{m.body}</div>
                      <div style={{ fontSize: 10, opacity: 0.7, marginTop: 4 }}>
                        {new Date(m.created_at).toLocaleString()}
                      </div>
                    </div>
                  );
                })}
              </div>
              <form onSubmit={send} className="flex" style={{ marginTop: 12 }}>
                <textarea
                  className="input"
                  value={body}
                  onChange={(e) => setBody(e.target.value)}
                  placeholder="Type a message…"
                  rows={2}
                  style={{ flex: 1 }}
                />
                <button type="submit" className="btn" disabled={sending || !body.trim()}>Send</button>
              </form>
            </>
          )}
        </div>
      </div>
    </>
  );
}
