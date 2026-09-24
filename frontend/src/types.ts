/* ── TypeScript interfaces mirroring backend schemas ── */

export interface User {
  id: string;
  email: string;
  full_name: string;
  phone: string | null;
  is_seller: boolean;
  is_buyer: boolean;
  is_operator: boolean;
  is_admin: boolean;
  is_demo: boolean;
  org_id: string | null;
  org_name: string | null;
  created_at: string;
}

export interface Organisation {
  id: string;
  name: string;
  org_type: string;
  gstin: string | null;
  city: string | null;
  state: string | null;
  pincode: string | null;
  verification_status: string;
  is_demo: boolean;
}

export interface Photo {
  id: string;
  file_path: string;
  caption: string | null;
  sort_order: number;
}

export interface Listing {
  id: string;
  org_id: string;
  created_by: string;
  title: string;
  material_category: string;
  material_grade: string | null;
  grade_unknown: boolean;
  quantity_grams: number;
  quantity_unit: string;
  physical_form: string;
  description: string | null;
  rejection_reason: string;
  rejection_details: string | null;
  material_source: string | null;
  has_hazardous_contamination: boolean;
  city: string;
  state: string;
  pincode: string;
  asking_price_paise: number | null;
  price_unit: string;
  request_quote: boolean;
  preferred_route: string;
  status: string;
  has_assessment: boolean;
  assessment_date: string | null;
  is_demo: boolean;
  created_at: string;
  updated_at: string;
  photos: Photo[];
  org_name: string | null;
  seller_name: string | null;
}

export interface BuyerRequirement {
  id: string;
  org_id: string;
  title: string;
  material_category: string;
  material_grade: string | null;
  acceptable_forms: string[] | null;
  required_quantity_grams: number;
  quantity_unit: string;
  delivery_city: string;
  delivery_state: string;
  target_price_min_paise: number | null;
  target_price_max_paise: number | null;
  quality_specs: Record<string, any> | null;
  required_by: string | null;
  is_active: boolean;
  created_at: string;
  org_name: string | null;
}

export interface Offer {
  id: string;
  listing_id: string;
  buyer_org_id: string;
  offered_price_paise: number;
  price_unit: string;
  offered_quantity_grams: number;
  terms: string | null;
  message: string | null;
  status: string;
  created_at: string;
  buyer_name: string | null;
}

export interface Assessment {
  id: string;
  listing_id: string;
  assessor_id: string;
  sampling_date: string;
  sampling_method: string;
  sample_size: string;
  observed_composition: Record<string, number> | null;
  moisture_pct: number | null;
  contamination_pct: number | null;
  estimated_recoverable_min_grams: number | null;
  estimated_recoverable_max_grams: number | null;
  proposed_processing_steps: string[] | null;
  uncertainties: string | null;
  outcome: string;
  created_at: string;
}

export interface QuoteVersion {
  id: string;
  version_number: number;
  estimated_incoming_weight_grams: number;
  expected_output_min_grams: number | null;
  expected_output_max_grams: number | null;
  sale_price_paise_per_kg: number | null;
  purchase_price_paise_per_kg: number | null;
  transport_cost_paise: number;
  assessment_cost_paise: number;
  processing_cost_paise: number;
  packaging_cost_paise: number;
  residue_handling_cost_paise: number;
  platform_fee_paise: number;
  tax_paise: number;
  estimated_seller_proceeds_paise: number | null;
  assumptions: string | null;
  is_estimate: boolean;
  expires_at: string | null;
  created_at: string;
}

export interface Quote {
  id: string;
  listing_id: string;
  commercial_model: string;
  current_version: number;
  status: string;
  created_at: string;
  versions: QuoteVersion[];
}

export interface Order {
  id: string;
  listing_id: string;
  seller_org_id: string;
  buyer_org_id: string;
  agreed_material: string;
  agreed_quantity_grams: number;
  agreed_price_paise: number;
  price_unit: string;
  delivery_terms: string | null;
  status: string;
  order_type: string;
  is_demo: boolean;
  created_at: string;
  updated_at: string;
  seller_name: string | null;
  buyer_name: string | null;
}

export interface RecoveryJob {
  id: string;
  listing_id: string;
  order_id: string | null;
  quote_id: string | null;
  operator_id: string | null;
  seller_org_id: string;
  buyer_org_id: string | null;
  status: string;
  incoming_weight_grams: number | null;
  processed_output_grams: number | null;
  residue_grams: number | null;
  loss_grams: number | null;
  loss_notes: string | null;
  batch_code: string | null;
  is_demo: boolean;
  created_at: string;
  updated_at: string;
}

