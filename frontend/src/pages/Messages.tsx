/* ── Messages page ── */
import { useState, useEffect } from "react";
import api from "../api";
import type { Message as MsgType } from "../types";
import { useAuth } from "../auth";
import { formatDateTime } from "../utils";

export default function Messages() {
  const { user } = useAuth();
  const [messages, setMessages] = useState<MsgType[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // In a real app this would be a proper inbox endpoint.
    // For now, show recent messages from user's orders.
    api.get("/orders").then(async r => {
      const allMsgs: MsgType[] = [];
      for (const order of r.data.slice(0, 10)) {
        try {
          const mr = await api.get(`/messages/order/${order.id}`);
          allMsgs.push(...mr.data);
        } catch {}
      }
      allMsgs.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
      setMessages(allMsgs);
    }).catch(() => {}).finally(() => setLoading(false));
  }, []);

  return (
    <div className="page-container animate-fade-in">
      <h1 className="section-title mb-6">Messages</h1>
      {loading ? <p className="text-charcoal-lighter">Loading...</p> :
       messages.length === 0 ? (
        <div className="card p-12 text-center text-charcoal-lighter">
          <p className="text-2xl mb-2">💬</p>
          <p>No messages yet. Messages appear when you communicate on an order.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {messages.map(m => (
            <div key={m.id} className={`card p-4 ${m.sender_id === user?.id ? "border-l-4 border-primary-300" : ""}`}>
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-sm font-semibold text-charcoal">{m.sender_name || "Unknown"}</p>
                  <p className="text-sm text-charcoal-lighter mt-1">{m.body}</p>
                </div>
                <span className="text-xs text-charcoal-lighter shrink-0">{formatDateTime(m.created_at)}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
