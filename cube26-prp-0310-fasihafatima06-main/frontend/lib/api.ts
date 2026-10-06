import { InspectionResponse, Product, Rule, TestScenario, AgentStatus, AgentEvent } from "./types";

const getApiBase = () => {
  if (typeof window !== "undefined" && process.env.NEXT_PUBLIC_API_URL) {
    return `${process.env.NEXT_PUBLIC_API_URL.replace(/\/$/, "")}/api`;
  }
  if (process.env.NEXT_PUBLIC_API_URL) {
    return `${process.env.NEXT_PUBLIC_API_URL.replace(/\/$/, "")}/api`;
  }
  return "/api";
};

const API_BASE = getApiBase();

export async function fetchProducts(): Promise<Product[]> {
  const res = await fetch(`${API_BASE}/products`);
  if (!res.ok) throw new Error("Failed to fetch products");
  return res.json();
}

export async function createProduct(payload: any): Promise<Product> {
  const res = await fetch(`${API_BASE}/products`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Failed to create product");
  }
  return res.json();
}

export async function deleteProduct(id: string): Promise<void> {
  const res = await fetch(`${API_BASE}/products/${id}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error("Failed to delete product");
}

export async function fetchProduct(id: string): Promise<Product> {
  const res = await fetch(`${API_BASE}/products/${id}`);
  if (!res.ok) throw new Error(`Failed to fetch product ${id}`);
  return res.json();
}

export async function fetchRules(): Promise<Rule[]> {
  const res = await fetch(`${API_BASE}/rules`);
  if (!res.ok) throw new Error("Failed to fetch rules");
  return res.json();
}

export async function fetchTestScenarios(): Promise<TestScenario[]> {
  const res = await fetch(`${API_BASE}/scenarios`);
  if (!res.ok) throw new Error("Failed to fetch scenarios");
  return res.json();
}

export async function fetchInspections(status?: string, productId?: string): Promise<InspectionResponse[]> {
  const params = new URLSearchParams();
  if (status) params.append("status", status);
  if (productId) params.append("product_id", productId);
  const res = await fetch(`${API_BASE}/inspections?${params.toString()}`);
  if (!res.ok) throw new Error("Failed to fetch inspections");
  return res.json();
}

export async function fetchInspection(id: string): Promise<InspectionResponse> {
  const res = await fetch(`${API_BASE}/inspections/${id}`);
  if (!res.ok) throw new Error(`Failed to fetch inspection ${id}`);
  return res.json();
}

export async function createInspection(formData: FormData): Promise<InspectionResponse> {
  const res = await fetch(`${API_BASE}/inspections`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Failed to create inspection");
  }
  return res.json();
}

export async function submitAdditionalEvidence(id: string, formData: FormData): Promise<InspectionResponse> {
  const res = await fetch(`${API_BASE}/inspections/${id}/additional-evidence`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) throw new Error("Failed to submit additional evidence");
  return res.json();
}

export async function submitInspectionFeedback(id: string, payload: {
  check_id?: string;
  check_name?: string;
  corrected_status: string;
  feedback_category?: string;
  operator_notes: string;
  operator_name?: string;
}): Promise<InspectionResponse> {
  const res = await fetch(`${API_BASE}/inspections/${id}/feedback`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Failed to submit operator feedback");
  return res.json();
}

export async function fetchAgentStatus(): Promise<AgentStatus> {
  const res = await fetch(`${API_BASE}/agent/status`);
  if (!res.ok) throw new Error("Failed to fetch agent status");
  return res.json();
}

export async function fetchAgentActivity(): Promise<AgentEvent[]> {
  const res = await fetch(`${API_BASE}/agent/activity`);
  if (!res.ok) throw new Error("Failed to fetch agent activity");
  return res.json();
}

export async function fetchInspectionEvidence(id: string): Promise<any> {
  const res = await fetch(`${API_BASE}/inspections/${id}/evidence`);
  if (!res.ok) throw new Error("Failed to fetch inspection evidence");
  return res.json();
}
