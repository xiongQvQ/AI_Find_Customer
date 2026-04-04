import { useState, useEffect, useRef } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Search,
  Cpu,
  Mail,
  CheckCircle2,
  Loader2,
  Eye,
  EyeOff,
  Save,
  RefreshCw,
  ChevronDown,
  Check,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { api } from "@/api/client";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";

const API_BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000";  // 生产环境: VITE_API_URL=https://license.b2binsights.io

// ── Provider definitions ──────────────────────────────────────────────────────

type Provider = {
  id: string;
  label: string;
  apiKeyField: string;
  apiKeyPlaceholder: string;
  defaultModels: string[];
  reasoningModels: string[];
  litellmPrefix?: string;
};

const PROVIDERS: Provider[] = [
  {
    id: "openai",
    label: "OpenAI",
    apiKeyField: "openai_api_key",
    apiKeyPlaceholder: "sk-…",
    defaultModels: ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"],
    reasoningModels: ["gpt-4o", "o1-mini", "o3-mini", "o1"],
  },
  {
    id: "anthropic",
    label: "Anthropic",
    apiKeyField: "anthropic_api_key",
    apiKeyPlaceholder: "sk-ant-…",
    defaultModels: [
      "anthropic/claude-3-5-haiku-20241022",
      "anthropic/claude-3-haiku-20240307",
    ],
    reasoningModels: [
      "anthropic/claude-3-5-sonnet-20241022",
      "anthropic/claude-3-7-sonnet-20250219",
      "anthropic/claude-opus-4-5",
    ],
  },
  {
    id: "openrouter",
    label: "OpenRouter",
    apiKeyField: "openrouter_api_key",
    apiKeyPlaceholder: "sk-or-…",
    defaultModels: [
      "openrouter/google/gemini-flash-1.5",
      "openrouter/mistralai/mistral-7b-instruct",
      "openrouter/meta-llama/llama-3.1-8b-instruct",
    ],
    reasoningModels: [
      "openrouter/google/gemini-pro-1.5",
      "openrouter/deepseek/deepseek-r1",
      "openrouter/openai/gpt-4o",
    ],
  },
  {
    id: "groq",
    label: "Groq",
    apiKeyField: "groq_api_key",
    apiKeyPlaceholder: "gsk_…",
    defaultModels: [
      "groq/llama-3.1-8b-instant",
      "groq/llama-3.3-70b-versatile",
      "groq/gemma2-9b-it",
    ],
    reasoningModels: [
      "groq/llama-3.3-70b-versatile",
      "groq/deepseek-r1-distill-llama-70b",
    ],
  },
  {
    id: "glm",
    label: "GLM / Z.AI",
    apiKeyField: "zai_api_key",
    apiKeyPlaceholder: "",
    defaultModels: ["openai/glm-4-flash", "openai/glm-4-air"],
    reasoningModels: ["openai/glm-4", "openai/glm-z1-airx"],
  },
  {
    id: "kimi",
    label: "Kimi (Moonshot)",
    apiKeyField: "moonshot_api_key",
    apiKeyPlaceholder: "",
    defaultModels: ["openai/moonshot-v1-8k", "openai/moonshot-v1-32k"],
    reasoningModels: ["openai/moonshot-v1-128k", "openai/kimi-k1-5"],
  },
  {
    id: "minimax",
    label: "MiniMax",
    apiKeyField: "minimax_api_key",
    apiKeyPlaceholder: "",
    defaultModels: ["openai/MiniMax-Text-01"],
    reasoningModels: ["openai/MiniMax-Text-01"],
  },
];

// ── API helpers ───────────────────────────────────────────────────────────────

async function fetchSettings() {
  const res = await fetch(`${API_BASE}/api/settings`);
  if (!res.ok) throw new Error("加载设置失败");
  return res.json();
}

