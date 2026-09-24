/* ── How It Works page ── */
import { Link } from "react-router-dom";

export default function HowItWorks() {
  return (
    <div className="page-container max-w-4xl mx-auto animate-fade-in">
      <h1 className="section-title text-center mb-2">How Wast-e Works</h1>
      <p className="section-subtitle text-center mb-12">
        From rejected batch to recovery or sale in four steps
      </p>

      {/* Steps */}
      <div className="space-y-12">
        {[
          { n: "1", title: "List the Batch", desc: "Describe your rejected material: what it is, why it was rejected, how much you have, and where it is. Add photos if available. You can save a draft and come back later.", icon: "📋" },
          { n: "2", title: "Assess Suitability", desc: "Depending on the route:\n\n• Direct sale: Buyers browse, ask questions, and request samples or inspections.\n• Managed recovery: A Wast-e operator samples the batch, records composition, moisture, contamination, and proposes a processing route.\n\nNot every batch can be recovered. Some may be declined after assessment.", icon: "🔬" },
          { n: "3", title: "Agree Route & Costs", desc: "For direct sales: The seller and buyer negotiate price, quantity, and delivery terms.\n\nFor managed recovery: You receive an itemised quote showing transport, processing, packaging, platform fees, and estimated proceeds. You approve a specific quote version before work begins.\n\nEstimates are clearly marked. A quote version cannot be silently changed.", icon: "🤝" },
          { n: "4", title: "Deliver & Settle", desc: "Material is picked up, processed if needed, quality-checked, and delivered to the buyer. Weights are recorded at each stage.\n\nThe buyer inspects on arrival. If accepted, payment is settled. If there's a dispute, both parties submit evidence for resolution.\n\nAll events are logged in an immutable timeline.", icon: "🚛" },
        ].map(s => (
          <div key={s.n} className="flex gap-6 items-start animate-slide-up">
            <div className="w-16 h-16 rounded-2xl bg-primary-100 text-primary-700 font-bold text-2xl
                          flex items-center justify-center shrink-0">{s.icon}</div>
            <div>
              <h3 className="text-xl font-bold text-charcoal mb-2">Step {s.n}: {s.title}</h3>
              <p className="text-charcoal-lighter leading-relaxed whitespace-pre-line">{s.desc}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Direct vs Recovery comparison */}
      <div className="mt-16">
        <h2 className="text-xl font-bold text-charcoal text-center mb-8">Direct Trading vs Managed Recovery</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-left py-3 px-4 text-charcoal-lighter font-medium"></th>
                <th className="text-left py-3 px-4 font-semibold text-primary-700">Direct Trading</th>
                <th className="text-left py-3 px-4 font-semibold text-pending-600">Managed Recovery</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {[
                ["Best for", "Material suitable as-is for another buyer", "Material needing sorting, cleaning, or processing"],
                ["Who finds the buyer?", "Seller lists, buyers browse and offer", "Wast-e matches to suitable buyers after assessment"],
                ["Processing", "None — material moves directly", "Sorting, washing, drying, or other steps as needed"],
                ["Cost structure", "Agreed price between buyer and seller", "Itemised quote: transport, processing, fees, estimated proceeds"],
                ["Quality check", "Buyer inspects on arrival", "Wast-e QC before dispatch + buyer inspection on arrival"],
                ["Risk", "Buyer bears quality risk after acceptance", "Depends on commercial model (service vs purchase)"],
              ].map(([label, direct, managed], i) => (
                <tr key={i}>
                  <td className="py-3 px-4 font-medium text-charcoal">{label}</td>
                  <td className="py-3 px-4 text-charcoal-lighter">{direct}</td>
                  <td className="py-3 px-4 text-charcoal-lighter">{managed}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* CTA */}
      <div className="text-center mt-16 py-12 bg-primary-50 rounded-2xl">
        <h2 className="text-2xl font-bold text-charcoal mb-4">Ready to get started?</h2>
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Link to="/create-listing" className="btn-primary">List a Rejected Batch</Link>
          <Link to="/browse" className="btn-secondary">Browse Available Materials</Link>
        </div>
      </div>
    </div>
  );
}
