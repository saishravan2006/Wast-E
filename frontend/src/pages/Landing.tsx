/* ── Landing Page ── */
import { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { categoryIcon, MATERIAL_CATEGORIES } from "../types";

export default function Landing() {
  const [search, setSearch] = useState("");
  const [location, setLoc] = useState("");
  const navigate = useNavigate();

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    const params = new URLSearchParams();
    if (search) params.set("search", search);
    if (location) params.set("city", location);
    navigate(`/browse?${params}`);
  };

  return (
    <div className="animate-fade-in">
      {/* Hero */}
      <section className="bg-gradient-to-br from-primary-700 via-primary-600 to-primary-800 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 sm:py-24">
          <div className="max-w-3xl">
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold leading-tight mb-4">
              A second chance for<br />rejected materials.
            </h1>
            <p className="text-lg sm:text-xl text-primary-100 mb-8 leading-relaxed">
              Sell a rejected batch, find suitable material, or request recovery support.
            </p>

            {/* Search bar */}
            <form onSubmit={handleSearch} className="flex flex-col sm:flex-row gap-3 mb-8">
              <input type="text" value={search} onChange={e => setSearch(e.target.value)}
                placeholder="Search material type, grade..."
                className="flex-1 px-5 py-4 rounded-xl text-charcoal placeholder:text-gray-400
                         bg-white/95 backdrop-blur focus:outline-none focus:ring-2 focus:ring-primary-300" />
              <input type="text" value={location} onChange={e => setLoc(e.target.value)}
                placeholder="City or pincode"
                className="sm:w-48 px-5 py-4 rounded-xl text-charcoal placeholder:text-gray-400
                         bg-white/95 backdrop-blur focus:outline-none focus:ring-2 focus:ring-primary-300" />
              <button type="submit" className="btn bg-pending-500 text-white hover:bg-pending-600
                                             !rounded-xl !px-8 !py-4 font-bold shadow-lg">
                Search
              </button>
            </form>

            {/* CTAs */}
            <div className="flex flex-col sm:flex-row gap-3">
              <Link to="/create-listing" className="btn bg-white text-primary-700 hover:bg-primary-50
                                                   !px-8 !py-4 font-bold shadow-lg !rounded-xl">
                List Rejected Material
              </Link>
              <Link to="/browse" className="btn bg-primary-600/50 text-white border-2 border-white/30
                                           hover:bg-primary-600/70 !px-8 !py-4 font-bold !rounded-xl">
                Browse Materials
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Material category shortcuts */}
      <section className="page-container -mt-8 relative z-10">
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
          {MATERIAL_CATEGORIES.map(cat => (
            <Link key={cat.value} to={`/browse?material_category=${cat.value}`}
              className="card p-5 text-center hover:border-primary-300 group cursor-pointer">
              <span className="text-3xl mb-2 block group-hover:scale-110 transition-transform">
                {categoryIcon(cat.value)}
              </span>
              <span className="text-sm font-semibold text-charcoal">{cat.label}</span>
              {cat.value !== "plastics" && (
                <span className="block text-[10px] text-charcoal-lighter mt-1">Coming soon</span>
              )}
            </Link>
          ))}
        </div>
      </section>

      {/* How it works — 4 steps */}
      <section className="page-container py-16">
        <h2 className="section-title text-center mb-2">How Wast-e Works</h2>
        <p className="section-subtitle text-center">Four steps from rejected batch to recovery or sale</p>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mt-10">
          {[
            { step: "1", title: "List the Batch", desc: "Describe your rejected material, add photos, and set your terms." },
            { step: "2", title: "Assess Suitability", desc: "Our team or a buyer reviews the material. Assessment findings are recorded transparently." },
            { step: "3", title: "Agree Route & Costs", desc: "Choose direct sale or managed recovery. Review an itemised quote before committing." },
            { step: "4", title: "Deliver & Settle", desc: "Material is picked up, processed if needed, delivered, and payment is settled." },
          ].map(s => (
            <div key={s.step} className="text-center animate-slide-up" style={{ animationDelay: `${parseInt(s.step) * 100}ms` }}>
              <div className="w-14 h-14 rounded-2xl bg-primary-100 text-primary-700 font-bold text-xl
                            flex items-center justify-center mx-auto mb-4">
                {s.step}
              </div>
              <h3 className="font-bold text-charcoal mb-2">{s.title}</h3>
              <p className="text-sm text-charcoal-lighter leading-relaxed">{s.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Direct vs Recovery */}
      <section className="bg-primary-50/50">
        <div className="page-container py-16">
          <h2 className="section-title text-center mb-8">Two Ways to Move Material</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-4xl mx-auto">
            <div className="card p-8">
              <div className="w-12 h-12 rounded-xl bg-primary-100 text-primary-700 flex items-center justify-center text-2xl mb-4">
                🤝
              </div>
              <h3 className="text-lg font-bold text-charcoal mb-3">Direct Trading</h3>
              <p className="text-sm text-charcoal-lighter leading-relaxed mb-4">
                A rejected batch may already suit another buyer. List your material, receive offers, negotiate terms, and arrange delivery directly.
              </p>
              <ul className="text-sm text-charcoal-lighter space-y-1.5">
                <li>• Seller lists, buyer offers</li>
                <li>• Agree specs, price, delivery</li>
                <li>• Buyer inspects on arrival</li>
                <li>• Settle payment</li>
              </ul>
            </div>
            <div className="card p-8">
              <div className="w-12 h-12 rounded-xl bg-pending-100 text-pending-600 flex items-center justify-center text-2xl mb-4">
                🔧
              </div>
              <h3 className="text-lg font-bold text-charcoal mb-3">Managed Recovery</h3>
              <p className="text-sm text-charcoal-lighter leading-relaxed mb-4">
                Material that needs sorting, cleaning, or processing. Wast-e inspects, assesses, proposes a route, and coordinates recovery.
              </p>
              <ul className="text-sm text-charcoal-lighter space-y-1.5">
                <li>• Assessment and sampling</li>
                <li>• Itemised recovery quote</li>
                <li>• Processing and quality check</li>
                <li>• Delivery to matched buyer</li>
              </ul>
              <p className="text-xs text-charcoal-lighter mt-4 italic">
                Not every batch can be recovered. Some batches may be declined after assessment.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Recent listings teaser */}
      <section className="page-container py-16">
        <div className="flex items-center justify-between mb-6">
          <h2 className="section-title">Recent Listings</h2>
          <Link to="/browse" className="btn-secondary !py-2 !px-4 text-sm">View All</Link>
        </div>
        <RecentListings />
      </section>
    </div>
  );
}

function RecentListings() {
  const [listings, setListings] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    import("../api").then(({ default: api }) => {
      api.get("/listings?page_size=6").then(r => setListings(r.data.items || []))
        .catch(() => {}).finally(() => setLoading(false));
    });
  }, []);

  if (loading) return <div className="text-center py-8 text-charcoal-lighter">Loading recent listings...</div>;
  if (!listings.length) return <div className="text-center py-8 text-charcoal-lighter">No listings yet.</div>;

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
      {listings.map(l => (
        <Link to={`/listings/${l.id}`} key={l.id} className="card p-5 hover:border-primary-300 group animate-slide-up">
          <div className="flex items-start justify-between mb-3">
            <span className="badge-active">{categoryIcon(l.material_category)} {l.material_category?.replace(/_/g, " ")}</span>
            <span className="badge-info text-[10px]">{l.status?.replace(/_/g, " ")}</span>
          </div>
          <h3 className="font-bold text-charcoal mb-2 group-hover:text-primary-700 transition-colors line-clamp-2">
            {l.title}
          </h3>
          <div className="space-y-1 text-sm text-charcoal-lighter">
            <p>{l.material_grade || "Grade not specified"} • {(l.quantity_grams / 1000).toLocaleString("en-IN")} kg</p>
            <p>📍 {l.city}, {l.state}</p>
            <p className="font-semibold text-charcoal">
              {l.asking_price_paise ? `₹${(l.asking_price_paise / 100).toFixed(2)}/kg` : "Request quote"}
            </p>
          </div>
          {l.is_demo && <span className="block text-[10px] text-pending-500 mt-2">DEMO DATA</span>}
        </Link>
      ))}
    </div>
  );
}
