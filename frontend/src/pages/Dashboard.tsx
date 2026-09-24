/* ── Dashboard — role-aware, shows relevant data per role ── */
import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import api from "../api";
import { useAuth } from "../auth";
import type { Listing, Order, RecoveryJob, Notification as NotifType, BuyerRequirement, MatchResult } from "../types";
import { LISTING_STATUSES, RECOVERY_STATUSES, humanise, categoryIcon } from "../types";
import { formatPrice, formatWeight, formatDate, timeAgo } from "../utils";

export default function Dashboard() {
  const { user } = useAuth();
  const [listings, setListings] = useState<Listing[]>([]);
  const [orders, setOrders] = useState<Order[]>([]);
  const [jobs, setJobs] = useState<RecoveryJob[]>([]);
  const [reqs, setReqs] = useState<BuyerRequirement[]>([]);
  const [matches, setMatches] = useState<Record<string, MatchResult[]>>({});
  const [notifications, setNotifications] = useState<NotifType[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetches: Promise<any>[] = [
      api.get("/notifications").then(r => setNotifications(r.data)).catch(() => {}),
      api.get("/orders").then(r => setOrders(r.data)).catch(() => {}),
    ];
    if (user?.is_seller) {
      fetches.push(api.get("/listings/my").then(r => setListings(r.data)).catch(() => {}));
    }
    if (user?.is_buyer) {
      fetches.push(
        api.get("/requirements/my").then(async (r) => {
          setReqs(r.data);
          // Get matches for each requirement
          const m: Record<string, MatchResult[]> = {};
          for (const req of r.data.slice(0, 5)) {
            try {
              const mr = await api.get(`/requirements/${req.id}/matches`);
              m[req.id] = mr.data;
            } catch {}
          }
          setMatches(m);
        }).catch(() => {})
      );
    }
    if (user?.is_operator || user?.is_admin) {
      fetches.push(api.get("/recovery").then(r => setJobs(r.data)).catch(() => {}));
    }
    Promise.all(fetches).finally(() => setLoading(false));
  }, [user]);

  if (loading) return <div className="page-container text-center py-20 text-charcoal-lighter">Loading dashboard...</div>;

  return (
    <div className="page-container animate-fade-in">
      <div className="mb-8">
        <h1 className="section-title">Welcome, {user?.full_name}</h1>
        <p className="section-subtitle">
          {[user?.is_seller && "Seller", user?.is_buyer && "Buyer", user?.is_operator && "Operator", user?.is_admin && "Admin"]
            .filter(Boolean).join(" • ")}
          {user?.org_name && ` — ${user.org_name}`}
        </p>
      </div>

      {/* Notifications */}
      {notifications.filter(n => !n.is_read).length > 0 && (
        <div className="mb-8">
          <h2 className="text-lg font-bold text-charcoal mb-3">Notifications</h2>
          <div className="space-y-2">
            {notifications.filter(n => !n.is_read).slice(0, 5).map(n => (
              <div key={n.id} className="card p-4 flex items-start gap-3 border-l-4 border-pending-400">
                <span className="text-lg">🔔</span>
                <div className="flex-1 min-w-0">
                  <p className="font-semibold text-sm text-charcoal">{n.title}</p>
                  <p className="text-xs text-charcoal-lighter">{n.content}</p>
                </div>
                <span className="text-xs text-charcoal-lighter shrink-0">{timeAgo(n.created_at)}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Seller section */}
        {user?.is_seller && (
          <div>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold text-charcoal">My Listings</h2>
              <Link to="/create-listing" className="btn-primary btn-sm">New Listing</Link>
            </div>
            {listings.length === 0 ? (
              <div className="card p-8 text-center text-charcoal-lighter">
                <p className="text-2xl mb-2">📦</p>
                <p>No listings yet</p>
                <Link to="/create-listing" className="btn-primary mt-4 inline-block">List your first batch</Link>
              </div>
            ) : (
              <div className="space-y-3">
                {listings.slice(0, 8).map(l => {
                  const s = LISTING_STATUSES[l.status] || { label: l.status, color: "neutral" };
                  return (
                    <Link to={`/listings/${l.id}`} key={l.id} className="card p-4 flex items-center gap-3 hover:border-primary-300">
                      <span className="text-xl">{categoryIcon(l.material_category)}</span>
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-charcoal truncate">{l.title}</p>
                        <p className="text-xs text-charcoal-lighter">{formatWeight(l.quantity_grams)} • {l.city}</p>
                      </div>
                      <span className={`badge-${s.color} text-xs`}>{s.label}</span>
                    </Link>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {/* Buyer section */}
        {user?.is_buyer && (
          <div>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold text-charcoal">My Requirements</h2>
              <Link to="/create-requirement" className="btn-primary btn-sm">Post Requirement</Link>
            </div>
            {reqs.length === 0 ? (
              <div className="card p-8 text-center text-charcoal-lighter">
                <p className="text-2xl mb-2">🔍</p>
                <p>No requirements posted</p>
              </div>
            ) : (
              <div className="space-y-3">
                {reqs.slice(0, 5).map(r => (
                  <div key={r.id} className="card p-4">
                    <p className="font-medium text-charcoal">{r.title}</p>
                    <p className="text-xs text-charcoal-lighter">{humanise(r.material_category)} • {formatWeight(r.required_quantity_grams)}</p>
                    {matches[r.id] && matches[r.id].length > 0 && (
                      <div className="mt-2 pt-2 border-t border-gray-100">
                        <p className="text-xs font-semibold text-primary-700 mb-1">
                          {matches[r.id].length} potential match{matches[r.id].length > 1 ? "es" : ""}
                        </p>
                        {matches[r.id].slice(0, 2).map((m, i) => (
                          <div key={i} className="text-xs text-charcoal-lighter">
                            <Link to={`/listings/${m.listing_id}`} className="text-primary-700 hover:underline">
                              {m.listing_title}
                            </Link>
                            <span className={`ml-2 badge-${m.match_score === "strong" ? "success" : m.match_score === "potential" ? "pending" : "neutral"} text-[10px]`}>
                              {m.match_score}
                            </span>
                            {m.may_need_treatment && <span className="ml-1 text-pending-500">⚠️ treatment may be needed</span>}
                          </div>
                        ))}
                        {matches[r.id].length > 0 && (
                          <div className="mt-1 text-[10px] text-charcoal-lighter italic">
                            Matches: {matches[r.id][0].matches.slice(0, 2).join(", ")}
                            {matches[r.id][0].mismatches.length > 0 && <> • Mismatches: {matches[r.id][0].mismatches[0]}</>}
                            {matches[r.id][0].info_needed.length > 0 && <> • Needs: {matches[r.id][0].info_needed[0]}</>}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Orders */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-bold text-charcoal">Orders</h2>
            <Link to="/orders" className="text-sm text-primary-700 hover:underline">View all</Link>
          </div>
          {orders.length === 0 ? (
            <div className="card p-8 text-center text-charcoal-lighter">
              <p>No orders yet</p>
            </div>
          ) : (
            <div className="space-y-3">
              {orders.slice(0, 5).map(o => (
                <Link to={`/orders/${o.id}`} key={o.id} className="card p-4 hover:border-primary-300 block">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium text-charcoal">{o.agreed_material}</p>
                      <p className="text-xs text-charcoal-lighter">
                        {formatWeight(o.agreed_quantity_grams)} • {o.order_type === "direct" ? "Direct" : "Recovery"}
                      </p>
                    </div>
                    <span className={`badge-${o.status === "closed" ? "success" : o.status.includes("disput") ? "error" : "pending"} text-xs`}>
                      {humanise(o.status)}
                    </span>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>

        {/* Recovery jobs (operator/admin) */}
        {(user?.is_operator || user?.is_admin) && (
          <div>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold text-charcoal">Recovery Jobs</h2>
              <Link to="/recovery" className="text-sm text-primary-700 hover:underline">View all</Link>
            </div>
            {jobs.length === 0 ? (
              <div className="card p-8 text-center text-charcoal-lighter"><p>No recovery jobs</p></div>
            ) : (
              <div className="space-y-3">
                {jobs.slice(0, 5).map(j => {
                  const s = RECOVERY_STATUSES[j.status] || { label: j.status, color: "neutral" };
                  return (
                    <Link to={`/recovery/${j.id}`} key={j.id} className="card p-4 hover:border-primary-300 block">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="font-mono text-sm text-charcoal">{j.batch_code || j.id.slice(0, 8)}</p>
                          <p className="text-xs text-charcoal-lighter">
                            {j.incoming_weight_grams ? formatWeight(j.incoming_weight_grams) : "Awaiting receipt"}
                          </p>
                        </div>
                        <span className={`badge-${s.color} text-xs`}>{s.label}</span>
                      </div>
                    </Link>
                  );
                })}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
