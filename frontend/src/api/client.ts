const API_BASE = "/api/v1";
const API_ACCESS_TOKEN = import.meta.env.VITE_API_ACCESS_TOKEN?.trim() ?? "";

function withApiAuth(headers?: HeadersInit): HeadersInit {
  if (!API_ACCESS_TOKEN) {
    return headers ?? {};
  }
  return {
    ...(headers ?? {}),
    "X-API-Key": API_ACCESS_TOKEN,
  };
}

export interface HuntRequest {
  website_url: string;
  description: string;
  product_keywords: string[];
  target_customer_profile: string;
  uploaded_file_ids: string[];
  target_regions: string[];
  target_lead_count: number;
  max_rounds: number;
  min_new_leads_threshold: number;
  enable_email_craft: boolean;
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
  email_campaign_summary?: Record<string, unknown> | null;
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
  min_new_leads_threshold: number;
  enable_email_craft: boolean;
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

export interface EmailCampaign {
  id: string;
  hunt_id: string;
  email_account_id: string;
  name: string;
  status: string;
  language_mode: string;
  default_language: string;
  fallback_language: string;
  tone: string;
  step1_delay_days: number;
  step2_delay_days: number;
  step3_delay_days: number;
  min_fit_score: number;
  min_contactability_score: number;
  created_at: string;
  updated_at: string;
}

export interface EmailSequenceSummary {
  id: string;
  campaign_id: string;
  hunt_id: string;
  lead_key: string;
  lead_email: string;
  lead_name: string;
  decision_maker_name: string;
  decision_maker_title: string;
  locale: string;
  status: string;
  current_step: number;
  stop_reason: string;
  replied_at: string;
  last_sent_at: string;
  next_scheduled_at: string;
  created_at: string;
  updated_at: string;
}

export interface EmailCampaignListItem {
  campaign: EmailCampaign;
  sequence_count: number;
  sent_count: number;
  pending_count: number;
  failed_count: number;
  sequences: EmailSequenceSummary[];
}

export interface EmailMessage {
  id: string;
  sequence_id: string;
  step_number: number;
  goal: string;
  locale: string;
  subject: string;
  body_text: string;
  status: string;
  scheduled_at: string;
  sent_at: string;
  provider_message_id: string;
  thread_key: string;
  failure_reason: string;
  created_at: string;
  updated_at: string;
}

export interface EmailSequenceDetail {
  sequence: EmailSequenceSummary;
  messages: EmailMessage[];
  reply_events?: Array<{
    id: string;
    sequence_id: string;
    message_id: string;
    from_email: string;
    subject: string;
    snippet: string;
    received_at: string;
    raw_ref: string;
    created_at: string;
  }>;
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: withApiAuth({ "Content-Type": "application/json" }),
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
    const res = await fetch(`${API_BASE}/upload`, {
      method: "POST",
      body: formData,
      headers: withApiAuth(),
    });
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

  createEmailCampaign: (huntId: string, name: string) =>
    request<{ campaign_id: string; status: string; sequence_count: number }>(`/hunts/${huntId}/email-campaigns`, {
      method: "POST",
      body: JSON.stringify({ name }),
    }),

  listEmailCampaigns: (huntId: string) =>
    request<EmailCampaignListItem[]>(`/hunts/${huntId}/email-campaigns`),

  startEmailCampaign: (campaignId: string) =>
    request<{ campaign_id: string; status: string }>(`/email-campaigns/${campaignId}/start`, {
      method: "POST",
    }),

  pauseEmailCampaign: (campaignId: string) =>
    request<{ campaign_id: string; status: string }>(`/email-campaigns/${campaignId}/pause`, {
      method: "POST",
    }),

  runEmailReplyCheck: () =>
    request<{ checked: number; matched: number; skipped: number; ignored: number }>(`/email-replies/check`, {
      method: "POST",
    }),

  getEmailSequence: (sequenceId: string) =>
    request<EmailSequenceDetail>(`/email-sequences/${sequenceId}`),

  streamHunt: (huntId: string) => {
    const suffix = API_ACCESS_TOKEN ? `?api_key=${encodeURIComponent(API_ACCESS_TOKEN)}` : "";
    const url = `${API_BASE}/hunts/${huntId}/stream${suffix}`;
    return new EventSource(url);
  },
};
