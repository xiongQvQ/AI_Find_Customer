import { useState, useEffect } from "react";
import { Link, Outlet } from "@tanstack/react-router";
import { Crosshair, Plus, LayoutDashboard, Settings, Shield, XCircle, Loader2, CheckCircle2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

const API_BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000";  // 本地开发: 其他 API 使用本地后端
const LICENSE_API_BASE = "https://aihunter-license-worker.xiongbojian007.workers.dev";  // License 激活使用线上环境 (待配置自定义域名)

type LicenseStatus = "loading" | "valid" | "valid_offline" | "not_activated" | "error";

// ── Machine ID (浏览器指纹) ────────────────────────────────────────────────────────

const MACHINE_ID_KEY = "aihunter_machine_id";

function getMachineId(): string {
  let mid = localStorage.getItem(MACHINE_ID_KEY);
  if (mid) return mid;

  // 生成机器指纹: 基于 user agent + 屏幕信息 + 时区
  const components = [
    navigator.userAgent,
    navigator.language,
    screen.width + "x" + screen.height,
    screen.colorDepth,
    new Intl.DateTimeFormat().resolvedOptions().timeZone,
  ];

  // 简单哈希 (生产环境可用 crypto.subtle)
  const raw = components.join("|");
  let hash = 0;
  for (let i = 0; i < raw.length; i++) {
    const char = raw.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash; // Convert to 32bit integer
  }
  mid = Math.abs(hash).toString(16).padStart(32, "0");
  localStorage.setItem(MACHINE_ID_KEY, mid);
  return mid;
}

// ── License Status Check (通过本地后端，支持离线 Token) ─────────────────────────────

async function fetchLicenseStatus(): Promise<string> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 8000);
  let res: Response;
  try {
    res = await fetch(`${API_BASE}/api/settings/license/status`, { signal: controller.signal });
  } finally {
    clearTimeout(timeout);
  }
  if (!res.ok) throw new Error("failed");
  const data = await res.json();
  return data.status as string;
}

// ── License Activation (直接调用线上 License Worker) ───────────────────────────────────

interface BindResponse {
  status: string;
  token?: string;
  token_expires_at?: string;
  plan?: string;
  license_expires_at?: string | null;
  customer_name?: string;
  message: string;
}

async function activateLicense(licenseKey: string, machineLabel: string): Promise<BindResponse> {
  const machineId = getMachineId();
  const res = await fetch(`${LICENSE_API_BASE}/api/v1/bind`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      license_key: licenseKey,
      machine_id: machineId,
      machine_label: machineLabel || undefined,
    }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ message: "激活失败" }));
    throw new Error(err.message || "激活失败");
  }

  const data = (await res.json()) as BindResponse;

  // 激活成功，将 Token 保存到本地后端
  if (data.status === "valid" && data.token) {
    await fetch(`${API_BASE}/api/settings/license/save-token`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        token: data.token,
        expires_at: data.token_expires_at || null,
      }),
    }).catch(() => {
      // 忽略保存失败，前端仍然可以使用
    });
  }

  return data;
}

// ── Activation Screen Component ─────────────────────────────────────────────────────

