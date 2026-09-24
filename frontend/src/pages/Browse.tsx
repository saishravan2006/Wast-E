/* ── Browse / Marketplace page — grid+list views, full filters ── */
import { useState, useEffect } from "react";
import { Link, useSearchParams } from "react-router-dom";
import api from "../api";
import type { Listing, PaginatedResponse } from "../types";
import { MATERIAL_CATEGORIES, REJECTION_REASONS, LISTING_STATUSES, categoryIcon } from "../types";
import { formatPrice, formatWeight, formatDate, humanise, timeAgo } from "../utils";

export default function Browse() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [listings, setListings] = useState<Listing[]>([]);
  const [total, setTotal] = useState(0);
  const [pages, setPages] = useState(0);
  const [loading, setLoading] = useState(true);
  const [view, setView] = useState<"grid" | "list">("grid");
  const [showFilters, setShowFilters] = useState(false);

  const page = parseInt(searchParams.get("page") || "1");
  const material_category = searchParams.get("material_category") || "";
  const city = searchParams.get("city") || "";
  const search = searchParams.get("search") || "";

  const [filters, setFilters] = useState({
    material_category, city, search,
    material_grade: "", state: "", pincode: "",
    rejection_reason: "", preferred_route: "", has_assessment: "",
    min_quantity_grams: "", max_quantity_grams: "",
    min_price_paise: "", max_price_paise: "",
  });

  useEffect(() => {
    setLoading(true);
    const params: Record<string, string> = { page: String(page), page_size: "12" };
    Object.entries(filters).forEach(([k, v]) => { if (v) params[k] = v; });
    api.get("/listings", { params })
      .then(r => {
        setListings(r.data.items || []);
        setTotal(r.data.total || 0);
        setPages(r.data.pages || 0);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [page, filters.material_category, filters.city, filters.search]);

  const applyFilters = () => {
    const p = new URLSearchParams();
    Object.entries(filters).forEach(([k, v]) => { if (v) p.set(k, v); });
    setSearchParams(p);
    setShowFilters(false);
    setLoading(true);
    api.get("/listings", { params: { page: "1", page_size: "12", ...Object.fromEntries(Object.entries(filters).filter(([, v]) => v)) } })
      .then(r => { setListings(r.data.items || []); setTotal(r.data.total || 0); setPages(r.data.pages || 0); })
      .finally(() => setLoading(false));
  };

  const clearFilters = () => {
    setFilters({ material_category: "", city: "", search: "", material_grade: "", state: "", pincode: "",
      rejection_reason: "", preferred_route: "", has_assessment: "", min_quantity_grams: "", max_quantity_grams: "",
      min_price_paise: "", max_price_paise: "" });
    setSearchParams({});
  };

  return (
    <div className="page-container animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-6 gap-4">
        <div>
          <h1 className="section-title">Browse Materials</h1>
          <p className="text-charcoal-lighter">{total} listing{total !== 1 ? "s" : ""} available</p>
        </div>
        <div className="flex items-center gap-3">
          <button onClick={() => setShowFilters(!showFilters)}
            className="btn-secondary !py-2 !px-4 text-sm">
            {showFilters ? "Hide" : "Show"} Filters
          </button>
          <div className="flex rounded-lg border border-gray-200 overflow-hidden">
            <button onClick={() => setView("grid")}
              className={`px-3 py-2 text-sm ${view === "grid" ? "bg-primary-100 text-primary-700" : "bg-white text-charcoal-lighter"}`}>
              Grid
            </button>
            <button onClick={() => setView("list")}
              className={`px-3 py-2 text-sm ${view === "list" ? "bg-primary-100 text-primary-700" : "bg-white text-charcoal-lighter"}`}>
              List
            </button>
          </div>
        </div>
      </div>

      {/* Filter panel */}
      {showFilters && (
        <div className="card p-6 mb-6 animate-fade-in">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div>
              <label className="input-label">Material Category</label>
              <select className="input-field" value={filters.material_category}
                onChange={e => setFilters({ ...filters, material_category: e.target.value })}>
                <option value="">All categories</option>
                {MATERIAL_CATEGORIES.map(c => <option key={c.value} value={c.value}>{c.label}</option>)}
              </select>
            </div>
            <div>
              <label className="input-label">Grade / Polymer</label>
              <input className="input-field" placeholder="e.g. HDPE, PET"
                value={filters.material_grade} onChange={e => setFilters({ ...filters, material_grade: e.target.value })} />
            </div>
            <div>
              <label className="input-label">City</label>
              <input className="input-field" placeholder="e.g. Chennai"
                value={filters.city} onChange={e => setFilters({ ...filters, city: e.target.value })} />
            </div>
            <div>
              <label className="input-label">State</label>
              <input className="input-field" placeholder="e.g. Tamil Nadu"
                value={filters.state} onChange={e => setFilters({ ...filters, state: e.target.value })} />
            </div>
            <div>
              <label className="input-label">Pincode</label>
              <input className="input-field" placeholder="e.g. 600032"
                value={filters.pincode} onChange={e => setFilters({ ...filters, pincode: e.target.value })} />
            </div>
            <div>
              <label className="input-label">Rejection Reason</label>
              <select className="input-field" value={filters.rejection_reason}
                onChange={e => setFilters({ ...filters, rejection_reason: e.target.value })}>
                <option value="">Any</option>
                {REJECTION_REASONS.map(r => <option key={r.value} value={r.value}>{r.label}</option>)}
              </select>
            </div>
            <div>
              <label className="input-label">Route</label>
              <select className="input-field" value={filters.preferred_route}
                onChange={e => setFilters({ ...filters, preferred_route: e.target.value })}>
                <option value="">Any</option>
                <option value="direct_sale">Direct Sale</option>
                <option value="managed_recovery">Managed Recovery</option>
              </select>
            </div>
            <div>
              <label className="input-label">Assessment</label>
              <select className="input-field" value={filters.has_assessment}
                onChange={e => setFilters({ ...filters, has_assessment: e.target.value })}>
                <option value="">Any</option>
                <option value="true">Has assessment</option>
                <option value="false">No assessment</option>
              </select>
            </div>
            <div>
              <label className="input-label">Search</label>
              <input className="input-field" placeholder="Keywords..."
                value={filters.search} onChange={e => setFilters({ ...filters, search: e.target.value })} />
            </div>
          </div>
          <div className="flex gap-3 mt-4">
            <button onClick={applyFilters} className="btn-primary !py-2 text-sm">Apply Filters</button>
            <button onClick={clearFilters} className="btn-ghost !py-2 text-sm">Clear All</button>
          </div>
        </div>
      )}

      {/* Listings */}
      {loading ? (
        <div className="text-center py-16 text-charcoal-lighter">Loading listings...</div>
      ) : listings.length === 0 ? (
        <div className="text-center py-16">
          <p className="text-2xl mb-2">📦</p>
          <p className="text-charcoal-lighter">No listings match your filters</p>
          <button onClick={clearFilters} className="btn-secondary mt-4 text-sm !py-2">Clear Filters</button>
        </div>
      ) : view === "grid" ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {listings.map(l => <ListingCard key={l.id} listing={l} />)}
        </div>
      ) : (
        <div className="space-y-4">
          {listings.map(l => <ListingRow key={l.id} listing={l} />)}
        </div>
      )}

      {/* Pagination */}
      {pages > 1 && (
        <div className="flex items-center justify-center gap-2 mt-8">
          {Array.from({ length: pages }, (_, i) => i + 1).map(p => (
            <button key={p} onClick={() => setSearchParams(prev => { prev.set("page", String(p)); return prev; })}
              className={`px-3 py-2 rounded-lg text-sm font-medium ${p === page ? "bg-primary-700 text-white" : "bg-white text-charcoal-lighter hover:bg-primary-50"}`}>
              {p}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

function ListingCard({ listing: l }: { listing: Listing }) {
  const statusInfo = LISTING_STATUSES[l.status] || { label: l.status, color: "neutral" };
  return (
    <Link to={`/listings/${l.id}`} className="card p-5 hover:border-primary-300 group animate-slide-up block">
      {/* Header badges */}
      <div className="flex items-start justify-between mb-3">
        <span className="badge-active text-xs">
          {categoryIcon(l.material_category)} {humanise(l.material_category)}
        </span>
        <span className={`badge-${statusInfo.color} text-[10px]`}>{statusInfo.label}</span>
      </div>

      {/* Title */}
      <h3 className="font-bold text-charcoal mb-2 group-hover:text-primary-700 transition-colors line-clamp-2">
        {l.title}
      </h3>

      {/* Details */}
      <div className="space-y-1.5 text-sm text-charcoal-lighter">
        <p>{l.material_grade || "Grade not specified"} • {humanise(l.physical_form)}</p>
        <p className="font-medium text-charcoal">{formatWeight(l.quantity_grams)}</p>
        <p>📍 {l.city}, {l.state}</p>
        <p className="font-semibold text-primary-700">{formatPrice(l.asking_price_paise, l.price_unit)}</p>
        <p className="text-xs">Rejected: {humanise(l.rejection_reason)}</p>
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between mt-4 pt-3 border-t border-gray-100">
        <div className="flex items-center gap-2">
          {l.has_assessment && <span className="badge-info text-[10px]">Assessment available</span>}
        </div>
        <span className="text-xs text-charcoal-lighter">{timeAgo(l.created_at)}</span>
      </div>

      {/* Labels */}
      <div className="mt-2 space-y-1">
        <p className="text-[10px] text-charcoal-lighter italic">ℹ️ Seller-declared information</p>
        {l.org_name && <p className="text-xs text-charcoal-lighter">By {l.org_name}</p>}
        {l.is_demo && <p className="text-[10px] text-pending-500 font-medium">DEMO DATA</p>}
      </div>
    </Link>
  );
}

function ListingRow({ listing: l }: { listing: Listing }) {
  const statusInfo = LISTING_STATUSES[l.status] || { label: l.status, color: "neutral" };
  return (
    <Link to={`/listings/${l.id}`} className="card p-4 hover:border-primary-300 flex flex-col sm:flex-row gap-4 group block">
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <span className="badge-active text-xs">{categoryIcon(l.material_category)} {humanise(l.material_category)}</span>
          <span className={`badge-${statusInfo.color} text-[10px]`}>{statusInfo.label}</span>
          {l.has_assessment && <span className="badge-info text-[10px]">Assessed</span>}
        </div>
        <h3 className="font-bold text-charcoal group-hover:text-primary-700 transition-colors">{l.title}</h3>
        <p className="text-sm text-charcoal-lighter mt-1">
          {l.material_grade || "Grade unknown"} • {humanise(l.physical_form)} • Rejected: {humanise(l.rejection_reason)}
        </p>
        {l.is_demo && <span className="text-[10px] text-pending-500">DEMO DATA</span>}
      </div>
      <div className="flex flex-row sm:flex-col items-end gap-2 sm:gap-1 text-right shrink-0">
        <p className="font-bold text-primary-700">{formatPrice(l.asking_price_paise, l.price_unit)}</p>
        <p className="text-sm text-charcoal">{formatWeight(l.quantity_grams)}</p>
        <p className="text-xs text-charcoal-lighter">📍 {l.city}, {l.state}</p>
        <p className="text-xs text-charcoal-lighter">{timeAgo(l.created_at)}</p>
      </div>
    </Link>
  );
}
