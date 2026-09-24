/* ── Formatting utilities for INR, weight, dates ── */

/** Format paise to INR with Indian number system (₹1,23,456) */
export function formatINR(paise: number | null | undefined): string {
  if (paise == null) return "—";
  const rupees = paise / 100;
  // Indian number format: last group of 3, then groups of 2
  const parts = rupees.toFixed(2).split(".");
  let intPart = parts[0];
  const decPart = parts[1];
  const isNeg = intPart.startsWith("-");
  if (isNeg) intPart = intPart.slice(1);

  if (intPart.length > 3) {
    const last3 = intPart.slice(-3);
    const rest = intPart.slice(0, -3);
    const grouped = rest.replace(/\B(?=(\d{2})+(?!\d))/g, ",");
    intPart = grouped + "," + last3;
  }
  return `₹${isNeg ? "-" : ""}${intPart}.${decPart}`;
}

/** Format paise per kg as price display */
export function formatPrice(paise: number | null | undefined, unit = "per_kg"): string {
  if (paise == null) return "Request quote";
  const label = unit === "per_tonne" ? "/tonne" : "/kg";
  return formatINR(paise) + label;
}

/** Format grams to human-readable weight */
export function formatWeight(grams: number | null | undefined, displayUnit = "kg"): string {
  if (grams == null) return "—";
  if (displayUnit === "tonne" || grams >= 10_000_000) {
    return `${(grams / 1_000_000).toLocaleString("en-IN", { maximumFractionDigits: 2 })} tonnes`;
  }
  return `${(grams / 1000).toLocaleString("en-IN", { maximumFractionDigits: 1 })} kg`;
}

/** Format ISO date to local display */
export function formatDate(iso: string | null | undefined): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString("en-IN", {
    day: "numeric", month: "short", year: "numeric",
  });
}

export function formatDateTime(iso: string | null | undefined): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("en-IN", {
    day: "numeric", month: "short", year: "numeric",
    hour: "2-digit", minute: "2-digit",
  });
}

/** Time ago */
export function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "Just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  if (days < 7) return `${days}d ago`;
  return formatDate(iso);
}

/** Humanise enum values */
export function humanise(val: string | null | undefined): string {
  if (!val) return "—";
  return val.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

/** Category icon emoji */
export function categoryIcon(cat: string): string {
  const icons: Record<string, string> = {
    plastics: "♻️", paper_cardboard: "📦", metals: "⚙️",
    glass: "🪟", textiles: "🧵",
  };
  return icons[cat] || "📦";
}
