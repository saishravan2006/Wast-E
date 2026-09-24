/* ── Orders list and Order Detail pages ── */
import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import api from "../api";
import type { Order } from "../types";
import { humanise } from "../types";
import { formatWeight, formatPrice, formatDate } from "../utils";

export default function Orders() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/orders").then(r => setOrders(r.data)).catch(() => {}).finally(() => setLoading(false));
  }, []);

  return (
    <div className="page-container animate-fade-in">
      <h1 className="section-title mb-6">Orders</h1>
      {loading ? <p className="text-charcoal-lighter">Loading...</p> :
       orders.length === 0 ? (
        <div className="card p-12 text-center text-charcoal-lighter">
          <p className="text-2xl mb-2">📋</p>
          <p>No orders yet. Orders are created when an offer is accepted or a recovery quote is approved.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {orders.map(o => (
            <Link to={`/orders/${o.id}`} key={o.id} className="card p-5 hover:border-primary-300 block">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div>
                  <p className="font-bold text-charcoal">{o.agreed_material}</p>
                  <p className="text-sm text-charcoal-lighter">
                    {o.order_type === "direct" ? "Direct Trade" : "Managed Recovery"} •
                    {formatWeight(o.agreed_quantity_grams)} • {formatPrice(o.agreed_price_paise, o.price_unit)}
                  </p>
                  <p className="text-xs text-charcoal-lighter mt-1">
                    Seller: {o.seller_name || "—"} → Buyer: {o.buyer_name || "—"}
                  </p>
                </div>
                <div className="flex items-center gap-3">
                  <span className={`badge-${o.status === "closed" ? "success" : o.status.includes("disput") ? "error" : "pending"}`}>
                    {humanise(o.status)}
                  </span>
                  <span className="text-xs text-charcoal-lighter">{formatDate(o.created_at)}</span>
                </div>
              </div>
              {o.is_demo && <span className="text-[10px] text-pending-500 mt-1 block">DEMO DATA</span>}
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
