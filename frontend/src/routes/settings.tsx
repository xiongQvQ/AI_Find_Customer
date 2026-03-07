import { useState, useEffect, useRef } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Settings,
  Search,
  Cpu,
  Mail,
  Shield,
  CheckCircle2,
  XCircle,
  AlertCircle,
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
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
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

async function fetchLicenseStatus() {
  const res = await fetch(`${API_BASE}/api/settings/license/status`);
  if (!res.ok) throw new Error("检查授权失败");
  return res.json();
}

async function activateLicense(data: { license_key: string; machine_label: string }) {
  const res = await fetch(`${API_BASE}/api/settings/license/activate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail ?? "激活失败");
  }
  return res.json();
}

async function deactivateLicense() {
  await fetch(`${API_BASE}/api/settings/license/deactivate`, { method: "POST" });
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

function LicenseStatusBadge({ status }: { status: string }) {
  if (status === "valid")
    return (
      <Badge className="bg-green-500/15 text-green-600 border-green-500/30">
        <CheckCircle2 className="h-3 w-3 mr-1" /> 已激活
      </Badge>
    );
  if (status === "valid_offline")
    return (
      <Badge className="bg-yellow-500/15 text-yellow-600 border-yellow-500/30">
        <AlertCircle className="h-3 w-3 mr-1" /> 离线模式
      </Badge>
    );
  if (status === "not_activated")
    return (
      <Badge variant="outline">
        <XCircle className="h-3 w-3 mr-1" /> 未激活
      </Badge>
    );
  return (
    <Badge variant="destructive">
      <XCircle className="h-3 w-3 mr-1" /> {status}
    </Badge>
  );
}

// ── License Panel ─────────────────────────────────────────────────────────────

function LicensePanel() {
  const queryClient = useQueryClient();
  const [licenseKey, setLicenseKey] = useState("");
  const [machineLabel, setMachineLabel] = useState("");
  const [activateError, setActivateError] = useState("");

  const { data: licStatus, isLoading } = useQuery({
    queryKey: ["license-status"],
    queryFn: fetchLicenseStatus,
    retry: false,
  });

  const activateMutation = useMutation({
    mutationFn: activateLicense,
    onSuccess: () => {
      setLicenseKey("");
      setActivateError("");
      queryClient.invalidateQueries({ queryKey: ["license-status"] });
    },
    onError: (e: Error) => setActivateError(e.message),
  });

  const deactivateMutation = useMutation({
    mutationFn: deactivateLicense,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["license-status"] }),
  });

  const isActivated = licStatus?.status === "valid" || licStatus?.status === "valid_offline";

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Shield className="h-5 w-5 text-primary" />
            <CardTitle>授权信息</CardTitle>
          </div>
          {licStatus && <LicenseStatusBadge status={licStatus.status} />}
        </div>
        <CardDescription>
          激活 B2Binsights 授权后可解锁全部功能。
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {isLoading && (
          <div className="flex items-center gap-2 text-muted-foreground text-sm">
            <Loader2 className="h-4 w-4 animate-spin" /> 正在检查授权…
          </div>
        )}
        {isActivated && licStatus && (
          <div className="rounded-lg border bg-muted/30 p-4 space-y-2 text-sm">
            {licStatus.customer_name && (
              <div className="flex justify-between">
                <span className="text-muted-foreground">客户</span>
                <span className="font-medium">{licStatus.customer_name}</span>
              </div>
            )}
            {licStatus.plan && (
              <div className="flex justify-between">
                <span className="text-muted-foreground">套餐</span>
                <span className="font-medium capitalize">{licStatus.plan}</span>
              </div>
            )}
            {licStatus.expires_at && (
              <div className="flex justify-between">
                <span className="text-muted-foreground">授权有效期</span>
                <span className="font-medium">
                  {new Date(licStatus.expires_at).toLocaleDateString()}
                </span>
              </div>
            )}
            {licStatus.message && (
              <p className="text-muted-foreground text-xs pt-1">{licStatus.message}</p>
            )}
          </div>
        )}
        {!isActivated && (
          <div className="space-y-3">
            <div className="space-y-1.5">
              <Label htmlFor="license-key">授权码</Label>
              <Input
                id="license-key"
                placeholder="AIHNT-XXXXX-XXXXX-XXXXX-XXXXX"
                value={licenseKey}
                onChange={(e) => setLicenseKey(e.target.value.toUpperCase())}
                className="font-mono"
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="machine-label">设备名称（可选）</Label>
              <Input
                id="machine-label"
                placeholder="例如：销售部 MacBook"
                value={machineLabel}
                onChange={(e) => setMachineLabel(e.target.value)}
              />
            </div>
            {activateError && (
              <p className="text-destructive text-sm flex items-center gap-1">
                <XCircle className="h-4 w-4" /> {activateError}
              </p>
            )}
            <Button
              onClick={() =>
                activateMutation.mutate({ license_key: licenseKey, machine_label: machineLabel })
              }
              disabled={!licenseKey.trim() || activateMutation.isPending}
              className="w-full"
            >
              {activateMutation.isPending ? (
                <><Loader2 className="h-4 w-4 mr-2 animate-spin" /> 激活中…</>
              ) : (
                "激活授权"
              )}
            </Button>
          </div>
        )}
        {isActivated && (
          <div className="pt-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => deactivateMutation.mutate()}
              disabled={deactivateMutation.isPending}
              className="text-destructive hover:text-destructive"
            >
              {deactivateMutation.isPending ? (
                <><Loader2 className="h-3 w-3 mr-1 animate-spin" /> 解绑中…</>
              ) : (
                "解绑当前设备"
              )}
            </Button>
            <p className="text-xs text-muted-foreground mt-1">
              如需迁移授权到其他设备，请先解绑当前设备。
            </p>
          </div>
        )}
      </CardContent>
    </Card>
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

      </CardContent>
    </Card>
  );
}

// ── Search / Email / Performance panels (simple field groups) ─────────────────

type FieldDef = { key: string; label: string; placeholder?: string; secret?: boolean; hint?: string };

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

const CONCURRENCY_FIELDS: FieldDef[] = [
  { key: "search_concurrency", label: "搜索并发数", placeholder: "10", hint: "搜索 API 最大并发调用数" },
  { key: "scrape_concurrency", label: "抓取并发数", placeholder: "5", hint: "Jina 抓取最大并发调用数" },
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
    setValues((prev) => ({ ...prev, [key]: value }));
  };

  const handleSave = () => {
    saveMutation.mutate(values);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20 text-muted-foreground">
        <Loader2 className="h-6 w-6 animate-spin mr-2" /> 正在加载设置…
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Settings className="h-6 w-6" /> 系统设置
          </h1>
          {data?.env_path && (
            <p className="text-xs text-muted-foreground mt-1">
              配置文件：<code className="bg-muted px-1 rounded">{data.env_path}</code>
            </p>
          )}
        </div>
        <Button onClick={handleSave} disabled={saveMutation.isPending}>
          {saveMutation.isPending ? (
            <><Loader2 className="h-4 w-4 mr-2 animate-spin" /> 保存中…</>
          ) : saved ? (
            <><CheckCircle2 className="h-4 w-4 mr-2 text-green-500" /> 已保存</>
          ) : (
            <><Save className="h-4 w-4 mr-2" /> 保存设置</>
          )}
        </Button>
      </div>

      {/* License */}
      <LicensePanel />

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