function ActivationScreen({ onActivated }: { onActivated: () => void }) {
  const [licenseKey, setLicenseKey] = useState("");
  const [machineLabel, setMachineLabel] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);

  const handleActivate = async () => {
    if (!licenseKey.trim()) return;
    setLoading(true);
    setError("");
    try {
      const result = await activateLicense(licenseKey.trim(), machineLabel.trim());

      if (result.status === "valid") {
        setSuccess(true);
        setTimeout(onActivated, 800);
      } else if (result.status === "already_bound") {
        setError("此 License 已绑定到其他设备，请先解绑或联系客服");
      } else if (result.status === "expired") {
        setError("License 已过期");
      } else if (result.status === "revoked") {
        setError("License 已被吊销");
      } else {
        setError(result.message || "激活失败，请检查 License Key");
      }
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "激活失败");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <div className="w-full max-w-md space-y-6">
        {/* Logo */}
        <div className="text-center space-y-2">
          <div className="flex items-center justify-center gap-2">
            <Crosshair className="h-8 w-8 text-primary" />
            <span className="text-2xl font-bold">B2Binsights</span>
          </div>
          <div className="flex items-center justify-center gap-1.5 text-muted-foreground">
            <Shield className="h-4 w-4" />
            <span className="text-sm">需要激活 License 才能使用</span>
          </div>
        </div>

        {/* Activation card */}
        <div className="rounded-xl border bg-card p-6 shadow-sm space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="license-key">License Key</Label>
            <Input
              id="license-key"
              placeholder="AIHNT-XXXXX-XXXXX-XXXXX-XXXXX"
              value={licenseKey}
              onChange={(e) => setLicenseKey(e.target.value.toUpperCase())}
              className="font-mono"
              disabled={loading || success}
              onKeyDown={(e) => e.key === "Enter" && handleActivate()}
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="machine-label">设备名称 <span className="text-muted-foreground font-normal">（可选）</span></Label>
            <Input
              id="machine-label"
              placeholder="例：我的工作电脑"
              value={machineLabel}
              onChange={(e) => setMachineLabel(e.target.value)}
              disabled={loading || success}
            />
          </div>

          {error && (
            <p className="text-destructive text-sm flex items-center gap-1.5">
              <XCircle className="h-4 w-4 shrink-0" /> {error}
            </p>
          )}

          {success && (
            <p className="text-green-600 text-sm flex items-center gap-1.5">
              <CheckCircle2 className="h-4 w-4 shrink-0" /> 激活成功，正在进入…
            </p>
          )}

          <Button
            className="w-full"
            onClick={handleActivate}
            disabled={!licenseKey.trim() || loading || success}
          >
            {loading ? (
              <><Loader2 className="h-4 w-4 mr-2 animate-spin" /> 正在激活…</>
            ) : success ? (
              <><CheckCircle2 className="h-4 w-4 mr-2" /> 激活成功</>
            ) : (
              "激活 License"
            )}
          </Button>
        </div>

        <p className="text-center text-xs text-muted-foreground">
          购买后请联系客服获取 License Key
        </p>
      </div>
    </div>
  );
}

// ── License Gate (强制激活) ─────────────────────────────────────────────────────────────

// License check is enforced by default.
// Set VITE_SKIP_LICENSE_CHECK=true to skip for development only.
const SKIP_LICENSE = import.meta.env.VITE_SKIP_LICENSE_CHECK === "true";

function LicenseGate({ children }: { children: React.ReactNode }) {
  const [status, setStatus] = useState<LicenseStatus>(SKIP_LICENSE ? "valid" : "loading");

  useEffect(() => {
    if (SKIP_LICENSE) return;
    fetchLicenseStatus()
      .then((s) => {
        if (s === "valid" || s === "valid_offline") setStatus("valid");
        else setStatus("not_activated");
      })
      .catch(() => setStatus("not_activated"));
  }, []);

  if (status === "loading") {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="flex items-center gap-2 text-muted-foreground">
          <Loader2 className="h-5 w-5 animate-spin" />
          <span className="text-sm">正在检查授权…</span>
        </div>
      </div>
    );
  }

  if (status === "not_activated") {
    return <ActivationScreen onActivated={() => setStatus("valid")} />;
  }

  return <>{children}</>;
}

// ── Root Layout ────────────────────────────────────────────────────────────────────────

export function RootLayout() {
  return (
    <LicenseGate>
      <div className="min-h-screen bg-background">
        <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
          <div className="container flex h-14 items-center mx-auto px-4">
            <Link to="/" className="flex items-center gap-2 font-bold text-lg mr-8">
              <Crosshair className="h-5 w-5 text-primary" />
              <span>B2Binsights 智能获客</span>
            </Link>
            <nav className="flex items-center gap-4 text-sm">
              <Link
                to="/"
                className="flex items-center gap-1.5 text-muted-foreground hover:text-foreground transition-colors [&.active]:text-foreground"
              >
                <LayoutDashboard className="h-4 w-4" />
                任务看板
              </Link>
              <Link
                to="/hunts/new"
                className="flex items-center gap-1.5 text-muted-foreground hover:text-foreground transition-colors [&.active]:text-foreground"
              >
                <Plus className="h-4 w-4" />
                新建任务
              </Link>
            </nav>
            <div className="ml-auto">
              <Link
                to="/settings"
                className="flex items-center gap-1.5 text-muted-foreground hover:text-foreground transition-colors [&.active]:text-foreground text-sm"
              >
                <Settings className="h-4 w-4" />
                系统设置
              </Link>
            </div>
          </div>
        </header>
        <main className="container mx-auto px-4 py-8">
          <Outlet />
        </main>
      </div>
    </LicenseGate>
  );
}
