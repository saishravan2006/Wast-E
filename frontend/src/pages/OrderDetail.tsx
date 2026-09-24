/* ── Order Detail with timeline, messaging, disputes, payments ── */
import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import api from "../api";
import { useAuth } from "../auth";
import type { Order, TimelineEvent, Message as MsgType, Payment, Settlement, Dispute } from "../types";
import { humanise } from "../types";
import { formatWeight, formatPrice, formatDate, formatDateTime, formatINR } from "../utils";

export default function OrderDetail() {
  const { id } = useParams();
  const { user } = useAuth();
  const [order, setOrder] = useState<Order | null>(null);
  const [timeline, setTimeline] = useState<TimelineEvent[]>([]);
  const [messages, setMessages] = useState<MsgType[]>([]);
  const [payments, setPayments] = useState<Payment[]>([]);
  const [settlement, setSettlement] = useState<Settlement | null>(null);
  const [disputes, setDisputes] = useState<Dispute[]>([]);
  const [loading, setLoading] = useState(true);
  const [msgBody, setMsgBody] = useState("");
  const [tab, setTab] = useState("timeline");

  // Dispute form
  const [showDispute, setShowDispute] = useState(false);
  const [disputeType, setDisputeType] = useState("material_quality");
  const [disputeDesc, setDisputeDesc] = useState("");
  const [disputeRes, setDisputeRes] = useState("");

  useEffect(() => {
    Promise.all([
      api.get(`/orders/${id}`).then(r => setOrder(r.data)),
      api.get(`/messages/order/${id}`).then(r => setMessages(r.data)).catch(() => {}),
      api.get(`/payments/order/${id}`).then(r => setPayments(r.data)).catch(() => {}),
      api.get(`/payments/settlement/${id}`).then(r => { if (r.data) setSettlement(r.data); }).catch(() => {}),
      api.get("/disputes").then(r => setDisputes(r.data.filter((d: Dispute) => d.order_id === id))).catch(() => {}),
    ]).catch(() => {}).finally(() => setLoading(false));

    // Timeline — try recovery first, then audit
    api.get(`/recovery`).then(r => {
      const job = r.data.find((j: any) => j.order_id === id);
      if (job) {
        api.get(`/recovery/${job.id}/timeline`).then(r2 => setTimeline(r2.data)).catch(() => {});
      }
    }).catch(() => {});
  }, [id]);

  const sendMessage = async () => {
    if (!msgBody.trim()) return;
    await api.post("/messages", { order_id: id, body: msgBody });
    setMsgBody("");
    const r = await api.get(`/messages/order/${id}`);
    setMessages(r.data);
  };

  const transitionOrder = async (status: string) => {
    try {
      await api.post(`/orders/${id}/transition?new_status=${status}`);
      const r = await api.get(`/orders/${id}`);
      setOrder(r.data);
    } catch (e: any) {
      alert(e.response?.data?.detail || "Cannot transition");
    }
  };

  const simulatePayment = async () => {
    if (!order) return;
    try {
      await api.post(`/payments/simulate?order_id=${order.id}&amount_paise=${order.agreed_price_paise * (order.agreed_quantity_grams / 1000)}`);
      const r = await api.get(`/payments/order/${id}`);
      setPayments(r.data);
    } catch (e: any) {
      alert(e.response?.data?.detail || "Failed");
    }
  };

  const submitDispute = async () => {
    try {
      await api.post("/disputes", {
        order_id: id, dispute_type: disputeType, description: disputeDesc,
        requested_resolution: disputeRes,
      });
      setShowDispute(false);
      const r = await api.get("/disputes");
      setDisputes(r.data.filter((d: Dispute) => d.order_id === id));
      const or = await api.get(`/orders/${id}`);
      setOrder(or.data);
    } catch (e: any) {
      alert(e.response?.data?.detail || "Failed");
    }
  };

  if (loading) return <div className="page-container text-center py-20 text-charcoal-lighter">Loading...</div>;
  if (!order) return <div className="page-container">Order not found</div>;

  const nextActions: Record<string, string[]> = {
    created: ["inspection_confirmed", "cancelled"],
    inspection_confirmed: ["pickup_arranged"],
    pickup_arranged: ["in_transit"],
    in_transit: ["delivered"],
    delivered: ["buyer_inspecting"],
    buyer_inspecting: ["accepted", "disputed"],
    accepted: ["settlement_recorded"],
    settlement_recorded: ["closed"],
  };

  return (
    <div className="page-container animate-fade-in">
      <nav className="text-sm text-charcoal-lighter mb-4">
        <Link to="/orders" className="hover:text-primary-700">Orders</Link> / <span className="text-charcoal">{order.agreed_material}</span>
      </nav>

      <div className="flex flex-col sm:flex-row justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl font-bold text-charcoal">{order.agreed_material}</h1>
          <p className="text-charcoal-lighter">
            {order.order_type === "direct" ? "Direct Trade" : "Managed Recovery"} •
            {formatWeight(order.agreed_quantity_grams)} • {formatPrice(order.agreed_price_paise, order.price_unit)}
          </p>
          {order.is_demo && <span className="badge-pending text-xs mt-1 inline-block">DEMO DATA</span>}
        </div>
        <span className={`badge-${order.status === "closed" ? "success" : order.status.includes("disput") ? "error" : "pending"} self-start text-sm`}>
          {humanise(order.status)}
        </span>
      </div>

      {/* Info cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
        <div className="card p-4">
          <p className="text-xs text-charcoal-lighter">Seller</p>
          <p className="font-semibold">{order.seller_name || "—"}</p>
        </div>
        <div className="card p-4">
          <p className="text-xs text-charcoal-lighter">Buyer</p>
          <p className="font-semibold">{order.buyer_name || "—"}</p>
        </div>
        <div className="card p-4">
          <p className="text-xs text-charcoal-lighter">Created</p>
          <p className="font-semibold">{formatDate(order.created_at)}</p>
        </div>
      </div>

      {/* Actions */}
      {nextActions[order.status] && (
        <div className="card p-4 mb-6 flex flex-wrap gap-2">
          <span className="text-sm text-charcoal-lighter mr-2">Actions:</span>
          {nextActions[order.status]?.map(s => (
            <button key={s} onClick={() => transitionOrder(s)}
              className={s.includes("cancel") || s.includes("disput") ? "btn-danger btn-sm" : "btn-primary btn-sm"}>
              {humanise(s)}
            </button>
          ))}
          {order.status === "accepted" && (
            <button onClick={simulatePayment} className="btn-pending btn-sm">Simulate Payment (Demo)</button>
          )}
          <button onClick={() => setShowDispute(true)} className="btn-ghost btn-sm text-red-600">Open Dispute</button>
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-1 border-b border-gray-200 mb-6 overflow-x-auto">
        {["timeline", "messages", "payments", "disputes"].map(t => (
          <button key={t} onClick={() => setTab(t)}
            className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${
              tab === t ? "border-primary-700 text-primary-700" : "border-transparent text-charcoal-lighter hover:text-charcoal"
            }`}>{humanise(t)}</button>
        ))}
      </div>

      {tab === "timeline" && (
        <div className="space-y-4 animate-fade-in">
          {timeline.length === 0 ? <p className="text-charcoal-lighter">No events recorded yet.</p> :
            timeline.map((e, i) => (
              <div key={i} className="flex gap-4">
                <div className="flex flex-col items-center">
                  <div className={`w-3 h-3 rounded-full ${
                    e.type === "quality_check" ? (e.passed ? "bg-teal-500" : "bg-red-500") :
                    e.type === "weight" ? "bg-blue-500" : "bg-primary-500"
                  }`} />
                  {i < timeline.length - 1 && <div className="w-0.5 flex-1 bg-gray-200 mt-1" />}
                </div>
                <div className="pb-4">
                  <p className="text-sm font-medium text-charcoal">
                    {e.type === "audit" ? humanise(e.action) :
                     e.type === "weight" ? `Weight recorded: ${e.stage} — ${formatWeight(e.weight_grams)}` :
                     e.type === "processing" ? `Processing: ${e.event_type}` :
                     e.type === "quality_check" ? `QC: ${e.passed ? "Passed ✓" : "Failed ✗"}` : e.type}
                  </p>
                  {e.description && <p className="text-xs text-charcoal-lighter">{e.description}</p>}
                  {e.failure_reason && <p className="text-xs text-red-600">{e.failure_reason}</p>}
                  {e.notes && <p className="text-xs text-charcoal-lighter">{e.notes}</p>}
                  <p className="text-[10px] text-charcoal-lighter mt-1">
                    {formatDateTime(e.timestamp)} {e.actor && `• ${e.actor}`}
                  </p>
                </div>
              </div>
            ))
          }
        </div>
      )}

      {tab === "messages" && (
        <div className="animate-fade-in">
          <div className="space-y-3 mb-4 max-h-96 overflow-y-auto">
            {messages.map(m => (
              <div key={m.id} className={`p-3 rounded-xl max-w-[80%] ${
                m.sender_id === user?.id ? "bg-primary-50 ml-auto" : "bg-gray-100"
              }`}>
                <p className="text-xs font-semibold text-charcoal-lighter mb-1">{m.sender_name}</p>
                <p className="text-sm text-charcoal">{m.body}</p>
                <p className="text-[10px] text-charcoal-lighter mt-1">{formatDateTime(m.created_at)}</p>
              </div>
            ))}
            {messages.length === 0 && <p className="text-charcoal-lighter text-sm">No messages yet.</p>}
          </div>
          <div className="flex gap-2">
            <input className="input-field flex-1" placeholder="Type a message..."
              value={msgBody} onChange={e => setMsgBody(e.target.value)}
              onKeyDown={e => e.key === "Enter" && sendMessage()} />
            <button onClick={sendMessage} className="btn-primary !px-6">Send</button>
          </div>
        </div>
      )}

      {tab === "payments" && (
        <div className="animate-fade-in space-y-4">
          {payments.map(p => (
            <div key={p.id} className="card p-4 flex items-center justify-between">
              <div>
                <p className="font-medium">{formatINR(p.amount_paise)}</p>
                <p className="text-xs text-charcoal-lighter">{formatDateTime(p.created_at)}</p>
              </div>
              <div className="flex items-center gap-2">
                <span className={`badge-${p.status === "paid" ? "success" : "pending"}`}>{humanise(p.status)}</span>
                {p.is_simulated && <span className="badge-pending text-[10px]">SIMULATED</span>}
              </div>
            </div>
          ))}
          {settlement && (
            <div className="card p-6 border-t-4 border-primary-500">
              <h4 className="font-bold text-charcoal mb-3">Settlement</h4>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between"><span className="text-charcoal-lighter">Seller Proceeds</span><span className="font-bold text-primary-700">{formatINR(settlement.total_seller_proceeds_paise)}</span></div>
                <div className="flex justify-between"><span className="text-charcoal-lighter">Buyer Payment</span><span className="font-bold">{formatINR(settlement.total_buyer_payment_paise)}</span></div>
                {settlement.is_simulated && <p className="text-[10px] text-pending-500">SIMULATED SETTLEMENT — DEMO</p>}
              </div>
            </div>
          )}
          {payments.length === 0 && !settlement && <p className="text-charcoal-lighter">No payments recorded.</p>}
        </div>
      )}

      {tab === "disputes" && (
        <div className="animate-fade-in space-y-4">
          {disputes.map(d => (
            <div key={d.id} className="card p-4 border-l-4 border-red-400">
              <div className="flex justify-between mb-2">
                <span className="font-medium text-red-700">{humanise(d.dispute_type)}</span>
                <span className={`badge-${d.status === "resolved" ? "success" : "error"}`}>{d.status}</span>
              </div>
              <p className="text-sm text-charcoal">{d.description}</p>
              {d.requested_resolution && <p className="text-sm text-charcoal-lighter mt-1">Resolution requested: {d.requested_resolution}</p>}
              {d.admin_resolution && <p className="text-sm text-primary-700 mt-1">Admin resolution: {d.admin_resolution}</p>}
            </div>
          ))}
          {disputes.length === 0 && <p className="text-charcoal-lighter">No disputes.</p>}
        </div>
      )}

      {/* Dispute modal */}
      {showDispute && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" onClick={() => setShowDispute(false)}>
          <div className="bg-white rounded-2xl p-6 max-w-md w-full" onClick={e => e.stopPropagation()}>
            <h3 className="text-xl font-bold mb-4">Open a Dispute</h3>
            <div className="space-y-4">
              <div>
                <label className="input-label">Type</label>
                <select className="input-field" value={disputeType} onChange={e => setDisputeType(e.target.value)}>
                  {["weight_difference", "material_quality", "delivery_damage", "payment", "additional_costs", "other"]
                    .map(t => <option key={t} value={t}>{humanise(t)}</option>)}
                </select>
              </div>
              <div>
                <label className="input-label">Description *</label>
                <textarea className="input-field" rows={4} value={disputeDesc} onChange={e => setDisputeDesc(e.target.value)} />
              </div>
              <div>
                <label className="input-label">Requested Resolution</label>
                <textarea className="input-field" rows={2} value={disputeRes} onChange={e => setDisputeRes(e.target.value)} />
              </div>
              <div className="flex gap-3">
                <button onClick={submitDispute} className="btn-danger flex-1">Submit Dispute</button>
                <button onClick={() => setShowDispute(false)} className="btn-ghost flex-1">Cancel</button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
