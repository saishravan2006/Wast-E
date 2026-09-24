/* ── Recovery Job Detail — operator workflow, weight recording, QC, timeline, QR ── */
import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { QRCodeSVG } from "qrcode.react";
import api from "../api";
import { useAuth } from "../auth";
import type { RecoveryJob, TimelineEvent } from "../types";
import { RECOVERY_STATUSES, humanise } from "../types";
import { formatWeight, formatDate, formatDateTime } from "../utils";

export default function RecoveryJobDetail() {
  const { id } = useParams();
  const { user } = useAuth();
  const [job, setJob] = useState<RecoveryJob | null>(null);
  const [timeline, setTimeline] = useState<TimelineEvent[]>([]);
  const [loading, setLoading] = useState(true);

  // Forms
  const [weightStage, setWeightStage] = useState("incoming");
  const [weightGrams, setWeightGrams] = useState("");
  const [weightNotes, setWeightNotes] = useState("");
  const [eventType, setEventType] = useState("sorting");
  const [eventDesc, setEventDesc] = useState("");
  const [qcPassed, setQcPassed] = useState(true);
  const [qcNotes, setQcNotes] = useState("");
  const [qcFailure, setQcFailure] = useState("");

  const refresh = () => {
    api.get(`/recovery/${id}`).then(r => setJob(r.data)).catch(() => {});
    api.get(`/recovery/${id}/timeline`).then(r => setTimeline(r.data)).catch(() => {});
  };

  useEffect(() => {
    refresh();
    setLoading(false);
  }, [id]);

  const transition = async (status: string) => {
    try {
      await api.post(`/recovery/${id}/transition?new_status=${status}`);
      refresh();
    } catch (e: any) { alert(e.response?.data?.detail || "Cannot transition"); }
  };

  const recordWeight = async () => {
    const grams = Math.round(parseFloat(weightGrams) * 1000);
    if (!grams) return;
    await api.post(`/recovery/${id}/weight?stage=${weightStage}&weight_grams=${grams}&notes=${encodeURIComponent(weightNotes)}`);
    setWeightGrams(""); setWeightNotes("");
    refresh();
  };

  const addEvent = async () => {
    await api.post(`/recovery/${id}/processing-event?event_type=${eventType}&description=${encodeURIComponent(eventDesc)}`);
    setEventDesc("");
    refresh();
  };

  const recordQC = async () => {
    await api.post(`/recovery/${id}/quality-check?passed=${qcPassed}&notes=${encodeURIComponent(qcNotes)}&failure_reason=${encodeURIComponent(qcFailure)}`);
    setQcNotes(""); setQcFailure("");
    refresh();
  };

  if (!job) return <div className="page-container text-center py-20 text-charcoal-lighter">Loading...</div>;

  const s = RECOVERY_STATUSES[job.status] || { label: job.status, color: "neutral" };
  const isOp = user?.is_operator || user?.is_admin;

  return (
    <div className="page-container animate-fade-in">
      <nav className="text-sm text-charcoal-lighter mb-4">
        <Link to="/recovery" className="hover:text-primary-700">Recovery Jobs</Link> / <span className="text-charcoal">{job.batch_code}</span>
      </nav>

      <div className="flex flex-col sm:flex-row justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl font-bold text-charcoal font-mono">{job.batch_code}</h1>
          <span className={`badge-${s.color} mt-1`}>{s.label}</span>
          {job.is_demo && <span className="badge-pending ml-2">DEMO</span>}
        </div>
        <div className="card p-4 flex items-center gap-4 self-start">
          <QRCodeSVG value={`${window.location.origin}/recovery/${job.id}`} size={80} />
          <div className="text-xs text-charcoal-lighter">
            <p>Scan to view</p>
            <p>batch record</p>
          </div>
        </div>
      </div>

      {/* Weight summary */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-4 mb-6">
        <WeightCard label="Incoming" grams={job.incoming_weight_grams} color="blue" />
        <WeightCard label="Output" grams={job.processed_output_grams} color="green" />
        <WeightCard label="Residue" grams={job.residue_grams} color="orange" />
        <WeightCard label="Loss" grams={job.loss_grams} color="red" />
        <div className="card p-3 text-center col-span-2 sm:col-span-1">
          <p className="text-[10px] text-charcoal-lighter mb-1">Recovery Rate</p>
          <p className="text-xl font-bold text-primary-700">
            {job.incoming_weight_grams && job.processed_output_grams
              ? `${((job.processed_output_grams / job.incoming_weight_grams) * 100).toFixed(1)}%`
              : "—"}
          </p>
        </div>
      </div>

      {job.loss_notes && (
        <div className="bg-pending-50 p-3 rounded-lg text-xs text-pending-600 mb-6">
          <strong>Loss notes:</strong> {job.loss_notes}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Timeline */}
        <div>
          <h2 className="text-lg font-bold mb-4">Event Timeline</h2>
          <div className="space-y-3">
            {timeline.map((e, i) => (
              <div key={i} className="flex gap-3">
                <div className="flex flex-col items-center">
                  <div className={`w-2.5 h-2.5 rounded-full ${
                    e.type === "quality_check" ? (e.passed ? "bg-teal-500" : "bg-red-500") :
                    e.type === "weight" ? "bg-blue-500" : "bg-primary-500"
                  }`} />
                  {i < timeline.length - 1 && <div className="w-0.5 flex-1 bg-gray-200 mt-1" />}
                </div>
                <div className="pb-3">
                  <p className="text-sm font-medium text-charcoal">
                    {e.type === "weight" ? `${humanise(e.stage)}: ${formatWeight(e.weight_grams)}` :
                     e.type === "processing" ? humanise(e.event_type || "") :
                     e.type === "quality_check" ? `QC ${e.passed ? "✓ Passed" : "✗ Failed"}` :
                     humanise(e.action || "")}
                  </p>
                  {e.description && <p className="text-xs text-charcoal-lighter">{e.description}</p>}
                  {e.failure_reason && <p className="text-xs text-red-600">{e.failure_reason}</p>}
                  <p className="text-[10px] text-charcoal-lighter">{formatDateTime(e.timestamp)}</p>
                </div>
              </div>
            ))}
            {timeline.length === 0 && <p className="text-charcoal-lighter text-sm">No events yet.</p>}
          </div>
        </div>

        {/* Operator actions */}
        {isOp && (
          <div className="space-y-6">
            <h2 className="text-lg font-bold">Operator Actions</h2>

            {/* Status transitions */}
            <div className="card p-4">
              <h4 className="text-sm font-semibold mb-3">Transition Status</h4>
              <div className="flex flex-wrap gap-2">
                {["screening", "sample_scheduled", "assessment_recorded", "route_proposed",
                  "quote_issued", "seller_approved", "buyer_committed", "pickup_scheduled",
                  "received", "processing", "quality_check", "dispatch",
                  "buyer_acceptance", "settlement", "closed",
                  "declined", "cancelled", "on_hold", "reassessment_required"].map(st => (
                  <button key={st} onClick={() => transition(st)} className="btn-ghost btn-sm text-xs">
                    → {humanise(st)}
                  </button>
                ))}
              </div>
            </div>

            {/* Record weight */}
            <div className="card p-4">
              <h4 className="text-sm font-semibold mb-3">Record Weight</h4>
              <div className="space-y-3">
                <select className="input-field" value={weightStage} onChange={e => setWeightStage(e.target.value)}>
                  <option value="incoming">Incoming</option>
                  <option value="sorted">Sorted</option>
                  <option value="processed">Processed</option>
                  <option value="output">Output</option>
                  <option value="residue">Residue</option>
                </select>
                <input type="number" className="input-field" placeholder="Weight in kg" value={weightGrams}
                  onChange={e => setWeightGrams(e.target.value)} step="0.1" />
                <input className="input-field" placeholder="Notes (optional)" value={weightNotes}
                  onChange={e => setWeightNotes(e.target.value)} />
                <button onClick={recordWeight} className="btn-primary btn-sm w-full">Record Weight</button>
              </div>
            </div>

            {/* Processing event */}
            <div className="card p-4">
              <h4 className="text-sm font-semibold mb-3">Processing Event</h4>
              <div className="space-y-3">
                <select className="input-field" value={eventType} onChange={e => setEventType(e.target.value)}>
                  {["sorting", "manual_sorting", "washing", "drying", "shredding", "grinding",
                    "pelletising", "colour_sorting", "other"].map(t =>
                    <option key={t} value={t}>{humanise(t)}</option>)}
                </select>
                <input className="input-field" placeholder="Description" value={eventDesc}
                  onChange={e => setEventDesc(e.target.value)} />
                <button onClick={addEvent} className="btn-primary btn-sm w-full">Add Event</button>
              </div>
            </div>

            {/* Quality check */}
            <div className="card p-4">
              <h4 className="text-sm font-semibold mb-3">Quality Check</h4>
              <div className="space-y-3">
                <div className="flex gap-3">
                  <label className={`flex-1 p-3 rounded-xl border-2 cursor-pointer text-center text-sm font-medium ${
                    qcPassed ? "border-teal-400 bg-teal-50 text-teal-700" : "border-gray-200"}`}>
                    <input type="radio" checked={qcPassed} onChange={() => setQcPassed(true)} className="sr-only" />
                    ✓ Pass
                  </label>
                  <label className={`flex-1 p-3 rounded-xl border-2 cursor-pointer text-center text-sm font-medium ${
                    !qcPassed ? "border-red-400 bg-red-50 text-red-700" : "border-gray-200"}`}>
                    <input type="radio" checked={!qcPassed} onChange={() => setQcPassed(false)} className="sr-only" />
                    ✗ Fail
                  </label>
                </div>
                <input className="input-field" placeholder="Notes" value={qcNotes} onChange={e => setQcNotes(e.target.value)} />
                {!qcPassed && (
                  <input className="input-field" placeholder="Failure reason" value={qcFailure} onChange={e => setQcFailure(e.target.value)} />
                )}
                <button onClick={recordQC} className={`${qcPassed ? "btn-primary" : "btn-danger"} btn-sm w-full`}>
                  Record QC {qcPassed ? "Pass" : "Fail"}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function WeightCard({ label, grams, color }: { label: string; grams: number | null; color: string }) {
  const colors: Record<string, string> = {
    blue: "text-blue-600", green: "text-teal-600", orange: "text-pending-600", red: "text-red-600",
  };
  return (
    <div className="card p-3 text-center">
      <p className="text-[10px] text-charcoal-lighter mb-1">{label}</p>
      <p className={`text-lg font-bold ${colors[color] || "text-charcoal"}`}>
        {grams ? formatWeight(grams) : "—"}
      </p>
    </div>
  );
}
