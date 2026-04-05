const API_BASE = "/api/v1";
const API_ACCESS_TOKEN = import.meta.env.VITE_API_ACCESS_TOKEN?.trim() ?? "";
const API_TIMEOUT_MS = 15000;

function withApiAuth(headers?: HeadersInit): HeadersInit {
  if (!API_ACCESS_TOKEN) {
    return headers ?? {};
  }
  return {
    ...(headers ?? {}),
    "X-API-Key": API_ACCESS_TOKEN,
  };
}
const SETTINGS_API_BASE = "/api/settings";

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

export interface EmailDraft {
  sequence_number: number;
  email_type: string;
  subject: string;
  body_text: string;
  suggested_send_day: number;
  personalization_points?: string[];
  cultural_adaptations?: string[];
  send_status?: string;
  sent_at?: string;
  sent_to?: string;
}

export interface EmailReviewSummary {
  status: string;
  score: number;
  issues: string[];
  suggestions: string[];
  min_score_required: number;
  max_blocking_issues: number;
  blocking_issue_count: number;
  locale: string;
}

export interface EmailManualReview {
  decision: string;
  notes?: string;
  updated_at?: string;
}

export interface EmailSequence {
  lead: Record<string, unknown>;
  locale: string;
  emails: EmailDraft[];
  template_profile: Record<string, unknown>;
  template_plan: Record<string, unknown>;
  validation_summary?: {
    passed?: boolean;
    status?: string;
    issues?: string[];
    suggestions?: string[];
  };
  review_summary: EmailReviewSummary;
  auto_send_eligible: boolean;
  generation_mode?: string;
  template_reused?: boolean;
  template_group?: string;
  template_id?: string;
  template_usage_index?: number;
  template_assigned_count?: number;
  template_remaining_capacity?: number;
  template_max_send_count?: number;
  template_performance?: {
    sent_count?: number;
    replied_count?: number;
    reply_rate?: number;
    status?: string;
    optimization_needed?: boolean;
    recommended_action?: string;
    reason?: string;
  };
  manual_review?: EmailManualReview;
  reply_detection?: {
    checked_at?: string;
    reply_count?: number;
    replies?: Array<Record<string, string>>;
  };
}