async function saveSettings(payload: Record<string, string>) {
  const res = await fetch(`${API_BASE}/api/settings`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("保存设置失败");
}

// ── Helpers to detect provider from a model string ───────────────────────────

function detectProvider(model: string): string {
  if (!model) return "openai";
  if (model.startsWith("anthropic/")) return "anthropic";
  if (model.startsWith("openrouter/")) return "openrouter";
  if (model.startsWith("groq/")) return "groq";
  if (model.startsWith("openai/glm") || model.startsWith("openai/glm")) return "glm";
  if (model.startsWith("openai/moonshot") || model.startsWith("openai/kimi")) return "kimi";
  if (model.startsWith("openai/MiniMax")) return "minimax";
  return "openai";
}

// ── Sub-components ────────────────────────────────────────────────────────────

function SecretInput({
  id,
  value,
  onChange,
  placeholder,
}: {
  id: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
}) {
  const [show, setShow] = useState(false);
  return (
    <div className="relative">
      <Input
        id={id}
        type={show ? "text" : "password"}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="pr-10 font-mono text-sm"
      />
      <button
        type="button"
        onClick={() => setShow((s) => !s)}
        className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
      >
        {show ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
      </button>
    </div>
  );
}

// Combobox: dropdown list of presets + free-text input
function ModelCombobox({
  id,
  value,
  onChange,
  options,
  placeholder,
}: {
  id: string;
  value: string;
  onChange: (v: string) => void;
  options: string[];
  placeholder?: string;
}) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handler(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const isCustom = value && !options.includes(value);

  return (
    <div ref={ref} className="relative">
      <div className="flex gap-2">
        <div className="relative flex-1">
          <Input
            id={id}
            value={value}
            onChange={(e) => onChange(e.target.value)}
            placeholder={placeholder ?? "选择或输入模型名称…"}
            className="font-mono text-sm pr-8"
            onFocus={() => setOpen(true)}
          />
          <button
            type="button"
            onClick={() => setOpen((o) => !o)}
            className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
          >
            <ChevronDown className="h-4 w-4" />
          </button>
        </div>
      </div>

      {open && (
        <div className="absolute z-50 mt-1 w-full rounded-md border bg-popover shadow-lg">
          <div className="max-h-52 overflow-y-auto py-1">
            {options.map((opt) => (
              <button
                key={opt}
                type="button"
                onClick={() => { onChange(opt); setOpen(false); }}
                className="flex w-full items-center gap-2 px-3 py-2 text-sm hover:bg-accent hover:text-accent-foreground font-mono"
              >
                {value === opt && <Check className="h-3.5 w-3.5 shrink-0 text-primary" />}
                <span className={value === opt ? "ml-0" : "ml-5"}>{opt}</span>
              </button>
            ))}
            <div className="px-3 py-1.5 border-t">
              <p className="text-xs text-muted-foreground">
                或直接在上方输入自定义模型名称
              </p>
            </div>
          </div>
        </div>
      )}
      {isCustom && (
        <p className="text-xs text-muted-foreground mt-1">
          ✎ 自定义模型：<span className="font-mono">{value}</span>
        </p>
      )}
    </div>
  );
}

// ── LLM Provider Panel ────────────────────────────────────────────────────────

function LLMProviderPanel({
  values,
  onChange,
}: {
  values: Record<string, string>;
  onChange: (key: string, value: string) => void;
}) {
  const currentDefaultModel = values.llm_model ?? "";
  const currentReasoningModel = values.reasoning_model ?? "";

  // Derive the active provider from saved model values (default to openai)
  const [providerId, setProviderId] = useState<string>(() =>
    detectProvider(currentDefaultModel || currentReasoningModel)
  );

  const provider = PROVIDERS.find((p) => p.id === providerId) ?? PROVIDERS[0];

  // When provider changes, update API key field visibility and reset models to first preset
  const handleProviderChange = (newId: string) => {
    setProviderId(newId);
    const p = PROVIDERS.find((pr) => pr.id === newId)!;
    // Only reset models if the current values don't belong to the new provider
    if (!currentDefaultModel || detectProvider(currentDefaultModel) !== newId) {
      onChange("llm_model", p.defaultModels[0] ?? "");
    }
    if (!currentReasoningModel || detectProvider(currentReasoningModel) !== newId) {
      onChange("reasoning_model", p.reasoningModels[0] ?? "");
    }
  };

  const apiKeyValue = values[provider.apiKeyField] ?? "";

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <Cpu className="h-5 w-5 text-primary" />
          <CardTitle className="text-base">AI 模型配置</CardTitle>
        </div>
        <CardDescription>
          选择 LLM 供应商，填写 API Key，并配置默认模型与推理模型。
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-5">

        {/* Provider selector */}
        <div className="space-y-1.5">
          <Label>LLM 供应商</Label>
          <div className="grid grid-cols-4 gap-2">
            {PROVIDERS.map((p) => (
              <button
                key={p.id}
                type="button"
                onClick={() => handleProviderChange(p.id)}
                className={`rounded-md border px-3 py-2 text-sm font-medium transition-colors ${
                  providerId === p.id
                    ? "border-primary bg-primary/10 text-primary"
                    : "border-border bg-background text-muted-foreground hover:border-primary/50 hover:text-foreground"
                }`}
              >
                {p.label}
              </button>
            ))}
          </div>
        </div>

        {/* API Key — only show the relevant one */}
        <div className="space-y-1.5">
          <Label htmlFor="llm-api-key">{provider.label} API Key</Label>
          <SecretInput
            id="llm-api-key"
            value={apiKeyValue}
            onChange={(v) => onChange(provider.apiKeyField, v)}
            placeholder={provider.apiKeyPlaceholder || `输入 ${provider.label} API Key`}
          />
        </div>

        <Separator />

        {/* Default / Fast model */}
        <div className="space-y-1.5">
          <Label htmlFor="llm-default-model">
            默认模型
            <span className="ml-2 text-xs font-normal text-muted-foreground">
              — 用于提取、关键词生成、邮件生成
            </span>
          </Label>
          <ModelCombobox
            id="llm-default-model"
            value={values.llm_model ?? ""}
            onChange={(v) => onChange("llm_model", v)}
            options={provider.defaultModels}
            placeholder={provider.defaultModels[0] ?? "gpt-4o-mini"}
          />
        </div>

        {/* Reasoning model */}
        <div className="space-y-1.5">
          <Label htmlFor="llm-reasoning-model">
            推理模型
            <span className="ml-2 text-xs font-normal text-muted-foreground">
              — 用于 ReAct 决策
            </span>
          </Label>
          <ModelCombobox
            id="llm-reasoning-model"
            value={values.reasoning_model ?? ""}
            onChange={(v) => onChange("reasoning_model", v)}
            options={provider.reasoningModels}
            placeholder={provider.reasoningModels[0] ?? "gpt-4o"}
          />
        </div>

        <Separator />

        <div className="space-y-1.5">
          <Label htmlFor="email-llm-model">
            邮件生成模型
            <span className="ml-2 text-xs font-normal text-muted-foreground">
              — 用于模板提取、邮件生成、改写
            </span>
          </Label>
          <ModelCombobox
            id="email-llm-model"
            value={values.email_llm_model ?? ""}
            onChange={(v) => onChange("email_llm_model", v)}
            options={provider.defaultModels}
            placeholder={provider.defaultModels[0] ?? "gpt-4o-mini"}
          />
          <p className="text-xs text-muted-foreground">
            留空时会回退到默认模型。单独配置后，邮件生成不会再和主链路共用同一个默认模型 RPM。
          </p>
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="email-reasoning-model">
            邮件推理模型
            <span className="ml-2 text-xs font-normal text-muted-foreground">
              — 用于邮件 ReAct / 校验修复闭环
            </span>
          </Label>
          <ModelCombobox
            id="email-reasoning-model"
            value={values.email_reasoning_model ?? ""}
            onChange={(v) => onChange("email_reasoning_model", v)}
            options={provider.reasoningModels}
            placeholder={provider.reasoningModels[0] ?? "gpt-4o"}
          />
          <p className="text-xs text-muted-foreground">
            留空时会回退到主推理模型。适合把邮件链路单独切到另一套模型，规避 MiniMax 共用限速。
          </p>
        </div>

      </CardContent>
    </Card>
  );
}

// ── Search / Email / Performance panels (simple field groups) ─────────────────

type FieldDef = { key: string; label: string; placeholder?: string; secret?: boolean; hint?: string };
type EmailProviderPreset = {
  id: string;
  label: string;
  smtpHost: string;
  smtpPort: string;
  imapHost: string;
  imapPort: string;
  useTls: string;
  note: string;
};

const SEARCH_FIELDS: FieldDef[] = [
  { key: "tavily_api_key", label: "Tavily API Key", placeholder: "tvly-…（多 Key 用逗号分隔）", secret: true, hint: "通用网页搜索，支持多 Key：key1,key2" },
  { key: "serper_api_key", label: "Serper API Key", placeholder: "", secret: true, hint: "Google Maps 搜索及部分网页补充查询" },
  { key: "jina_api_key", label: "Jina Reader API Key", placeholder: "", secret: true, hint: "网页读取与抓取" },
  { key: "amap_api_key", label: "Amap API Key（高德）", placeholder: "", secret: true, hint: "中国区域地图搜索" },
  { key: "baidu_api_key", label: "Baidu API Key（百度）", placeholder: "", secret: true, hint: "中国区域网页搜索" },
];

const EMAIL_FIELDS: FieldDef[] = [
  { key: "hunter_api_key", label: "Hunter.io API Key", placeholder: "", secret: true, hint: "企业邮箱发现" },
];

const EMAIL_DELIVERY_FIELDS: FieldDef[] = [
  { key: "email_from_name", label: "发件人名称", placeholder: "B2Binsights" },
  { key: "email_from_address", label: "发件邮箱", placeholder: "sales@example.com" },
  { key: "email_reply_to", label: "回复邮箱", placeholder: "sales@example.com" },
  { key: "email_smtp_host", label: "SMTP Host", placeholder: "smtp.gmail.com" },
  { key: "email_smtp_port", label: "SMTP Port", placeholder: "587" },
  { key: "email_smtp_username", label: "SMTP 用户名", placeholder: "sales@example.com" },
  { key: "email_smtp_password", label: "SMTP 授权码 / 密码", placeholder: "", secret: true },
  { key: "email_imap_host", label: "IMAP Host", placeholder: "imap.gmail.com" },
  { key: "email_imap_port", label: "IMAP Port", placeholder: "993" },
  { key: "email_imap_username", label: "IMAP 用户名", placeholder: "sales@example.com" },
  { key: "email_imap_password", label: "IMAP 授权码 / 密码", placeholder: "", secret: true },
];

const EMAIL_PROVIDER_PRESETS: EmailProviderPreset[] = [
  {
    id: "manual",
    label: "手动填写",
    smtpHost: "",
    smtpPort: "",
    imapHost: "",
    imapPort: "",
    useTls: "true",
    note: "适合自建邮箱、地区化企业邮箱，或管理员给了专用网关地址的场景。",
  },
  {
    id: "qq",
    label: "QQ 邮箱",
    smtpHost: "smtp.qq.com",
    smtpPort: "465",
    imapHost: "imap.qq.com",
    imapPort: "993",
    useTls: "true",
    note: "通常需要在 QQ 邮箱设置里开启 IMAP/SMTP，并生成授权码。",
  },
  {
    id: "exmail_qq",
    label: "腾讯企业邮箱",
    smtpHost: "smtp.exmail.qq.com",
    smtpPort: "465",
    imapHost: "imap.exmail.qq.com",
    imapPort: "993",
    useTls: "true",
    note: "适合腾讯企业邮箱常见配置；若管理员提供专用地址，请以管理员配置为准。",
  },
  {
    id: "netease_163",
    label: "网易 163 邮箱",
    smtpHost: "smtp.163.com",
    smtpPort: "465",
    imapHost: "imap.163.com",
    imapPort: "993",
    useTls: "true",
    note: "通常需要先在邮箱安全设置里开启 IMAP/SMTP，并使用客户端授权码。",
  },
  {
    id: "netease_126",
    label: "网易 126 邮箱",
    smtpHost: "smtp.126.com",
    smtpPort: "465",
    imapHost: "imap.126.com",
    imapPort: "993",
    useTls: "true",
    note: "126 邮箱常见默认配置，授权方式通常与 163 类似。",
  },
  {
    id: "netease_qiye",
    label: "网易企业邮箱",
    smtpHost: "smtp.qiye.163.com",
    smtpPort: "465",
    imapHost: "imap.qiye.163.com",
    imapPort: "993",
    useTls: "true",
    note: "网易企业邮箱可能按区域或管理员策略使用不同地址；不一致时请以管理员提供为准。",
  },
  {
    id: "aliyun_qiye",
    label: "阿里云企业邮箱",
    smtpHost: "smtp.mxhichina.com",
    smtpPort: "465",
    imapHost: "imap.mxhichina.com",
    imapPort: "993",
    useTls: "true",
    note: "阿里云企业邮箱常见默认配置；部分企业可能由管理员提供独立服务器地址。",
  },
];

const CONCURRENCY_FIELDS: FieldDef[] = [
  { key: "search_concurrency", label: "搜索并发数", placeholder: "10", hint: "搜索 API 最大并发调用数" },
  { key: "scrape_concurrency", label: "抓取并发数", placeholder: "5", hint: "Jina 抓取最大并发调用数" },
  { key: "email_llm_requests_per_minute", label: "邮件生成模型 RPM", placeholder: "0", hint: "0 表示不限；用于邮件默认模型单独限速" },
  { key: "email_reasoning_requests_per_minute", label: "邮件推理模型 RPM", placeholder: "0", hint: "0 表示不限；用于邮件 ReAct / 校验模型单独限速" },
];

function FieldGroup({
  title,
  icon,
  description,
  fields,
  values,
  onChange,
}: {
  title: string;
  icon: React.ReactNode;
  description?: string;
  fields: FieldDef[];
  values: Record<string, string>;
  onChange: (key: string, value: string) => void;
}) {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          {icon}
          <CardTitle className="text-base">{title}</CardTitle>
        </div>
        {description && <CardDescription>{description}</CardDescription>}
      </CardHeader>
      <CardContent className="space-y-4">
        {fields.map((f) => (
          <div key={f.key} className="space-y-1.5">
            <Label htmlFor={f.key}>{f.label}</Label>
            {f.secret ? (
              <SecretInput
                id={f.key}
                value={values[f.key] ?? ""}
                onChange={(v) => onChange(f.key, v)}
                placeholder={f.placeholder}
              />
            ) : (
              <Input
                id={f.key}
                value={values[f.key] ?? ""}
                onChange={(e) => onChange(f.key, e.target.value)}
                placeholder={f.placeholder}
                className="font-mono text-sm"
              />
            )}
            {f.hint && <p className="text-xs text-muted-foreground">{f.hint}</p>}
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

function EmailDeliveryPanel({
  values,
  onChange,
  onPersist,
}: {
  values: Record<string, string>;
  onChange: (key: string, value: string) => void;
  onPersist: (payload: Record<string, string>) => Promise<void>;
}) {
  const [selectedPresetId, setSelectedPresetId] = useState("manual");
  const smtpConfigured = Boolean(
    values.email_from_address &&
    values.email_smtp_host &&
    values.email_smtp_port &&
    values.email_smtp_username &&
    values.email_smtp_password
  );
  const imapConfigured = Boolean(
    values.email_imap_host &&
    values.email_imap_port &&
    values.email_imap_username &&
    values.email_imap_password
  );
  const smtpVerified = Boolean(values.email_smtp_last_test_at);
  const imapVerified = Boolean(values.email_imap_last_test_at);
  const canEnableAutoSend = smtpConfigured && smtpVerified;
  const canEnableReplyDetection = imapConfigured && imapVerified;
  const smtpStatus = !smtpConfigured ? "unconfigured" : smtpVerified ? "verified" : "pending";
  const imapStatus = !imapConfigured ? "unconfigured" : imapVerified ? "verified" : "pending";

  const smtpTestMutation = useMutation({
    mutationFn: async () => {
      await onPersist(values);
      return api.testEmailSettings();
    },
    onSuccess: () => {
      onChange("email_smtp_last_test_at", new Date().toISOString());
    },
  });
  const imapTestMutation = useMutation({
    mutationFn: async () => {
      await onPersist(values);
      return api.testImapSettings();
    },
    onSuccess: () => {
      onChange("email_imap_last_test_at", new Date().toISOString());
    },
  });

  const statusMeta = {
    unconfigured: {
      label: "未配置",
      className: "border-slate-200 bg-slate-50 text-slate-900",
      description: "还缺少必要参数，当前不能进入对应自动化链路。",
    },
    pending: {
      label: "已配置未验证",
      className: "border-amber-200 bg-amber-50 text-amber-900",
      description: "参数已填写，但还需要点击测试连接并成功一次。",
    },
    verified: {
      label: "已验证",
      className: "border-emerald-200 bg-emerald-50 text-emerald-900",
      description: "最近一次连接测试成功，可以进入对应自动化链路。",
    },
  } as const;
  const selectedPreset = EMAIL_PROVIDER_PRESETS.find((item) => item.id === selectedPresetId) ?? EMAIL_PROVIDER_PRESETS[0];

  const applyProviderPreset = (preset: EmailProviderPreset) => {
    setSelectedPresetId(preset.id);
    if (preset.id === "manual") {
      return;
    }
    onChange("email_smtp_host", preset.smtpHost);
    onChange("email_smtp_port", preset.smtpPort);
    onChange("email_imap_host", preset.imapHost);
    onChange("email_imap_port", preset.imapPort);
    onChange("email_use_tls", preset.useTls);
    if (values.email_from_address) {
      onChange("email_smtp_username", values.email_from_address);
      onChange("email_imap_username", values.email_from_address);
      if (!values.email_reply_to) {
        onChange("email_reply_to", values.email_from_address);
      }
    }
  };

  useEffect(() => {
    const matchedPreset = EMAIL_PROVIDER_PRESETS.find((preset) => (
      preset.id !== "manual" &&
      values.email_smtp_host === preset.smtpHost &&
      values.email_smtp_port === preset.smtpPort &&
      values.email_imap_host === preset.imapHost &&
      values.email_imap_port === preset.imapPort
    ));
    setSelectedPresetId(matchedPreset?.id ?? "manual");
  }, [values.email_imap_host, values.email_imap_port, values.email_smtp_host, values.email_smtp_port]);

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <Mail className="h-5 w-5 text-primary" />
          <CardTitle className="text-base">SMTP 发信配置</CardTitle>
        </div>
        <CardDescription>
          配置企业邮箱 SMTP，用于测试连接和手动发送已批准邮件。点击测试连接时，系统会先自动保存当前表单。
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid gap-3 md:grid-cols-2">
          <div className={`rounded-md border px-3 py-3 ${statusMeta[smtpStatus].className}`}>
            <div className="flex items-center justify-between gap-3">
              <p className="text-sm font-semibold">SMTP 状态</p>
              <span className="rounded-full border border-current/20 px-2 py-0.5 text-xs font-medium">
                {statusMeta[smtpStatus].label}
              </span>
            </div>
            <p className="mt-2 text-xs leading-5 text-current/80">
              {statusMeta[smtpStatus].description}
            </p>
          </div>
          <div className={`rounded-md border px-3 py-3 ${statusMeta[imapStatus].className}`}>
            <div className="flex items-center justify-between gap-3">
              <p className="text-sm font-semibold">IMAP 状态</p>
              <span className="rounded-full border border-current/20 px-2 py-0.5 text-xs font-medium">
                {statusMeta[imapStatus].label}
              </span>
            </div>
            <p className="mt-2 text-xs leading-5 text-current/80">
              {statusMeta[imapStatus].description}
            </p>
          </div>
        </div>

        <div className="rounded-md border border-blue-200 bg-blue-50 px-4 py-4 text-sm text-blue-950">
          <p className="font-semibold">SMTP 和 IMAP 怎么配</p>
          <div className="mt-2 space-y-2 text-xs leading-5 text-blue-900/90">
            <p>1. `SMTP` 用于发信，是发送邮件的必填项。只想生成邮件并手动发送，配置 SMTP 就够了。</p>
            <p>2. `IMAP` 用于收信和检测客户回复。只有你想开启“回信自动检测”时，才需要额外配置 IMAP。</p>
            <p>3. 先确认你要用哪个发件邮箱。通常需要邮箱地址、服务器地址、端口、登录账号，以及授权码或应用专用密码。</p>
            <p>4. 很多服务商不建议直接填邮箱登录密码，而是要求先在邮箱后台开启 `SMTP / IMAP`、`第三方客户端`，再生成 `授权码` 或 `应用密码`。</p>
            <p>5. 一般去邮箱服务商的安全设置里找这些选项：`IMAP/SMTP 开启`、`第三方客户端`、`授权码`、`应用密码`。</p>
            <p>6. `SMTP 授权码 / 密码` 用于发信；`IMAP 授权码 / 密码` 用于检测回信。部分服务商两者相同，部分服务商需要分别确认。</p>
            <p>7. 填完后先测试对应连接：
              只发信时至少测试 `SMTP`；
              想自动检测回信时，再测试 `IMAP`。
            </p>
          </div>
        </div>

        <div className="rounded-md border border-amber-200 bg-amber-50 px-4 py-4 text-sm text-amber-950">
          <p className="font-semibold">主流邮箱服务商说明</p>
          <div className="mt-2 space-y-2 text-xs leading-5 text-amber-900/90">
            <p>QQ 邮箱、腾讯企业邮箱、网易 163/126、网易企业邮箱、阿里云企业邮箱，服务商类型基本是固定的：发信用 SMTP，收信/查回信用 IMAP。</p>
            <p>也就是说，服务商不会让你“只配 IMAP 就能发信”。发送邮件一定走 SMTP。</p>
            <p>如果你已经选了服务商模板，系统会自动填入常见 SMTP / IMAP 默认值；但授权码是否必需、是否允许第三方客户端，仍要以邮箱后台实际开关为准。</p>
            <p>阿里云企业邮箱和部分企业邮箱常常需要管理员先开启第三方客户端权限；网易企业邮箱不同站点的服务器地址也可能有差异，必要时请以管理员后台显示为准。</p>
          </div>
        </div>

        <div className="rounded-md border px-4 py-4">
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="text-sm font-semibold">邮箱服务商模板</p>
              <p className="mt-1 text-xs text-muted-foreground">
                选择后会自动填入常见 SMTP / IMAP 默认值。只发信时先完成 SMTP 配置即可；需要自动检测回信时再补齐 IMAP。
              </p>
            </div>
          </div>
          <div className="mt-3 flex flex-wrap gap-2">
            {EMAIL_PROVIDER_PRESETS.map((preset) => (
              <button
                key={preset.id}
                type="button"
                onClick={() => applyProviderPreset(preset)}
                className={`rounded-md border px-3 py-2 text-sm ${
                  selectedPresetId === preset.id
                    ? "border-primary bg-primary/10 text-primary"
                    : "border-border text-muted-foreground"
                }`}
              >
                {preset.label}
              </button>
            ))}
          </div>
          <p className="mt-3 text-xs text-muted-foreground">
            {selectedPreset.note}
          </p>
        </div>

        {EMAIL_DELIVERY_FIELDS.map((f) => (
          <div key={f.key} className="space-y-1.5">
            <Label htmlFor={f.key}>{f.label}</Label>
            {f.secret ? (
              <SecretInput
                id={f.key}
                value={values[f.key] ?? ""}
                onChange={(v) => onChange(f.key, v)}
                placeholder={f.placeholder}
              />
            ) : (
              <Input
                id={f.key}
                value={values[f.key] ?? ""}
                onChange={(e) => onChange(f.key, e.target.value)}
                placeholder={f.placeholder}
                className="font-mono text-sm"
              />
            )}
          </div>
        ))}

        <div className="space-y-2">
          <Label>SMTP TLS</Label>
          <div className="flex gap-2">
            {[
              ["true", "启用 TLS / STARTTLS"],
              ["false", "纯明文 / SSL 已由端口决定"],
            ].map(([value, label]) => (
              <button
                key={value}
                type="button"
                onClick={() => onChange("email_use_tls", value)}
                className={`rounded-md border px-3 py-2 text-sm ${
                  (values.email_use_tls ?? "true") === value
                    ? "border-primary bg-primary/10 text-primary"
                    : "border-border text-muted-foreground"
                }`}
              >
                {label}
              </button>
            ))}
          </div>
        </div>

        <div className="space-y-2">
          <Label>自动发送</Label>
          <div className="flex gap-2">
            {[
              ["false", "关闭"],
              ["true", "开启"],
            ].map(([value, label]) => (
              <button
                key={value}
                type="button"
                onClick={() => {
                  if (value === "true" && !canEnableAutoSend) return;
                  onChange("email_auto_send_enabled", value);
                }}
                disabled={value === "true" && !canEnableAutoSend}
                className={`rounded-md border px-3 py-2 text-sm ${
                  (values.email_auto_send_enabled ?? "false") === value
                    ? "border-primary bg-primary/10 text-primary"
                    : "border-border text-muted-foreground"
                } ${
                  value === "true" && !canEnableAutoSend
                    ? "cursor-not-allowed opacity-50"
                    : ""
                }`}
              >
                {label}
              </button>
            ))}
          </div>
          {!canEnableAutoSend && (
            <p className="text-xs text-amber-700">
              自动发送只依赖 SMTP。需要先完整填写 SMTP 参数并测试成功，才能开启自动发送。
            </p>
          )}
        </div>

        <div className="space-y-2">
          <Label>发送前必须人工审核</Label>
          <div className="flex gap-2">
            {[
              ["true", "必须审核"],
              ["false", "直接放行"],
            ].map(([value, label]) => (
              <button
                key={value}
                type="button"
                onClick={() => onChange("email_require_approval_before_send", value)}
                className={`rounded-md border px-3 py-2 text-sm ${
                  (values.email_require_approval_before_send ?? "true") === value
                    ? "border-primary bg-primary/10 text-primary"
                    : "border-border text-muted-foreground"
                }`}
              >
                {label}
              </button>
            ))}
          </div>
          <p className="text-xs text-muted-foreground">
            关闭后，`needs_review` 的邮件序列也会允许进入 campaign 和发送链路。只有手动明确拒绝的序列仍然不会发送。
          </p>
        </div>

        <div className="space-y-2">
          <Label>回信自动检测</Label>
          <div className="flex gap-2">
            {[
              ["false", "关闭"],
              ["true", "开启"],
            ].map(([value, label]) => (
              <button
                key={value}
                type="button"
                onClick={() => {
                  if (value === "true" && !canEnableReplyDetection) return;
                  onChange("email_reply_detection_enabled", value);
                }}
                disabled={value === "true" && !canEnableReplyDetection}
                className={`rounded-md border px-3 py-2 text-sm ${
                  (values.email_reply_detection_enabled ?? "false") === value
                    ? "border-primary bg-primary/10 text-primary"
                    : "border-border text-muted-foreground"
                } ${
                  value === "true" && !canEnableReplyDetection
                    ? "cursor-not-allowed opacity-50"
                    : ""
                }`}
              >
                {label}
              </button>
            ))}
          </div>
          {!canEnableReplyDetection && (
            <p className="text-xs text-amber-700">
              回信自动检测依赖 IMAP。需要先完整填写 IMAP 参数并测试成功，才能开启回信自动检测。
            </p>
          )}
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="email_reply_check_interval_seconds">回信检查间隔（秒）</Label>
          <Input
            id="email_reply_check_interval_seconds"
            value={values.email_reply_check_interval_seconds ?? ""}
            onChange={(e) => onChange("email_reply_check_interval_seconds", e.target.value)}
            placeholder="180"
            className="font-mono text-sm"
          />
        </div>

        <div className="flex items-center gap-3">
          <Button
            type="button"
            variant="outline"
            onClick={() => smtpTestMutation.mutate()}
            disabled={smtpTestMutation.isPending}
          >
            {smtpTestMutation.isPending ? (
              <><Loader2 className="h-4 w-4 mr-2 animate-spin" /> 测试中…</>
            ) : (
              "测试 SMTP 连接"
            )}
          </Button>
          {smtpTestMutation.isSuccess && (
            <p className="text-sm text-emerald-600">
              已连接到 {smtpTestMutation.data.host} / {smtpTestMutation.data.username}
            </p>
          )}
          {smtpTestMutation.isError && (
            <p className="text-sm text-destructive">{smtpTestMutation.error.message}</p>
          )}
        </div>
        {values.email_smtp_last_test_at && (
          <p className="text-xs text-muted-foreground">
            最近一次 SMTP 测试成功：{values.email_smtp_last_test_at}
          </p>
        )}

        <div className="flex items-center gap-3">
          <Button
            type="button"
            variant="outline"
            onClick={() => imapTestMutation.mutate()}
            disabled={imapTestMutation.isPending}
          >
            {imapTestMutation.isPending ? (
              <><Loader2 className="h-4 w-4 mr-2 animate-spin" /> 测试中…</>
            ) : (
              "测试 IMAP 连接"
            )}
          </Button>
          {imapTestMutation.isSuccess && (
            <p className="text-sm text-emerald-600">
              已连接到 {imapTestMutation.data.host} / {imapTestMutation.data.username}
            </p>
          )}
          {imapTestMutation.isError && (
            <p className="text-sm text-destructive">{imapTestMutation.error.message}</p>
          )}
        </div>
        {values.email_imap_last_test_at && (
          <p className="text-xs text-muted-foreground">
            最近一次 IMAP 测试成功：{values.email_imap_last_test_at}
          </p>
        )}
      </CardContent>
    </Card>
  );
}

// ── Main Settings Page ────────────────────────────────────────────────────────

export function SettingsPage() {
  const queryClient = useQueryClient();
  const [values, setValues] = useState<Record<string, string>>({});
  const [saved, setSaved] = useState(false);

  const { data, isLoading } = useQuery({
    queryKey: ["app-settings"],
    queryFn: fetchSettings,
  });

  useEffect(() => {
    if (data?.settings) {
      const mapped: Record<string, string> = {};
      const keyMap: Record<string, string> = {
        LLM_MODEL: "llm_model",
        REASONING_MODEL: "reasoning_model",
        EMAIL_LLM_MODEL: "email_llm_model",
        EMAIL_REASONING_MODEL: "email_reasoning_model",
        OPENAI_API_KEY: "openai_api_key",
        ANTHROPIC_API_KEY: "anthropic_api_key",
        OPENROUTER_API_KEY: "openrouter_api_key",
        GROQ_API_KEY: "groq_api_key",
        ZAI_API_KEY: "zai_api_key",
        MOONSHOT_API_KEY: "moonshot_api_key",
        MINIMAX_API_KEY: "minimax_api_key",
        SERPER_API_KEY: "serper_api_key",
        TAVILY_API_KEY: "tavily_api_key",
        JINA_API_KEY: "jina_api_key",
        AMAP_API_KEY: "amap_api_key",
        BAIDU_API_KEY: "baidu_api_key",
        HUNTER_API_KEY: "hunter_api_key",
        EMAIL_FROM_NAME: "email_from_name",
        EMAIL_FROM_ADDRESS: "email_from_address",
        EMAIL_REPLY_TO: "email_reply_to",
        EMAIL_SMTP_HOST: "email_smtp_host",
        EMAIL_SMTP_PORT: "email_smtp_port",
        EMAIL_SMTP_USERNAME: "email_smtp_username",
        EMAIL_SMTP_PASSWORD: "email_smtp_password",
        EMAIL_SMTP_LAST_TEST_AT: "email_smtp_last_test_at",
        EMAIL_IMAP_HOST: "email_imap_host",
        EMAIL_IMAP_PORT: "email_imap_port",
        EMAIL_IMAP_USERNAME: "email_imap_username",
        EMAIL_IMAP_PASSWORD: "email_imap_password",
        EMAIL_IMAP_LAST_TEST_AT: "email_imap_last_test_at",
        EMAIL_USE_TLS: "email_use_tls",
        EMAIL_AUTO_SEND_ENABLED: "email_auto_send_enabled",
        EMAIL_REPLY_DETECTION_ENABLED: "email_reply_detection_enabled",
        EMAIL_REPLY_CHECK_INTERVAL_SECONDS: "email_reply_check_interval_seconds",
        EMAIL_LLM_REQUESTS_PER_MINUTE: "email_llm_requests_per_minute",
        EMAIL_REASONING_REQUESTS_PER_MINUTE: "email_reasoning_requests_per_minute",
        EMAIL_REQUIRE_APPROVAL_BEFORE_SEND: "email_require_approval_before_send",
        SEARCH_CONCURRENCY: "search_concurrency",
        SCRAPE_CONCURRENCY: "scrape_concurrency",
      };
      for (const [envKey, fieldKey] of Object.entries(keyMap)) {
        if (data.settings[envKey] !== undefined) {
          mapped[fieldKey] = data.settings[envKey];
        }
      }
      setValues(mapped);
    }
  }, [data]);

  const saveMutation = useMutation({
    mutationFn: saveSettings,
    onSuccess: () => {
      setSaved(true);
      queryClient.invalidateQueries({ queryKey: ["app-settings"] });
      setTimeout(() => setSaved(false), 3000);
    },
  });

  const handleChange = (key: string, value: string) => {
    setValues((prev) => {
      const next = { ...prev, [key]: value };
      if (["email_from_address", "email_smtp_host", "email_smtp_port", "email_smtp_username", "email_smtp_password", "email_use_tls"].includes(key)) {
        next.email_smtp_last_test_at = "";
      }
      if (["email_imap_host", "email_imap_port", "email_imap_username", "email_imap_password"].includes(key)) {
        next.email_imap_last_test_at = "";
      }
      return next;
    });
  };

  const handleSave = () => {
    saveMutation.mutate(values);
  };

  const persistSettings = async (payload: Record<string, string>) => {
    await saveSettings(payload);
    await queryClient.invalidateQueries({ queryKey: ["app-settings"] });
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20 text-muted-foreground">
        <Loader2 className="h-6 w-6 animate-spin mr-2" /> 正在加载设置…
      </div>
    );
  }
  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">系统设置</h1>
        <p className="text-muted-foreground mt-1">配置模型、搜索、邮件发送和回信检测参数。</p>
      </div>

      <Separator />

      {/* LLM Provider + Models (new unified panel) */}
      <LLMProviderPanel values={values} onChange={handleChange} />

      {/* Search */}
      <FieldGroup
        title="搜索 API 密钥"
        icon={<Search className="h-5 w-5 text-primary" />}
        description="Tavily 用于通用网页检索，Serper 用于 Google Maps 与部分补充查询。"
        fields={SEARCH_FIELDS}
        values={values}
        onChange={handleChange}
      />

      {/* Email */}
      <FieldGroup
        title="邮箱工具"
        icon={<Mail className="h-5 w-5 text-primary" />}
        fields={EMAIL_FIELDS}
        values={values}
        onChange={handleChange}
      />

      <EmailDeliveryPanel values={values} onChange={handleChange} onPersist={persistSettings} />

      {/* Concurrency */}
      <FieldGroup
        title="性能参数"
        icon={<RefreshCw className="h-5 w-5 text-primary" />}
        description="根据你的 API 限流情况调整并发设置。"
        fields={CONCURRENCY_FIELDS}
        values={values}
        onChange={handleChange}
      />

      <div className="flex justify-end pb-8">
        <Button onClick={handleSave} disabled={saveMutation.isPending} size="lg">
          {saveMutation.isPending ? (
            <><Loader2 className="h-4 w-4 mr-2 animate-spin" /> 保存中…</>
          ) : saved ? (
            <><CheckCircle2 className="h-4 w-4 mr-2 text-green-500" /> 已保存</>
          ) : (
            <><Save className="h-4 w-4 mr-2" /> 保存设置</>
          )}
        </Button>
      </div>
    </div>
  );
}