export interface MatchResult {
  listing_id: string | null;
  requirement_id: string | null;
  listing_title: string | null;
  requirement_title: string | null;
  match_score: string;
  matches: string[];
  mismatches: string[];
  info_needed: string[];
  may_need_treatment: boolean;
}

export interface Message {
  id: string;
  order_id: string | null;
  listing_id: string | null;
  sender_id: string;
  body: string;
  is_read: boolean;
  created_at: string;
  sender_name: string | null;
}

export interface Dispute {
  id: string;
  order_id: string;
  raised_by: string;
  dispute_type: string;
  description: string;
  status: string;
  requested_resolution: string | null;
  admin_resolution: string | null;
  created_at: string;
}

export interface TimelineEvent {
  type: string;
  action?: string;
  actor?: string;
  stage?: string;
  weight_grams?: number;
  event_type?: string;
  description?: string;
  passed?: boolean;
  failure_reason?: string;
  notes?: string;
  old_values?: Record<string, any>;
  new_values?: Record<string, any>;
  timestamp: string;
}

export interface Notification {
  id: string;
  notification_type: string;
  title: string;
  content: string;
  link: string | null;
  is_read: boolean;
  created_at: string;
}

export interface Payment {
  id: string;
  order_id: string;
  amount_paise: number;
  currency: string;
  status: string;
  is_simulated: boolean;
  created_at: string;
}

export interface Settlement {
  id: string;
  order_id: string;
  breakdown: Record<string, any>;
  total_seller_proceeds_paise: number;
  total_buyer_payment_paise: number;
  is_simulated: boolean;
  created_at: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

// ── Constants ──

export const MATERIAL_CATEGORIES = [
  { value: "plastics", label: "Plastics" },
  { value: "paper_cardboard", label: "Paper & Cardboard" },
  { value: "metals", label: "Metals" },
  { value: "glass", label: "Glass" },
  { value: "textiles", label: "Textiles" },
] as const;

export const PHYSICAL_FORMS = [
  { value: "loose", label: "Loose" },
  { value: "baled", label: "Baled" },
  { value: "shredded", label: "Shredded" },
  { value: "granulated", label: "Granulated" },
  { value: "other", label: "Other" },
] as const;

export const REJECTION_REASONS = [
  { value: "mixed_materials", label: "Mixed materials" },
  { value: "contamination", label: "Contamination" },
  { value: "excess_moisture", label: "Excess moisture" },
  { value: "colour_mismatch", label: "Colour mismatch" },
  { value: "wrong_grade", label: "Wrong grade" },
  { value: "quantity_mismatch", label: "Quantity mismatch" },
  { value: "documentation_issue", label: "Documentation issue" },
  { value: "other", label: "Other" },
] as const;

export const LISTING_STATUSES: Record<string, { label: string; color: string }> = {
  draft: { label: "Draft", color: "neutral" },
  pending_review: { label: "Pending Review", color: "pending" },
  active: { label: "Active", color: "active" },
  under_assessment: { label: "Under Assessment", color: "info" },
  offer_accepted: { label: "Offer Accepted", color: "success" },
  in_recovery: { label: "In Recovery", color: "info" },
  sold: { label: "Sold", color: "success" },
  withdrawn: { label: "Withdrawn", color: "neutral" },
  rejected: { label: "Rejected", color: "error" },
};

export const RECOVERY_STATUSES: Record<string, { label: string; color: string }> = {
  requested: { label: "Requested", color: "pending" },
  screening: { label: "Screening", color: "info" },
  sample_scheduled: { label: "Sample Scheduled", color: "info" },
  assessment_recorded: { label: "Assessed", color: "info" },
  route_proposed: { label: "Route Proposed", color: "info" },
  quote_issued: { label: "Quote Issued", color: "pending" },
  seller_approved: { label: "Seller Approved", color: "success" },
  buyer_committed: { label: "Buyer Committed", color: "success" },
  pickup_scheduled: { label: "Pickup Scheduled", color: "info" },
  received: { label: "Received", color: "info" },
  processing: { label: "Processing", color: "info" },
  quality_check: { label: "Quality Check", color: "pending" },
  dispatch: { label: "Dispatch", color: "info" },
  buyer_acceptance: { label: "Buyer Acceptance", color: "pending" },
  settlement: { label: "Settlement", color: "success" },
  closed: { label: "Closed", color: "success" },
  declined: { label: "Declined", color: "error" },
  cancelled: { label: "Cancelled", color: "neutral" },
  on_hold: { label: "On Hold", color: "pending" },
  reassessment_required: { label: "Reassessment Required", color: "error" },
  disputed: { label: "Disputed", color: "error" },
};

// Re-export formatting helpers so pages can import from either types or utils
export { humanise, categoryIcon } from "./utils";
