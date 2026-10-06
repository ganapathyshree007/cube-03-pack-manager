export type CheckStatus = "PASS" | "FAIL" | "UNCERTAIN";

export interface BoundingBox {
  type: string;
  x: number;
  y: number;
  width: number;
  height: number;
  label?: string;
  confidence?: number;
  color?: string;
}

export interface EvidenceData {
  image_id?: string;
  bounding_boxes: BoundingBox[];
  detected_features: string[];
}

export interface CheckResult {
  id: string;
  rule_id: string;
  name: string;
  category: string;
  status: CheckStatus;
  confidence: number;
  reason: string;
  recommended_action?: string;
  visually_verifiable: boolean;
  evidence?: EvidenceData;
}

export interface AgentAction {
  type: "PASS" | "CORRECT_AND_RESCAN" | "REQUEST_ADDITIONAL_PHOTO" | "HUMAN_REVIEW";
  message: string;
  requires_rescan: boolean;
  requires_human_review: boolean;
}

export interface InspectionImage {
  id: string;
  inspection_id: string;
  file_path: string;
  view_angle: string;
  width: number;
  height: number;
  quality_score: number;
  is_blurry: boolean;
  has_glare: boolean;
}

export interface AgentEvent {
  id: string;
  inspection_id: string;
  timestamp: string;
  agent_name: string;
  stage: string;
  message: string;
  status: "INFO" | "SUCCESS" | "WARNING" | "ERROR";
  details?: Record<string, any>;
}

export interface InspectionResponse {
  inspection_id: string;
  unit_id: string;
  product_id: string;
  product_name?: string;
  work_order_id?: string;
  overall_status: CheckStatus;
  mode: string;
  engine_provider: string;
  operator_name: string;
  cost_per_check?: number;
  defect_fee_amount?: number;
  recovery_disputable?: boolean;
  
  // Continuous Learning / Operator Feedback Overrides
  is_overridden?: boolean;
  corrected_by_operator?: boolean;
  operator_feedback_notes?: string;

  created_at: string;
  checks: CheckResult[];
  agent_action: AgentAction;
  images: InspectionImage[];
  agent_events: AgentEvent[];
}

export interface Rule {
  id: string;
  product_id: string;
  name: string;
  category: string;
  visually_verifiable: boolean;
  evaluation_type: string;
  description?: string;
  required_views: string;
}

export interface Product {
  id: string;
  name: string;
  asin: string;
  sku: string;
  category: string;
  description?: string;
  requirements: Rule[];
}

export interface TestScenario {
  id: string;
  name: string;
  product_id: string;
  expected_status: CheckStatus;
  description: string;
  image_preview: string;
}

export interface AgentStatus {
  agent_name: string;
  agent_status: string;
  vision_engine: string;
  is_ai_configured: boolean;
  active_subagents: { name: string; role: string; status: string }[];
  statistics: {
    total_inspections: number;
    passed: number;
    failed: number;
    uncertain: number;
  };
}
