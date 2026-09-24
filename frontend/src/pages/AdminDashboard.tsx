/* ── Admin Dashboard — verification, moderation, disputes, audit, users ── */
import { useState, useEffect } from "react";
import api from "../api";
import { useAuth } from "../auth";
import type { Organisation, User as UserType, Dispute } from "../types";
import { humanise } from "../types";
import { formatDate, formatDateTime } from "../utils";

export default function AdminDashboard() {
  const { user } = useAuth();
  const [tab, setTab] = useState("verification");
  const [verQueue, setVerQueue] = useState<Organisation[]>([]);
  const [users, setUsers] = useState<UserType[]>([]);
  const [disputes, setDisputes] = useState<Dispute[]>([]);
  const [audit, setAudit] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user?.is_admin) return;
    Promise.all([
      api.get("/admin/verification-queue").then(r => setVerQueue(r.data)).catch(() => {}),
      api.get("/admin/users").then(r => setUsers(r.data)).catch(() => {}),
      api.get("/disputes").then(r => setDisputes(r.data)).catch(() => {}),
      api.get("/admin/audit?page_size=30").then(r => setAudit(r.data)).catch(() => {}),
    ]).finally(() => setLoading(false));
  }, [user]);

  const verifyOrg = async (orgId: string, decision: string) => {
    await api.post(`/admin/verify/${orgId}?decision=${decision}&notes=Demo+verification`);
    const r = await api.get("/admin/verification-queue");
    setVerQueue(r.data);
  };

  const assignRole = async (userId: string, role: string, value: boolean) => {
    await api.post(`/admin/assign-role?user_id=${userId}&role=${role}&value=${value}`);
    const r = await api.get("/admin/users");
    setUsers(r.data);
  };

  const resolveDispute = async (disputeId: string) => {
    const res = prompt("Enter resolution:");
    if (!res) return;
    await api.post(`/disputes/${disputeId}/resolve?resolution=${encodeURIComponent(res)}`);
    const r = await api.get("/disputes");
    setDisputes(r.data);
  };

  if (!user?.is_admin) {
    return <div className="page-container text-center py-20 text-red-600 font-semibold">Administrator access required</div>;
  }

  return (
    <div className="page-container animate-fade-in">
      <h1 className="section-title mb-6">Admin Dashboard</h1>

      {/* Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
        <StatCard label="Pending Verification" value={verQueue.length} color="pending" />
        <StatCard label="Total Users" value={users.length} color="primary" />
        <StatCard label="Open Disputes" value={disputes.filter(d => d.status === "open").length} color="error" />
        <StatCard label="Audit Events" value={audit.length} color="info" />
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b border-gray-200 mb-6 overflow-x-auto">
        {["verification", "users", "disputes", "audit"].map(t => (
          <button key={t} onClick={() => setTab(t)}
            className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${
              tab === t ? "border-primary-700 text-primary-700" : "border-transparent text-charcoal-lighter"
            }`}>{humanise(t)}</button>
        ))}
      </div>

      {loading ? <p className="text-charcoal-lighter">Loading...</p> : (
        <>
          {tab === "verification" && (
            <div className="space-y-4 animate-fade-in">
              <h2 className="text-lg font-bold">Verification Queue</h2>
              {verQueue.length === 0 ? <p className="text-charcoal-lighter">No pending verifications.</p> :
                verQueue.map(org => (
                  <div key={org.id} className="card p-4 flex items-center justify-between">
                    <div>
                      <p className="font-semibold">{org.name}</p>
                      <p className="text-sm text-charcoal-lighter">{humanise(org.org_type)} • {org.city}, {org.state}</p>
                      {org.is_demo && <span className="text-[10px] text-pending-500">DEMO</span>}
                    </div>
                    <div className="flex gap-2">
                      <button onClick={() => verifyOrg(org.id, "approved")} className="btn-primary btn-sm">Verify</button>
                      <button onClick={() => verifyOrg(org.id, "rejected")} className="btn-danger btn-sm">Reject</button>
                    </div>
                  </div>
                ))
              }
            </div>
          )}

          {tab === "users" && (
            <div className="space-y-4 animate-fade-in">
              <h2 className="text-lg font-bold">User Management</h2>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-gray-200 text-left">
                      <th className="py-2 px-3 text-charcoal-lighter">Name</th>
                      <th className="py-2 px-3 text-charcoal-lighter">Email</th>
                      <th className="py-2 px-3 text-charcoal-lighter">Org</th>
                      <th className="py-2 px-3 text-charcoal-lighter">Roles</th>
                      <th className="py-2 px-3 text-charcoal-lighter">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {users.map(u => (
                      <tr key={u.id}>
                        <td className="py-2 px-3 font-medium">{u.full_name} {u.is_demo && <span className="text-[10px] text-pending-500">DEMO</span>}</td>
                        <td className="py-2 px-3 text-charcoal-lighter">{u.email}</td>
                        <td className="py-2 px-3 text-charcoal-lighter">{u.org_name || "—"}</td>
                        <td className="py-2 px-3">
                          <div className="flex gap-1 flex-wrap">
                            {u.is_seller && <span className="badge-active text-[10px]">Seller</span>}
                            {u.is_buyer && <span className="badge-info text-[10px]">Buyer</span>}
                            {u.is_operator && <span className="badge-pending text-[10px]">Operator</span>}
                            {u.is_admin && <span className="badge-error text-[10px]">Admin</span>}
                          </div>
                        </td>
                        <td className="py-2 px-3">
                          <div className="flex gap-1">
                            {!u.is_operator && (
                              <button onClick={() => assignRole(u.id, "operator", true)} className="btn-ghost btn-sm text-[10px]">+Op</button>
                            )}
                            {u.is_operator && (
                              <button onClick={() => assignRole(u.id, "operator", false)} className="btn-ghost btn-sm text-[10px] text-red-500">-Op</button>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {tab === "disputes" && (
            <div className="space-y-4 animate-fade-in">
              <h2 className="text-lg font-bold">Disputes</h2>
              {disputes.length === 0 ? <p className="text-charcoal-lighter">No disputes.</p> :
                disputes.map(d => (
                  <div key={d.id} className="card p-4 border-l-4 border-red-400">
                    <div className="flex items-start justify-between">
                      <div>
                        <p className="font-semibold text-red-700">{humanise(d.dispute_type)}</p>
                        <p className="text-sm text-charcoal mt-1">{d.description}</p>
                        {d.requested_resolution && <p className="text-xs text-charcoal-lighter mt-1">Requested: {d.requested_resolution}</p>}
                        {d.admin_resolution && <p className="text-xs text-primary-700 mt-1">Resolution: {d.admin_resolution}</p>}
                      </div>
                      <div className="flex items-center gap-2">
                        <span className={`badge-${d.status === "resolved" ? "success" : "error"}`}>{d.status}</span>
                        {d.status === "open" && (
                          <button onClick={() => resolveDispute(d.id)} className="btn-primary btn-sm">Resolve</button>
                        )}
                      </div>
                    </div>
                  </div>
                ))
              }
            </div>
          )}

          {tab === "audit" && (
            <div className="animate-fade-in">
              <h2 className="text-lg font-bold mb-4">Audit Log</h2>
              <div className="space-y-2">
                {audit.map((e: any) => (
                  <div key={e.id} className="card p-3 flex items-start gap-3">
                    <div className="w-2 h-2 rounded-full bg-primary-400 mt-2 shrink-0" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm">
                        <span className="font-medium">{e.actor}</span>
                        <span className="text-charcoal-lighter"> • {humanise(e.action)} • </span>
                        <span className="text-charcoal-lighter">{e.entity_type}</span>
                      </p>
                      {e.new_values && (
                        <p className="text-xs text-charcoal-lighter mt-0.5 font-mono truncate">
                          {JSON.stringify(e.new_values).slice(0, 100)}
                        </p>
                      )}
                    </div>
                    <span className="text-[10px] text-charcoal-lighter shrink-0">{formatDateTime(e.timestamp)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

function StatCard({ label, value, color }: { label: string; value: number; color: string }) {
  const colors: Record<string, string> = {
    primary: "bg-primary-50 text-primary-700",
    pending: "bg-pending-50 text-pending-600",
    error: "bg-red-50 text-red-600",
    info: "bg-blue-50 text-blue-600",
  };
  return (
    <div className={`card p-4 text-center ${colors[color] || ""}`}>
      <p className="text-2xl font-bold">{value}</p>
      <p className="text-xs mt-1">{label}</p>
    </div>
  );
}
