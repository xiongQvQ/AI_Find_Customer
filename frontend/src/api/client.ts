const API_BASE = "/api/v1";

export interface HuntRequest {
  website_url: string;
  description: string;
  product_keywords: string[];
  target_customer_profile: string;
  uploaded_file_ids: string[];
  target_regions: string[];
  target_lead_count: number;
  max_rounds: number;
  enable_email_craft: boolean;
  email_template_examples: string[];
  email_template_notes: string;
}

export interface UploadedFile {
  original_name: string;
  file_id: string;
}

export interface HuntResponse {
  hunt_id: string;
  status: string;
}

export interface HuntStatus {
  hunt_id: string;
  status: string;
  current_stage: string | null;
  hunt_round: number;
  leads_count: number;
  email_sequences_count: number;
  error: string | null;
}

export interface HuntResult {
  hunt_id: string;
  status: string;
  insight: Record<string, unknown> | null;
  leads: Record<string, unknown>[];
  email_sequences: Record<string, unknown>[];
  used_keywords: string[];
  hunt_round: number;
  round_feedback: Record<string, unknown> | null;
  keyword_search_stats: Record<string, unknown>;
  search_result_count: number;
}

export interface LLMAgentCost {
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  cost_usd: number;
  call_count: number;
  models: Record<string, { prompt_tokens: number; completion_tokens: number; total_tokens: number; cost_usd: number; call_count: number }>;
}

export interface CostSummary {
  total_cost_usd: number;
  total_tokens: number;
  total_llm_calls: number;
  rounds_completed: number;
  avg_cost_per_round_usd: number;
  by_agent: Record<string, LLMAgentCost>;
  by_round: Record<string, { cost_usd: number; total_tokens: number }>;
  search_api: Record<string, { call_count: number; result_count: number }>;
}

export interface HuntCost {
  hunt_id: string;
  status: string;
  cost_summary: CostSummary;
}

export interface ResumeRequest {
  target_lead_count: number;
  max_rounds: number;
  enable_email_craft: boolean;
  email_template_examples?: string[];
  email_template_notes?: string;
}

export interface HuntListItem {
  hunt_id: string;
  status: string;
  leads_count: number;
  created_at: string;
  website_url: string;
  product_keywords: string[];
  target_customer_profile: string;
  target_regions: string[];
  hunt_round: number;
  email_sequences_count: number;
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || res.statusText);
  }
  return res.json();
}

export const api = {
  createHunt: (data: HuntRequest) =>
    request<HuntResponse>("/hunts", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  getHuntStatus: (huntId: string) =>
    request<HuntStatus>(`/hunts/${huntId}/status`),

  getHuntResult: (huntId: string) =>
    request<HuntResult>(`/hunts/${huntId}/result`),

  listHunts: () => request<HuntListItem[]>("/hunts"),

  uploadFiles: async (files: File[]): Promise<UploadedFile[]> => {
    const formData = new FormData();
    files.forEach((f) => formData.append("files", f));
    const res = await fetch(`${API_BASE}/upload`, { method: "POST", body: formData });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || res.statusText);
    }
    const data = await res.json();
    return data.uploaded as UploadedFile[];
  },

  resumeHunt: (huntId: string, data: ResumeRequest) =>
    request<HuntResponse>(`/hunts/${huntId}/resume`, {
      method: "POST",
      body: JSON.stringify(data),
    }),

  getHuntCost: (huntId: string) =>
    request<HuntCost>(`/hunts/${huntId}/cost`),

  streamHunt: (huntId: string) => {
    const url = `${API_BASE}/hunts/${huntId}/stream`;
    return new EventSource(url);
  },
};