export interface HuntResult {
  hunt_id: string;
  status: string;
  insight: Record<string, unknown> | null;
  leads: Record<string, unknown>[];
  email_sequences: EmailSequence[];
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

export interface EmailSequenceDecisionRequest {
  decision: "approved" | "rejected";
  notes?: string;
}

export interface EmailSequenceDecisionResponse {
  hunt_id: string;
  sequence_index: number;
  decision: string;
  auto_send_eligible: boolean;
  manual_review: EmailManualReview;
}

export interface SmtpTestResponse {
  status: string;
  message: string;
  host: string;
  username: string;
}

export interface ImapTestResponse {
  status: string;
  message: string;
  host: string;
  username: string;
}

export interface SettingsApiResponse {
  settings: Record<string, string>;
  is_configured: boolean;
}

export interface FeishuTestResponse {
  status: string;
  message: string;
  webhook_url: string;
}

export interface SendEmailDraftRequest {
  sequence_number: number;
}

export interface SendEmailDraftResponse {
  hunt_id: string;
  sequence_index: number;
  sequence_number: number;
  sent_to: string;
  subject: string;
  status: string;
}

export interface DetectReplyResponse {
  hunt_id: string;
  sequence_index: number;
  reply_count: number;
  replies: Array<Record<string, string>>;
}

export interface AutomationJob {
  job_id: string;
  status: string;
  created_at: string;
  updated_at: string;
  started_at: string;
  finished_at: string;
  claimed_by: string;
  attempt_count: number;
  last_error: string;
  last_hunt_id: string;
  progress_stage: string;
  progress_message: string;
  template_seed_status: string;
  template_seed_source: string;
  website_url: string;
  description: string;
  product_keywords: string[];
  target_regions: string[];
  target_lead_count: number;
  enable_email_craft: boolean;
  hunt_status: string;
  hunt_stage: string;
  hunt_error: string;
  leads_count: number;
}

export interface AutomationStatus {
  hunt_jobs: {
    queued: number;
    running: number;
    failed: number;
  };
  hunts: {
    running: number;
    pending: number;
    running_details: Array<{
      hunt_id: string;
      website_url: string;
      current_stage: string;
      leads_count: number;
      email_sequences_count: number;
    }>;
  };
  email_queue: {
    pending: number;
    sent: number;
    failed: number;
    cancelled: number;
    active_campaigns: number;
    draft_campaigns: number;
    active_sequences: number;
    replied_sequences: number;
  };
  features: {
    email_auto_send_enabled: boolean;
    email_reply_detection_enabled: boolean;
    automation_summary_enabled: boolean;
    automation_alerts_enabled: boolean;
  };
  workers: {
    consumer?: {
      enabled?: boolean;
      running?: boolean;
      worker_id?: string;
      active_job_id?: string;
      last_claimed_job_id?: string;
      last_completed_job_id?: string;
      last_error?: string;
      last_poll_at?: string;
      last_activity_at?: string;
    };
  };
}

export interface AutomationMetrics {
  window_hours: number;
  hunt_jobs: {
    completed: number;
    failed: number;
    queued: number;
    running: number;
    retrying: number;
  };
  hunts: {
    created: number;
    completed: number;
    failed: number;
    new_leads: number;
    generated_email_sequences: number;
  };
  emails: {
    queued: number;
    sent: number;
    failed: number;
    replied: number;
    active_campaigns: number;
    draft_campaigns: number;
    active_sequences: number;
    replied_sequences: number;
  };
  recent_failures: Array<{
    sequence_id?: string;
    lead_email?: string;
    subject?: string;
    failure_reason?: string;
  }>;
  recent_sent_messages: Array<{
    id: string;
    subject: string;
    sent_at: string;
    lead_email: string;
    lead_name: string;
    hunt_id: string;
    campaign_id: string;
  }>;
  recent_reply_events: Array<{
    id: string;
    from_email: string;
    subject: string;
    snippet: string;
    received_at: string;
    lead_name: string;
    hunt_id: string;
    campaign_id: string;
  }>;
  top_failure_reasons: Array<{
    failure_reason: string;
    count: number;
  }>;
  recent_completed_hunts: Array<{
    hunt_id: string;
    website_url: string;
    lead_count: number;
    email_sequence_count: number;
    status: string;
  }>;
  recent_failed_hunts: Array<{
    hunt_id: string;
    website_url: string;
    current_stage: string;
    error: string;
    retry_status: string;
    retry_attempts: number;
  }>;
}

async function requestSettings<T>(path: string, options?: RequestInit): Promise<T> {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), API_TIMEOUT_MS);
  let res: Response;
  try {
    res = await fetch(`${SETTINGS_API_BASE}${path}`, {
      headers: { "Content-Type": "application/json" },
      ...options,
      signal: controller.signal,
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new Error(`Request timed out after ${API_TIMEOUT_MS / 1000}s`);
    }
    throw error;
  } finally {
    window.clearTimeout(timeout);
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || res.statusText);
  }
  if (res.status === 204) {
    return undefined as T;
  }
  return res.json();
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), API_TIMEOUT_MS);
  let res: Response;
  try {
    res = await fetch(`${API_BASE}${path}`, {
      headers: withApiAuth({ "Content-Type": "application/json" }),
      ...options,
      signal: controller.signal,
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new Error(`Request timed out after ${API_TIMEOUT_MS / 1000}s`);
    }
    throw error;
  } finally {
    window.clearTimeout(timeout);
  }
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

  createAutomationJob: (data: HuntRequest) =>
    request<AutomationJob>("/automation/jobs", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  listAutomationJobs: () =>
    request<AutomationJob[]>("/automation/jobs"),

  getAutomationJob: (jobId: string) =>
    request<AutomationJob>(`/automation/jobs/${jobId}`),

  streamAutomationJob: (jobId: string) => {
    const suffix = API_ACCESS_TOKEN ? `?api_key=${encodeURIComponent(API_ACCESS_TOKEN)}` : "";
    const url = `${API_BASE}/automation/jobs/${jobId}/stream${suffix}`;
    return new EventSource(url);
  },

  getAutomationJobByHunt: (huntId: string) =>
    request<AutomationJob>(`/automation/jobs/by-hunt/${huntId}`),

  createAutomationJobFromHunt: (huntId: string, data: ResumeRequest) =>
    request<AutomationJob>(`/automation/jobs/from-hunt/${huntId}`, {
      method: "POST",
      body: JSON.stringify(data),
    }),

  cancelAutomationJob: (jobId: string) =>
    request<AutomationJob>(`/automation/jobs/${jobId}/cancel`, {
      method: "POST",
    }),

  retryAutomationJob: (jobId: string) =>
    request<AutomationJob>(`/automation/jobs/${jobId}/retry`, {
      method: "POST",
    }),

  getAutomationStatus: () =>
    request<AutomationStatus>("/automation/status"),

  getAutomationMetrics: (hours = 24) =>
    request<AutomationMetrics>(`/automation/metrics?hours=${hours}`),

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

  decideEmailSequence: (huntId: string, sequenceIndex: number, data: EmailSequenceDecisionRequest) =>
    request<EmailSequenceDecisionResponse>(`/hunts/${huntId}/email-sequences/${sequenceIndex}/decision`, {
      method: "POST",
      body: JSON.stringify(data),
    }),

  sendEmailDraft: (huntId: string, sequenceIndex: number, data: SendEmailDraftRequest) =>
    request<SendEmailDraftResponse>(`/hunts/${huntId}/email-sequences/${sequenceIndex}/send`, {
      method: "POST",
      body: JSON.stringify(data),
    }),

  testEmailSettings: () =>
    requestSettings<SmtpTestResponse>("/email/test", {
      method: "POST",
    }),

  getSettings: () =>
    requestSettings<SettingsApiResponse>(""),

  saveSettings: (payload: Record<string, string>) =>
    requestSettings<void>("", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  testImapSettings: () =>
    requestSettings<ImapTestResponse>("/email/imap-test", {
      method: "POST",
    }),

  testFeishuWebhook: () =>
    requestSettings<FeishuTestResponse>("/automation/feishu-test", {
      method: "POST",
    }),

  detectReplies: (huntId: string, sequenceIndex: number) =>
    request<DetectReplyResponse>(`/hunts/${huntId}/email-sequences/${sequenceIndex}/detect-replies`, {
      method: "POST",
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
