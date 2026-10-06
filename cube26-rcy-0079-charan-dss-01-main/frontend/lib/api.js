const getApiBase = () => {
  const raw =
    process.env.NEXT_PUBLIC_API_URL ||
    "https://rcy-recovery-backend.onrender.com/api/v1";
  const trimmed = raw.replace(/\/+$/, "");
  return trimmed.endsWith("/api/v1") ? trimmed : `${trimmed}/api/v1`;
};

const API_BASE = getApiBase();

export async function fetchApi(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  try {
    const res = await fetch(url, {
      ...options,
      headers: {
        ...(options.headers || {}),
      },
    });
    if (!res.ok) {
      const errText = await res.text();
      let errJson;
      try {
        errJson = JSON.parse(errText);
      } catch (e) {
        errJson = { detail: errText };
      }
      throw new Error(errJson.detail || `Request failed with status ${res.status}`);
    }
    return await res.json();
  } catch (err) {
    console.error(`API Error on ${url}:`, err);
    throw err;
  }
}

export const api = {
  // Companies
  getCompanies: () => fetchApi("/companies"),
  createCompany: (name) =>
    fetchApi("/companies", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name }),
    }),

  // Dashboard
  getDashboardSummary: (companyId = "org_demo_alpha") =>
    fetchApi(`/dashboard/summary?company_id=${companyId}`),

  // Charges
  getCharges: (companyId = "org_demo_alpha", params = {}) => {
    const clean = { company_id: companyId };
    for (const [k, v] of Object.entries(params)) {
      if (v !== undefined && v !== null && v !== "" && v !== "undefined" && v !== "null") {
        clean[k] = v;
      }
    }
    const query = new URLSearchParams(clean).toString();
    return fetchApi(`/charges?${query}`);
  },
  getChargeDetail: (chargeId, companyId = "org_demo_alpha") =>
    fetchApi(`/charges/${chargeId}?company_id=${companyId}`),
  createManualCharge: (data) =>
    fetchApi("/charges", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    }),
  batchInvestigate: (companyId = "org_demo_alpha") =>
    fetchApi(`/charges/batch/investigate?company_id=${companyId}`, { method: "POST" }),

  // Evidence
  getEvidenceList: (companyId = "org_demo_alpha", params = {}) => {
    const clean = { company_id: companyId };
    for (const [k, v] of Object.entries(params)) {
      if (v !== undefined && v !== null && v !== "" && v !== "undefined" && v !== "null") {
        clean[k] = v;
      }
    }
    const query = new URLSearchParams(clean).toString();
    return fetchApi(`/evidence?${query}`);
  },
  getEvidenceDetail: (evidenceId, companyId = "org_demo_alpha") =>
    fetchApi(`/evidence/${evidenceId}?company_id=${companyId}`),
  getEvidenceGraph: (chargeId, companyId = "org_demo_alpha") =>
    fetchApi(`/evidence/graph/${chargeId}?company_id=${companyId}`),
  createManualEvidence: (data) =>
    fetchApi("/evidence", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    }),

  // Investigations
  getInvestigation: (chargeId, companyId = "org_demo_alpha") =>
    fetchApi(`/investigations/${chargeId}?company_id=${companyId}`),
  runInvestigation: (chargeId, companyId = "org_demo_alpha") =>
    fetchApi(`/investigations/${chargeId}/run?company_id=${companyId}`, { method: "POST" }),

  // Recovery & Claims
  getRecoveryOpportunities: (companyId = "org_demo_alpha") =>
    fetchApi(`/recovery/opportunities?company_id=${companyId}`),
  getClaims: (companyId = "org_demo_alpha") =>
    fetchApi(`/claims?company_id=${companyId}`),
  createClaim: (companyId, chargeId) =>
    fetchApi("/claims", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ company_id: companyId, charge_id: chargeId }),
    }),
  updateClaimStatus: (claimId, status, companyId = "org_demo_alpha") =>
    fetchApi(`/claims/${claimId}/status?status=${status}&company_id=${companyId}`, {
      method: "PATCH",
    }),

  // Files
  previewUpload: (formData) =>
    fetchApi("/files/upload-preview", {
      method: "POST",
      body: formData,
    }),
  importFile: (formData) =>
    fetchApi("/files/import", {
      method: "POST",
      body: formData,
    }),
  getUploadedFiles: (companyId = "org_demo_alpha") =>
    fetchApi(`/files?company_id=${companyId}`),
};
