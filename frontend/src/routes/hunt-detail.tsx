import { useEffect, useState, useCallback, useRef, useMemo } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate, useParams } from "@tanstack/react-router";
import { api, EmailDraft, EmailSequence } from "@/api/client";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Sheet, SheetHeader, SheetBody } from "@/components/ui/sheet";
import {
  Loader2, Users, Mail, Search, Brain, FileText,
  CheckCircle2, XCircle, ArrowLeft, Download, Globe,
  Building2, User, ExternalLink, Phone, MapPin,
  ChevronRight, ChevronDown, Copy, Check, Activity,
  Tag, BarChart3, PlayCircle, RefreshCw, DollarSign, Zap, TrendingUp,
} from "lucide-react";
import { Link } from "@tanstack/react-router";

// ── Continue Job Dialog ──────────────────────────────────────────────
function ContinueJobDialog({
  open, onClose, onConfirm, isLoading, currentLeads,
}: {
  open: boolean;
  onClose: () => void;
  onConfirm: (
    targetLeadCount: number,
    maxRounds: number,
    minNewLeadsThreshold: number,
    enableEmailCraft: boolean,
    emailTemplateExamples: string[],
    emailTemplateNotes: string,
  ) => void;
  isLoading: boolean;
  currentLeads: number;
}) {
  const [targetLeadCount, setTargetLeadCount] = useState(Math.max(currentLeads + 100, 200));
  const [maxRounds, setMaxRounds] = useState(10);
  const [minNewLeadsThreshold, setMinNewLeadsThreshold] = useState(5);
  const [enableEmailCraft, setEnableEmailCraft] = useState(false);
  const [emailTemplateExamplesText, setEmailTemplateExamplesText] = useState("");
  const [emailTemplateNotes, setEmailTemplateNotes] = useState("");

  // Sync default when dialog opens
  useEffect(() => {
    if (open) {
      setTargetLeadCount(Math.max(currentLeads + 100, 200));
      setMaxRounds(10);
      setMinNewLeadsThreshold(5);
      setMinNewLeadsThreshold(5);
      setEnableEmailCraft(false);
      setEmailTemplateExamplesText("");
      setEmailTemplateNotes("");
    }
  }, [open, currentLeads]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />
      <div className="relative z-10 bg-background rounded-xl shadow-2xl border w-full max-w-md mx-4 p-6 space-y-5">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-primary/10">
            <PlayCircle className="h-5 w-5 text-primary" />
          </div>
          <div>
            <h2 className="text-lg font-bold">提交后续任务</h2>
            <p className="text-sm text-muted-foreground">基于已有 {currentLeads} 条线索，创建新的 queue job 持续挖掘</p>
          </div>
        </div>

        <div className="space-y-4">
          <div className="space-y-1.5">
            <label className="text-sm font-medium">目标线索数量</label>
            <p className="text-xs text-muted-foreground">当前已有 {currentLeads} 条，建议设置更高目标</p>
            <input
              type="number"
              min={currentLeads + 1}
              max={10000}
              value={targetLeadCount}
              onChange={(e) => setTargetLeadCount(Math.max(currentLeads + 1, Number(e.target.value)))}
              className="w-full h-9 rounded-md border border-input bg-background px-3 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-sm font-medium">最大轮次</label>
            <p className="text-xs text-muted-foreground">每轮生成 5-8 个关键词并搜索</p>
            <input
              type="number"
              min={1}
              max={50}
              value={maxRounds}
              onChange={(e) => setMaxRounds(Math.max(1, Math.min(50, Number(e.target.value))))}
              className="w-full h-9 rounded-md border border-input bg-background px-3 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-sm font-medium">每轮最少新增线索</label>
            <p className="text-xs text-muted-foreground">某轮新增线索低于这个值时，会停止继续迭代。默认 5。</p>
            <input
              type="number"
              min={1}
              max={100}
              value={minNewLeadsThreshold}
              onChange={(e) => setMinNewLeadsThreshold(Math.max(1, Math.min(100, Number(e.target.value))))}
              className="w-full h-9 rounded-md border border-input bg-background px-3 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>

          <div className="flex items-center justify-between rounded-md border p-3">
            <div>
              <p className="text-sm font-medium">生成邮件序列</p>
              <p className="text-xs text-muted-foreground">继续挖掘时可为新增线索生成个性化邮件。</p>
            </div>
            <button
              onClick={() => setEnableEmailCraft((v) => !v)}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none ${
                enableEmailCraft ? "bg-primary" : "bg-muted"
              }`}
            >
              <span className={`inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform ${
                enableEmailCraft ? "translate-x-6" : "translate-x-1"
              }`} />
            </button>
          </div>

          {enableEmailCraft && (
            <div className="space-y-4 rounded-md border p-3">
              <div className="space-y-1.5">
                <label className="text-sm font-medium">历史邮件样例 / 模板样例</label>
                <textarea
                  className="min-h-[140px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                  placeholder={"可选。粘贴你过去发过的英文邮件，多封之间用空行隔开。\n\nExample 1:\nSubject: Quick intro\nHello ...\n\nExample 2:\nSubject: Potential fit\nHi ..."}
                  value={emailTemplateExamplesText}
                  onChange={(e) => setEmailTemplateExamplesText(e.target.value)}
                />
                <p className="text-xs text-muted-foreground">系统会先抽取你的模板风格，再结合新线索内容生成邮件。</p>
              </div>

              <div className="space-y-1.5">
                <label className="text-sm font-medium">模板备注</label>
                <textarea
                  className="min-h-[90px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                  placeholder="例如：保持简洁直接；避免夸张表述；CTA 不要太强；优先突出渠道合作。"
                  value={emailTemplateNotes}
                  onChange={(e) => setEmailTemplateNotes(e.target.value)}
                />
              </div>
            </div>
          )}
        </div>

        <div className="rounded-md bg-muted/50 border p-3 text-xs text-muted-foreground space-y-1">
          <p className="font-medium text-foreground">将保留的数据：</p>
          <p>✓ 已有线索 ({currentLeads} 条) &nbsp;✓ 公司洞察 &nbsp;✓ 关键词历史 &nbsp;✓ 搜索统计</p>
          <p className="font-medium text-foreground mt-1">将重置的数据：</p>
          <p>↺ 轮次计数 &nbsp;↺ 搜索结果缓存（保留去重记录）&nbsp;↺ 邮件序列</p>
        </div>

        <div className="flex gap-3 pt-1">
          <Button variant="outline" className="flex-1" onClick={onClose} disabled={isLoading}>
            取消
          </Button>
          <Button
            className="flex-1"
            onClick={() => onConfirm(
              targetLeadCount,
              maxRounds,
              minNewLeadsThreshold,
              enableEmailCraft,
              emailTemplateExamplesText
                .split(/\n\s*\n/)
                .map((item) => item.trim())
                .filter(Boolean),
              emailTemplateNotes.trim(),
            )}
            disabled={isLoading}
          >
            {isLoading ? (
              <><Loader2 className="h-4 w-4 mr-2 animate-spin" />提交中...</>
            ) : (
              <><PlayCircle className="h-4 w-4 mr-2" />提交后续任务</>
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}

// ── Lead type helper ──────────────────────────────────────────────────
type Lead = Record<string, unknown>;

function getLeadEmails(lead: Lead): string[] { return (lead.emails as string[]) || []; }
function getLeadPhones(lead: Lead): string[] { return (lead.phone_numbers as string[]) || []; }
function getLeadSocial(lead: Lead): Record<string, string> { return (lead.social_media as Record<string, string>) || {}; }
function getLeadStr(lead: Lead, key: string): string { return typeof lead[key] === "string" ? (lead[key] as string) : ""; }
function normalizeDecisionMakerEmail(email: string): string {
  return email.replace(/\s*\(inferred\)\s*$/i, "").trim();
}
function isGenericDecisionMakerMailbox(email: string): boolean {
  const normalized = normalizeDecisionMakerEmail(email).toLowerCase();
  if (!normalized || !normalized.includes("@")) return false;
  const [local] = normalized.split("@", 1);
  const compact = local.replace(/[\W_]+/g, "");
  const genericLocals = new Set([
    "info", "sales", "contact", "support", "office", "hello", "admin",
    "marketing", "service", "services", "team", "enquiry", "enquiries",
    "inquiry", "inquiries", "export", "exports", "import", "imports",
    "cs", "customerservice",
  ]);
  if (genericLocals.has(local) || genericLocals.has(compact)) return true;
  return local.split(/[\W_]+/).some((token) => genericLocals.has(token));
}
function toChineseRole(role: string): string {
  const map: Record<string, string> = {
    distributor: "分销商",
    importer: "进口商",
    wholesaler: "批发商",
    oem: "OEM / 设备制造商",
    integrator: "系统集成商",
    end_user: "终端工厂",
    service: "服务商",
    retailer: "零售商",
    manufacturer: "制造商",
    unknown: "待判断",
  };
  return map[role] || role;
}
function toChineseRisk(level: string): string {
  const map: Record<string, string> = { low: "低", medium: "中", high: "高" };
  return map[level] || level;
}
function toChineseEvidence(level: string): string {
  const map: Record<string, string> = { low: "低", medium: "中", high: "高" };
  return map[level] || level;
}
function toChinesePriority(level: string): string {
  const map: Record<string, string> = { high: "高优先级", medium: "中优先级", low: "低优先级", reject: "排除" };
  return map[level] || level;
}
function getDecisionMakerEmailStatus(email: string): "verified" | "inferred-from-pattern" | "no-email-evidence" {
  const normalized = String(email || "").trim();
  if (!normalized) return "no-email-evidence";
  if (isGenericDecisionMakerMailbox(normalized)) return "no-email-evidence";
  if (/\(inferred\)\s*$/i.test(normalized) || normalized.toLowerCase() === "inferred") {
    return "inferred-from-pattern";
  }
  return "verified";
}
function getLeadNum(lead: Lead, key: string, fallback = 0): number {
  const value = lead[key];
  return typeof value === "number" ? value : (typeof value === "string" ? Number(value || fallback) : fallback);
}
function hasConcreteCustomsData(value: string): boolean {
  const text = value.trim().toLowerCase();
  if (!text) return false;
  const negativeMarkers = [
    "no data found",
    "no concrete customs data found",
    "no detailed customs data available",
    "no data available",
    "no public customs data",
    "not an importer/exporter",
    "not an importer",
    "not an exporter",
    "service-based",
    "engineering services provider",
    "not applicable",
  ];
  return !negativeMarkers.some((marker) => text.includes(marker));
}
function getLeadKey(lead: Lead): string {
  const website = getLeadStr(lead, "website").trim().toLowerCase();
  if (website) return `w:${website}`;
  const company = getLeadStr(lead, "company_name").trim().toLowerCase();
  if (company) return `c:${company}`;
  const emails = getLeadEmails(lead);
  if (emails.length > 0) return `e:${emails[0].trim().toLowerCase()}`;
  return `raw:${JSON.stringify(lead)}`;
}

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" ? value as Record<string, unknown> : {};
}

function asStringArray(value: unknown): string[] {
  return Array.isArray(value) ? value.filter((item): item is string => typeof item === "string" && item.trim().length > 0) : [];
}

function formatTemplateSource(source: string): string {
  return source === "user_examples" ? "历史模板" : "自动模板";
}

function formatReviewStatus(status: string): string {
  return status === "approved" ? "可进入发送流程" : "需人工复核";
}

function isSequenceReadyForSend(sequence: EmailSequence): boolean {
  const manualReview = asRecord(sequence.manual_review);
  if (String(manualReview.decision || "") === "approved") {
    return true;
  }
  if (String(manualReview.decision || "") === "rejected") {
    return false;
  }
  return Boolean(sequence.auto_send_eligible);
}

function formatEmailType(emailType: string): string {
  const labels: Record<string, string> = {
    company_intro: "首封介绍",
    product_showcase: "产品介绍",
    partnership_proposal: "合作提案",
  };
  return labels[emailType] || emailType;
}

function formatGenerationMode(mode: string): string {
  const labels: Record<string, string> = {
    template_pool: "组模板首稿",
    template_pool_personalized: "组模板后二次个性化",
    personalized: "逐条个性化",
  };
  return labels[mode] || mode || "未知模式";
}

function formatTemplatePerfStatus(status: string): string {
  const labels: Record<string, string> = {
    warming_up: "数据积累中",
    underperforming: "表现偏弱",
    exhausted: "已达上限",
  };
  return labels[status] || status || "未知";
}

function formatTemplateAction(action: string): string {
  const labels: Record<string, string> = {
    keep_collecting_data: "继续收集数据",
    optimize_template_before_more_sends: "先优化模板再继续发",
    create_new_template_version: "创建下一版模板",
  };
  return labels[action] || action || "待观察";
}

function buildSequencePreviewText(sequence: EmailSequence): string {
  const companyName = String(asRecord(sequence.lead).company_name || "Unknown company");
  const locale = sequence.locale || "en_US";
  const blocks = sequence.emails.map((email) => (
    [
      `#${email.sequence_number} ${formatEmailType(email.email_type)}`,
      `Subject: ${email.subject}`,
      `Send day: ${email.suggested_send_day}`,
      "",
      email.body_text,
    ].join("\n")
  ));
  return [`Company: ${companyName}`, `Locale: ${locale}`, "", ...blocks].join("\n\n");
}

function formatSendStatus(status: string): string {
  const labels: Record<string, string> = {
    queued: "队列中",
    sent: "已发送",
    failed: "发送失败",
  };
  return labels[status] || "未发送";
}

function compareLeads(a: Lead, b: Lead): number {
  const fitDiff = getLeadNum(b, "fit_score", getLeadNum(b, "match_score")) - getLeadNum(a, "fit_score", getLeadNum(a, "match_score"));
  if (fitDiff !== 0) return fitDiff;

  const customsDiff = getLeadNum(b, "customs_score") - getLeadNum(a, "customs_score");
  if (customsDiff !== 0) return customsDiff;

  const contactDiff = getLeadNum(b, "contactability_score") - getLeadNum(a, "contactability_score");
  if (contactDiff !== 0) return contactDiff;

  const decisionMakerDiff = (((b.decision_makers as Array<unknown>) || []).length) - (((a.decision_makers as Array<unknown>) || []).length);
  if (decisionMakerDiff !== 0) return decisionMakerDiff;

  return getLeadNum(b, "match_score") - getLeadNum(a, "match_score");
}

// ── Social media platform icons (text-based, no extra deps) ───────────
const SOCIAL_LABELS: Record<string, string> = {
  linkedin: "LinkedIn",
  facebook: "Facebook",
  twitter: "Twitter / X",
  instagram: "Instagram",
  youtube: "YouTube",
  whatsapp: "WhatsApp",
  wechat: "WeChat",
};

// ── Copy button helper ────────────────────────────────────────────────
function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  const handleCopy = (e: React.MouseEvent) => {
    e.stopPropagation();
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };
  return (
    <button onClick={handleCopy} className="p-0.5 rounded hover:bg-muted transition-colors text-muted-foreground hover:text-foreground">
      {copied ? <Check className="h-3 w-3 text-green-600" /> : <Copy className="h-3 w-3" />}
    </button>
  );
}

// ── Lead Detail Sheet ─────────────────────────────────────────────────
function LeadDetailSheet({ lead, open, onClose }: { lead: Lead | null; open: boolean; onClose: () => void }) {
  if (!lead) return null;

  const emails = getLeadEmails(lead);
  const phones = getLeadPhones(lead);
  const social = getLeadSocial(lead);
  const address = getLeadStr(lead, "address");
  const description = getLeadStr(lead, "description");
  const website = getLeadStr(lead, "website");
  const industry = getLeadStr(lead, "industry");
  const countryCode = getLeadStr(lead, "country_code");
  const contactPerson = getLeadStr(lead, "contact_person");
  const fitScore = Number(lead.fit_score ?? lead.match_score ?? 0);
  const contactabilityScore = Number(lead.contactability_score || 0);
  const customsScore = Number(lead.customs_score || 0);
  const priorityTier = getLeadStr(lead, "priority_tier") || "low";
  const customerRole = getLeadStr(lead, "customer_role") || "unknown";
  const competitorRisk = getLeadStr(lead, "competitor_risk") || "low";
  const evidenceStrength = getLeadStr(lead, "evidence_strength") || "low";
  const riskFlags = Array.isArray(lead.risk_flags) ? (lead.risk_flags as string[]) : [];
  const businessTypes = (lead.business_types as string[]) || [];
  const decisionMakers = (lead.decision_makers as Array<{name?: string; title?: string; email?: string; linkedin?: string}>) || [];
  const customsRecords = (lead.customs_records as Array<{
    provider?: string;
    source_url?: string;
    source_title?: string;
    period?: string;
    trade_direction?: string;
    partner_countries?: string[];
    hs_codes?: string[];
    product_clues?: string[];
    fetch_method?: string;
    confidence?: number;
  }>) || [];
  const customsData = getLeadStr(lead, "customs_data");
  const evidence = (lead.evidence as Array<{claim?: string; source_url?: string}>) || [];
  const mapsData = (lead.maps_data as Record<string, unknown>) || {};
  const mapsType = typeof mapsData.type === "string" ? mapsData.type : "";
  const mapsTypes = Array.isArray(mapsData.types) ? (mapsData.types as string[]) : [];
  const mapsDescription = typeof mapsData.description === "string" ? mapsData.description : "";
  const mapsEmail = typeof mapsData.email === "string" ? mapsData.email : "";
  const mapsPhone = typeof mapsData.phoneNumber === "string"
    ? mapsData.phoneNumber
    : (typeof mapsData.phone_number === "string" ? mapsData.phone_number : "");
  const mapsAddress = typeof mapsData.address === "string" ? mapsData.address : "";

  return (
    <Sheet open={open} onClose={onClose}>
      <SheetHeader>
        <div className="flex items-start gap-3 pr-8">
          <div className="p-2.5 rounded-lg bg-primary/10">
            <Building2 className="h-6 w-6 text-primary" />
          </div>
          <div className="min-w-0 flex-1">
            <h2 className="text-xl font-bold truncate">{String(lead.company_name || "未知企业")}</h2>
            <div className="flex items-center gap-2 mt-1 flex-wrap">
              {industry && <Badge variant="outline">{industry}</Badge>}
              {countryCode && <Badge variant="outline">{countryCode}</Badge>}
              <Badge variant={fitScore >= 0.7 ? "success" : fitScore >= 0.4 ? "warning" : "secondary"}>
                匹配度 {(fitScore * 100).toFixed(0)}%
              </Badge>
              {customsScore > 0 && (
                <Badge variant="outline">
                  海关 {(customsScore * 100).toFixed(0)}%
                </Badge>
              )}
              <Badge variant="outline">{toChinesePriority(priorityTier)}</Badge>
            </div>
          </div>
        </div>
      </SheetHeader>

      <SheetBody className="space-y-6">
        {/* Description */}
        {description && (
          <div>
            <h3 className="text-sm font-semibold text-muted-foreground mb-1.5">企业介绍</h3>
            <p className="text-sm leading-relaxed">{description}</p>
          </div>
        )}

        {(contactabilityScore > 0 || customsScore > 0) && (
          <div>
            <h3 className="text-sm font-semibold text-muted-foreground mb-1.5">评分</h3>
            <div className="flex items-center gap-2 flex-wrap">
              <Badge variant="outline">可联系性 {(contactabilityScore * 100).toFixed(0)}%</Badge>
              <Badge variant="outline">海关 {(customsScore * 100).toFixed(0)}%</Badge>
            </div>
          </div>
        )}

        <div>
          <h3 className="text-sm font-semibold text-muted-foreground mb-1.5">资格判断</h3>
          <div className="flex items-center gap-2 flex-wrap">
            <Badge variant="outline">{toChineseRole(customerRole)}</Badge>
            <Badge variant={competitorRisk === "high" ? "destructive" : competitorRisk === "medium" ? "warning" : "outline"}>
              竞争风险 {toChineseRisk(competitorRisk)}
            </Badge>
            <Badge variant="outline">证据强度 {toChineseEvidence(evidenceStrength)}</Badge>
            {riskFlags.map((flag, i) => (
              <Badge key={`${flag}-${i}`} variant="secondary">{flag}</Badge>
            ))}
          </div>
        </div>

        {/* Website */}
        {website && (
          <div>
            <h3 className="text-sm font-semibold text-muted-foreground mb-1.5">官网</h3>
            <a href={website} target="_blank" rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 text-sm text-primary hover:underline">
              <Globe className="h-3.5 w-3.5" />
              {website}
              <ExternalLink className="h-3 w-3" />
            </a>
          </div>
        )}

        {/* Contact Person */}
        {contactPerson && (
          <div>
            <h3 className="text-sm font-semibold text-muted-foreground mb-1.5">联系人</h3>
            <div className="flex items-center gap-2 text-sm">
              <User className="h-4 w-4 text-muted-foreground" />
              <span>{contactPerson}</span>
            </div>
          </div>
        )}

        {/* Emails */}
        {emails.length > 0 && (
          <div>
            <h3 className="text-sm font-semibold text-muted-foreground mb-1.5">
              邮箱 ({emails.length})
            </h3>
            <div className="space-y-1.5">
              {emails.map((email, i) => (
                <div key={i} className="flex items-center gap-2 text-sm group">
                  <Mail className="h-3.5 w-3.5 text-muted-foreground flex-shrink-0" />
                  <a href={`mailto:${email}`} className="text-primary hover:underline truncate">{email}</a>
                  <CopyButton text={email} />
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Phone Numbers */}
        {phones.length > 0 && (
          <div>
            <h3 className="text-sm font-semibold text-muted-foreground mb-1.5">
              电话 ({phones.length})
            </h3>
            <div className="space-y-1.5">
              {phones.map((phone, i) => (
                <div key={i} className="flex items-center gap-2 text-sm group">
                  <Phone className="h-3.5 w-3.5 text-muted-foreground flex-shrink-0" />
                  <a href={`tel:${phone}`} className="text-primary hover:underline">{phone}</a>
                  <CopyButton text={phone} />
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Address */}
        {address && (
          <div>
            <h3 className="text-sm font-semibold text-muted-foreground mb-1.5">地址</h3>
            <div className="flex items-start gap-2 text-sm">
              <MapPin className="h-3.5 w-3.5 text-muted-foreground flex-shrink-0 mt-0.5" />
              <span>{address}</span>
              <CopyButton text={address} />
            </div>
          </div>
        )}

        {/* Social Media */}
        {Object.keys(social).length > 0 && (
          <div>
            <h3 className="text-sm font-semibold text-muted-foreground mb-1.5">社交媒体</h3>
            <div className="grid gap-2">
              {Object.entries(social).map(([platform, url]) => (
                <a key={platform} href={url} target="_blank" rel="noopener noreferrer"
                  className="flex items-center gap-2.5 text-sm p-2 rounded-md border hover:bg-muted transition-colors group">
                  <ExternalLink className="h-3.5 w-3.5 text-muted-foreground group-hover:text-primary" />
                  <span className="font-medium">{SOCIAL_LABELS[platform] || platform}</span>
                  <span className="text-muted-foreground text-xs truncate ml-auto max-w-[200px]">{url}</span>
                </a>
              ))}
            </div>
          </div>
        )}

        {/* Business Types */}
        {businessTypes.length > 0 && (
          <div>
            <h3 className="text-sm font-semibold text-muted-foreground mb-1.5">业务类型</h3>
            <div className="flex flex-wrap gap-1.5">
              {businessTypes.map((type, i) => (
                <Badge key={i} variant="secondary">{type}</Badge>
              ))}
            </div>
          </div>
        )}

        {/* Decision Makers */}
        {decisionMakers.length > 0 && (
          <div>
            <h3 className="text-sm font-semibold text-muted-foreground mb-1.5">
              决策人 ({decisionMakers.length})
            </h3>
            <div className="space-y-2">
              {decisionMakers.map((dm, i) => {
                const displayEmail = isGenericDecisionMakerMailbox(dm.email || "") ? "" : normalizeDecisionMakerEmail(dm.email || "");
                const emailStatus = getDecisionMakerEmailStatus(dm.email || "");
                return (
                  <div key={i} className="rounded-md border p-3 space-y-1.5">
                    <div className="flex items-center gap-2">
                      <User className="h-3.5 w-3.5 text-muted-foreground" />
                      <span className="font-medium text-sm">{dm.name || "未知联系人"}</span>
                      {dm.title && <span className="text-xs text-muted-foreground">· {dm.title}</span>}
                    </div>
                    {displayEmail && (
                      <div className="flex items-center gap-2 text-sm pl-5">
                        <Mail className="h-3 w-3 text-muted-foreground" />
                        <a href={`mailto:${displayEmail}`} className="text-primary hover:underline">{displayEmail}</a>
                        <Badge variant={emailStatus === "verified" ? "outline" : "secondary"}>
                          {emailStatus === "verified" ? "已验证" : "按邮箱规则推断"}
                        </Badge>
                        <CopyButton text={displayEmail} />
                      </div>
                    )}
                    {!displayEmail && (
                      <div className="flex items-center gap-2 text-sm pl-5">
                        <Mail className="h-3 w-3 text-muted-foreground" />
                        <Badge variant="secondary">暂无邮箱证据</Badge>
                      </div>
                    )}
                    {dm.linkedin && (
                      <div className="flex items-center gap-2 text-sm pl-5">
                        <ExternalLink className="h-3 w-3 text-muted-foreground" />
                        <a href={dm.linkedin} target="_blank" rel="noopener noreferrer" className="text-primary hover:underline truncate max-w-[250px]">
                          LinkedIn 主页
                        </a>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Customs Data */}
        {hasConcreteCustomsData(customsData) && (
          <div>
            <h3 className="text-sm font-semibold text-muted-foreground mb-1.5">海关 / 贸易数据</h3>
            <p className="text-sm leading-relaxed">{customsData}</p>
            {customsRecords.length > 0 && (
              <div className="mt-3 space-y-2">
                {customsRecords.slice(0, 5).map((record, i) => (
                  <div key={i} className="rounded-md border p-3 text-sm space-y-1.5">
                    <div className="flex items-center gap-2 flex-wrap">
                      {record.provider && <Badge variant="outline">{record.provider}</Badge>}
                      {record.trade_direction && <Badge variant="outline">{record.trade_direction.replace("_", "/")}</Badge>}
                      {record.period && <Badge variant="outline">{record.period}</Badge>}
                      {typeof record.confidence === "number" && <Badge variant="secondary">置信度 {(record.confidence * 100).toFixed(0)}%</Badge>}
                    </div>
                    {record.partner_countries && record.partner_countries.length > 0 && (
                      <p><span className="font-medium">国家：</span> {record.partner_countries.join(", ")}</p>
                    )}
                    {record.hs_codes && record.hs_codes.length > 0 && (
                      <p><span className="font-medium">HS 编码：</span> {record.hs_codes.join(", ")}</p>
                    )}
                    {record.product_clues && record.product_clues.length > 0 && (
                      <p><span className="font-medium">产品线索：</span> {record.product_clues.join(", ")}</p>
                    )}
                    {record.source_title && (
                      <p><span className="font-medium">来源：</span> {record.source_title}</p>
                    )}
                    {record.source_url && (
                      <a href={record.source_url} target="_blank" rel="noopener noreferrer" className="text-primary hover:underline text-xs break-all">
                        {record.source_url}
                      </a>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {(fitScore > 0 || contactabilityScore > 0) && (
          <div>
            <h3 className="text-sm font-semibold text-muted-foreground mb-1.5">评分明细</h3>
            <div className="grid grid-cols-2 gap-2 text-sm">
              <div className="rounded-md border p-2"><span className="font-medium">匹配度：</span> {(fitScore * 100).toFixed(0)}%</div>
              <div className="rounded-md border p-2"><span className="font-medium">可联系性：</span> {(contactabilityScore * 100).toFixed(0)}%</div>
            </div>
          </div>
        )}

        {evidence.length > 0 && (
          <div>
            <h3 className="text-sm font-semibold text-muted-foreground mb-1.5">证据</h3>
            <div className="space-y-2">
              {evidence.slice(0, 5).map((ev, i) => (
                <div key={i} className="rounded-md border p-2 text-sm">
                  <p>{ev.claim || "证据说明"}</p>
                  {ev.source_url && (
                    <a href={ev.source_url} target="_blank" rel="noopener noreferrer" className="text-primary hover:underline text-xs">
                      {ev.source_url}
                    </a>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Google Maps Raw Data */}
        {(mapsType || mapsTypes.length > 0 || mapsAddress || mapsPhone || mapsDescription || mapsEmail) && (
          <div>
            <h3 className="text-sm font-semibold text-muted-foreground mb-1.5">Google Maps 快照</h3>
            <div className="space-y-2 rounded-md border p-3 text-sm">
              {mapsType && <p><span className="font-medium">类型：</span> {mapsType}</p>}
              {mapsTypes.length > 0 && (
                <p><span className="font-medium">分类：</span> {mapsTypes.join(", ")}</p>
              )}
              {mapsAddress && <p><span className="font-medium">地址：</span> {mapsAddress}</p>}
              {mapsPhone && <p><span className="font-medium">电话：</span> {mapsPhone}</p>}
              {mapsEmail && <p><span className="font-medium">邮箱：</span> {mapsEmail}</p>}
              {mapsDescription && <p><span className="font-medium">简介：</span> {mapsDescription}</p>}
            </div>
          </div>
        )}

        {/* Source info */}
        <div className="pt-2 border-t">
          <div className="flex items-center gap-4 text-xs text-muted-foreground">
            {getLeadStr(lead, "source") && <span>来源：{getLeadStr(lead, "source")}</span>}
            {getLeadStr(lead, "source_keyword") && <span>关键词：{getLeadStr(lead, "source_keyword")}</span>}
          </div>
        </div>
      </SheetBody>
    </Sheet>
  );
}

function EmailSequencePreviewSheet({
  sequence,
  open,
  onClose,
  onApprove,
  onReject,
  onSendDraft,
  onDetectReplies,
  isUpdating,
  isSending,
  isCheckingReplies,
}: {
  sequence: EmailSequence | null;
  open: boolean;
  onClose: () => void;
  onApprove: () => void;
  onReject: () => void;
  onSendDraft: (sequenceNumber: number) => void;
  onDetectReplies: () => void;
  isUpdating: boolean;
  isSending: boolean;
  isCheckingReplies: boolean;
}) {
  if (!sequence) return null;

  const lead = asRecord(sequence.lead);
  const reviewSummary = asRecord(sequence.review_summary);
  const validationSummary = asRecord(sequence.validation_summary);
  const templateProfile = asRecord(sequence.template_profile);
  const templatePlan = asRecord(sequence.template_plan);
  const templatePerformance = asRecord(sequence.template_performance);
  const proofPoints = asStringArray(templatePlan.proof_points);
  const issues = asStringArray(reviewSummary.issues);
  const validationIssues = asStringArray(validationSummary.issues);
  const validationSuggestions = asStringArray(validationSummary.suggestions);
  const manualReview = asRecord(sequence.manual_review);
  const replyDetection = asRecord(sequence.reply_detection);
  const replies = Array.isArray(replyDetection.replies) ? replyDetection.replies as Array<Record<string, string>> : [];

  return (
    <Sheet open={open} onClose={onClose} className="max-w-3xl">
      <SheetHeader>
        <div className="flex items-start gap-3 pr-8">
          <div className="p-2.5 rounded-lg bg-primary/10">
            <Mail className="h-6 w-6 text-primary" />
          </div>
          <div className="min-w-0 flex-1">
            <h2 className="text-xl font-bold truncate">{String(lead.company_name || "邮件预览")}</h2>
            <div className="mt-2 flex flex-wrap items-center gap-2">
              <Badge variant="outline">{sequence.locale || "en_US"}</Badge>
              <Badge className={sequence.auto_send_eligible ? "bg-emerald-600 hover:bg-emerald-600" : "bg-amber-600 hover:bg-amber-600"}>
                {sequence.auto_send_eligible ? "可建发送流程" : "需人工复核"}
              </Badge>
              <Badge variant="outline">Score {String(reviewSummary.score || 0)}</Badge>
              <Badge variant="outline">{formatTemplateSource(String(templateProfile.source || "auto_generated"))}</Badge>
              <Badge variant="outline">{formatGenerationMode(String(sequence.generation_mode || "personalized"))}</Badge>
              {sequence.template_reused ? <Badge variant="outline">复用模板</Badge> : <Badge variant="outline">模板首稿</Badge>}
              {Boolean(manualReview.decision) && (
                <Badge variant="outline">
                  人工决策: {String(manualReview.decision) === "approved" ? "已批准" : "已拦截"}
                </Badge>
              )}
            </div>
          </div>
          <CopyButton text={buildSequencePreviewText(sequence)} />
        </div>
      </SheetHeader>

      <SheetBody className="space-y-6">
        <div className="grid gap-3 md:grid-cols-3">
          <div className="rounded-md border p-3">
            <p className="text-xs uppercase tracking-wide text-muted-foreground">Tone</p>
            <p className="mt-1 text-sm font-medium">{String(templateProfile.tone || "n/a")}</p>
          </div>
          <div className="rounded-md border p-3">
            <p className="text-xs uppercase tracking-wide text-muted-foreground">Opening</p>
            <p className="mt-1 text-sm font-medium">{String(templatePlan.opening_strategy || "n/a")}</p>
          </div>
          <div className="rounded-md border p-3">
            <p className="text-xs uppercase tracking-wide text-muted-foreground">CTA</p>
            <p className="mt-1 text-sm font-medium">{String(templatePlan.cta_strategy || "n/a")}</p>
          </div>
        </div>

        <div className="grid gap-3 md:grid-cols-3">
          <div className="rounded-md border p-3">
            <p className="text-xs uppercase tracking-wide text-muted-foreground">Validation</p>
            <p className="mt-1 text-sm font-medium">{String(validationSummary.status || "n/a")}</p>
          </div>
          <div className="rounded-md border p-3">
            <p className="text-xs uppercase tracking-wide text-muted-foreground">Template Status</p>
            <p className="mt-1 text-sm font-medium">{formatTemplatePerfStatus(String(templatePerformance.status || "warming_up"))}</p>
          </div>
          <div className="rounded-md border p-3">
            <p className="text-xs uppercase tracking-wide text-muted-foreground">Next Action</p>
            <p className="mt-1 text-sm font-medium">{formatTemplateAction(String(templatePerformance.recommended_action || "keep_collecting_data"))}</p>
          </div>
        </div>

        {sequence.template_id && (
          <div className="rounded-md border p-3 text-sm">
            <div className="flex flex-wrap gap-x-6 gap-y-1 text-muted-foreground">
              <p>Template ID: <span className="text-foreground">{String(sequence.template_id)}</span></p>
              <p>Usage: <span className="text-foreground">{String(sequence.template_usage_index || 0)} / {String(sequence.template_assigned_count || 0)}</span></p>
              <p>Remaining: <span className="text-foreground">{String(sequence.template_remaining_capacity ?? "n/a")}</span></p>
            </div>
            {Boolean(templatePerformance.reason) && (
              <p className="mt-2 text-muted-foreground">{String(templatePerformance.reason)}</p>
            )}
          </div>
        )}

        {proofPoints.length > 0 && (
          <div>
            <p className="mb-2 text-sm font-semibold">Proof Points</p>
            <div className="flex flex-wrap gap-2">
              {proofPoints.map((item) => (
                <Badge key={item} variant="secondary">{item}</Badge>
              ))}
            </div>
          </div>
        )}

        {issues.length > 0 && (
          <div className="rounded-md border border-amber-200 bg-amber-50 p-4 dark:border-amber-900 dark:bg-amber-950/20">
            <p className="mb-2 text-sm font-semibold text-amber-800 dark:text-amber-300">Review Issues</p>
            <ul className="space-y-1 text-sm text-amber-700 dark:text-amber-400">
              {issues.map((issue) => <li key={issue}>• {issue}</li>)}
            </ul>
          </div>
        )}

        {(validationIssues.length > 0 || validationSuggestions.length > 0) && (
          <div className="rounded-md border p-4">
            <p className="mb-2 text-sm font-semibold">Validation Summary</p>
            {validationIssues.length > 0 && (
              <ul className="space-y-1 text-sm text-amber-700 dark:text-amber-400">
                {validationIssues.map((issue) => <li key={issue}>• {issue}</li>)}
              </ul>
            )}
            {validationSuggestions.length > 0 && (
              <ul className="mt-3 space-y-1 text-sm text-muted-foreground">
                {validationSuggestions.map((item) => <li key={item}>• {item}</li>)}
              </ul>
            )}
          </div>
        )}

        <div className="flex flex-wrap gap-2">
          <Button type="button" onClick={onApprove} disabled={isUpdating}>
            {isUpdating ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
            批准草稿
          </Button>
          <Button type="button" variant="outline" onClick={onReject} disabled={isUpdating}>
            拦截并保留草稿
          </Button>
          <Button type="button" variant="outline" onClick={onDetectReplies} disabled={isCheckingReplies}>
            {isCheckingReplies ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
            检查回信
          </Button>
        </div>

        <div className="rounded-md border p-3">
          <p className="text-sm font-medium">回信状态</p>
          <p className="mt-1 text-sm text-muted-foreground">
            {replyDetection.checked_at
              ? `最近检查时间 ${String(replyDetection.checked_at)}，发现 ${String(replyDetection.reply_count || 0)} 封回信`
              : "尚未检查回信"}
          </p>
          {replies.length > 0 && (
            <div className="mt-3 space-y-2">
              {replies.map((reply, index) => (
                <div key={`${reply.message_id || reply.subject || index}`} className="rounded-md bg-muted p-3 text-sm">
                  <p className="font-medium">{String(reply.subject || "(无主题)")}</p>
                  <p className="text-xs text-muted-foreground">{String(reply.date || "")}</p>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="space-y-4">
          {sequence.emails.map((email: EmailDraft) => (
            <div key={`${email.sequence_number}-${email.subject}`} className="rounded-lg border p-4 space-y-3">
              <div className="flex items-start gap-3">
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge variant="secondary">#{email.sequence_number}</Badge>
                    <Badge variant="outline">{formatEmailType(email.email_type)}</Badge>
                    <Badge variant="outline">Day {email.suggested_send_day}</Badge>
                    {email.send_status === "queued" && (
                      <Badge variant="outline">队列中</Badge>
                    )}
                    {email.send_status === "sent" && (
                      <Badge className="bg-emerald-600 hover:bg-emerald-600">已发送</Badge>
                    )}
                    {email.send_status === "failed" && (
                      <Badge variant="destructive">发送失败</Badge>
                    )}
                  </div>
                  <p className="mt-2 text-base font-semibold">{email.subject}</p>
                </div>
                <CopyButton text={`Subject: ${email.subject}\n\n${email.body_text}`} />
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <Button
                  type="button"
                  size="sm"
                  variant="outline"
                  onClick={() => onSendDraft(email.sequence_number)}
                  disabled={isSending || !sequence.auto_send_eligible}
                >
                  {isSending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
                  发送这封
                </Button>
                {email.sent_to && (
                  <p className="text-xs text-muted-foreground">
                    已发送到 {email.sent_to}{email.sent_at ? ` · ${email.sent_at}` : ""}
                  </p>
                )}
                {email.send_status === "queued" && (
                  <p className="text-xs text-muted-foreground">已进入发送队列。</p>
                )}
              </div>
              <p className="whitespace-pre-wrap text-sm text-muted-foreground">{email.body_text}</p>
              {((email.personalization_points || []).length > 0 || (email.cultural_adaptations || []).length > 0) && (
                <div className="grid gap-3 md:grid-cols-2">
                  {(email.personalization_points || []).length > 0 && (
                    <div>
                      <p className="mb-1 text-xs uppercase tracking-wide text-muted-foreground">Personalization</p>
                      <div className="flex flex-wrap gap-2">
                        {(email.personalization_points || []).map((point) => (
                          <Badge key={point} variant="secondary">{point}</Badge>
                        ))}
                      </div>
                    </div>
                  )}
                  {(email.cultural_adaptations || []).length > 0 && (
                    <div>
                      <p className="mb-1 text-xs uppercase tracking-wide text-muted-foreground">Locale Notes</p>
                      <div className="flex flex-wrap gap-2">
                        {(email.cultural_adaptations || []).map((item) => (
                          <Badge key={item} variant="outline">{item}</Badge>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      </SheetBody>
    </Sheet>
  );
}

interface SSEState {
  stage: string | null;
  huntRound: number;
  leadsCount: number;
  status: "connecting" | "running" | "completed" | "failed";
  error: string | null;
}

interface ActivityEntry {
  id: number;
  time: string;
  message: string;
  type: "info" | "success" | "error";
}

// Per-stage accumulated detail data
interface StageDataMap {
  insight?: Record<string, unknown>;
  keyword_gen?: { keywords: string[]; hunt_round: number }[];
  search?: { result_count: number; keyword_search_stats: Record<string, unknown>; hunt_round: number }[];
  lead_extract?: { leads_count: number; hunt_round: number }[];
  evaluate?: { round_feedback: Record<string, unknown> | null; hunt_round: number }[];
}

const STAGE_ICONS: Record<string, React.ReactNode> = {
  insight: <Brain className="h-4 w-4" />,
  keyword_gen: <FileText className="h-4 w-4" />,
  search: <Search className="h-4 w-4" />,
  lead_extract: <Users className="h-4 w-4" />,
  evaluate: <CheckCircle2 className="h-4 w-4" />,
};

const STAGE_LABELS: Record<string, string> = {
  insight: "分析企业画像",
  keyword_gen: "生成关键词",
  search: "搜索 Google Maps",
  lead_extract: "提取线索",
  evaluate: "评估结果",
};

const STAGES = ["insight", "keyword_gen", "search", "lead_extract", "evaluate"];

// ── Stage Detail Panel ────────────────────────────────────────────────
function StageDetailPanel({ stage, data }: { stage: string; data: StageDataMap }) {
  if (stage === "insight") {
    const ins = data.insight;
    if (!ins || Object.keys(ins).length === 0) {
      return <p className="text-sm text-muted-foreground">当前任务暂无企业画像数据。</p>;
    }
    return (
      <div className="space-y-3">
        <h4 className="font-semibold flex items-center gap-2">
          <Brain className="h-4 w-4" /> 企业画像
        </h4>
        {typeof ins.company_name === "string" && ins.company_name && (
          <p className="text-sm"><span className="font-medium">企业：</span> {ins.company_name}</p>
        )}
        {typeof ins.summary === "string" && ins.summary && (
          <p className="text-sm text-muted-foreground">{ins.summary}</p>
        )}
        {Array.isArray(ins.products) && ins.products.length > 0 && (
          <div>
            <p className="text-xs font-medium text-muted-foreground mb-1">产品</p>
            <div className="flex flex-wrap gap-1.5">
              {(ins.products as string[]).map((p, i) => (
                <Badge key={i} variant="outline">{p}</Badge>
              ))}
            </div>
          </div>
        )}
        {Array.isArray(ins.industries) && ins.industries.length > 0 && (
          <div>
            <p className="text-xs font-medium text-muted-foreground mb-1">行业</p>
            <div className="flex flex-wrap gap-1.5">
              {(ins.industries as string[]).map((ind, i) => (
                <Badge key={i} variant="secondary">{ind}</Badge>
              ))}
            </div>
          </div>
        )}
        {Array.isArray(ins.recommended_keywords_seed) && ins.recommended_keywords_seed.length > 0 && (
          <div>
            <p className="text-xs font-medium text-muted-foreground mb-1">推荐关键词</p>
            <div className="flex flex-wrap gap-1.5">
              {(ins.recommended_keywords_seed as string[]).map((kw, i) => (
                <Badge key={i} variant="outline" className="text-xs">{kw}</Badge>
              ))}
            </div>
          </div>
        )}
        {typeof ins.target_customer_profile === "string" && ins.target_customer_profile && (
          <div>
            <p className="text-xs font-medium text-muted-foreground mb-1">目标客户</p>
            <p className="text-sm">{ins.target_customer_profile}</p>
          </div>
        )}
      </div>
    );
  }

  if (stage === "keyword_gen") {
    if (!data.keyword_gen || data.keyword_gen.every(r => r.keywords.length === 0)) {
      return <p className="text-sm text-muted-foreground">当前还没有生成关键词。</p>;
    }
    return (
      <div className="space-y-3">
        <h4 className="font-semibold flex items-center gap-2">
          <Tag className="h-4 w-4" /> 已生成关键词
        </h4>
        {data.keyword_gen.map((round, i) => (
          <div key={i}>
            <p className="text-xs font-medium text-muted-foreground mb-1">第 {round.hunt_round} 轮</p>
            <div className="flex flex-wrap gap-1.5">
              {round.keywords.map((kw, j) => (
                <Badge key={j} variant="outline">{kw}</Badge>
              ))}
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (stage === "search") {
    if (!data.search) return <p className="text-sm text-muted-foreground">当前暂无搜索数据。</p>;
    return (
      <div className="space-y-3">
        <h4 className="font-semibold flex items-center gap-2">
          <Search className="h-4 w-4" /> 搜索结果
        </h4>
        {data.search.map((round, i) => (
          <div key={i} className="space-y-2">
            <p className="text-sm">
              <span className="font-medium">第 {round.hunt_round} 轮：</span>
              找到 {round.result_count} 个结果
            </p>
            {Object.keys(round.keyword_search_stats).length > 0 && (
              <div className="rounded-md border overflow-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b bg-muted/50">
                      <th className="h-8 px-3 text-left font-medium">关键词</th>
                      <th className="h-8 px-3 text-left font-medium">结果数</th>
                      <th className="h-8 px-3 text-left font-medium">线索数</th>
                      <th className="h-8 px-3 text-left font-medium">效果</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(round.keyword_search_stats).map(([kw, stats]) => {
                      const s = stats as Record<string, number>;
                      const leads = s.leads_found ?? 0;
                      const eff = leads > 3 ? "high" : leads > 0 ? "medium" : "low";
                      return (
                        <tr key={kw} className="border-b">
                          <td className="p-3 font-medium max-w-[200px] truncate">{kw}</td>
                          <td className="p-3">{s.result_count ?? 0}</td>
                          <td className="p-3">{leads}</td>
                          <td className="p-3">
                            <Badge variant={eff === "high" ? "success" : eff === "medium" ? "warning" : "secondary"}>
                              {eff === "high" ? "高" : eff === "medium" ? "中" : "低"}
                            </Badge>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        ))}
      </div>
    );
  }

  if (stage === "lead_extract") {
    if (!data.lead_extract) return <p className="text-sm text-muted-foreground">当前暂无线索提取数据。</p>;
    return (
      <div className="space-y-2">
        <h4 className="font-semibold flex items-center gap-2">
          <Users className="h-4 w-4" /> 线索提取
        </h4>
        {data.lead_extract.map((round, i) => (
          <p key={i} className="text-sm">
            <span className="font-medium">第 {round.hunt_round} 轮：</span>
            累计提取 {round.leads_count} 条线索
          </p>
        ))}
      </div>
    );
  }

  if (stage === "evaluate") {
    if (!data.evaluate) return <p className="text-sm text-muted-foreground">当前暂无评估数据。</p>;
    return (
      <div className="space-y-3">
        <h4 className="font-semibold flex items-center gap-2">
          <BarChart3 className="h-4 w-4" /> 轮次评估
        </h4>
        {data.evaluate.map((round, i) => {
          const fb = round.round_feedback as Record<string, unknown> | null;
          if (!fb) return null;
          const newLeads = Number(fb.new_leads_this_round ?? 0);
          const totalLeads = Number(fb.total_leads ?? 0);
          const target = Number(fb.target ?? 200);
          const bestKw = (fb.best_keywords as string[]) || [];
          const worstKw = (fb.worst_keywords as string[]) || [];
          return (
            <div key={i} className="space-y-2 rounded-md border p-3">
              <div className="flex items-center gap-4 text-sm">
                <span className="font-medium">第 {Number(fb.round ?? round.hunt_round)} 轮</span>
                <span>新增 {newLeads} 条线索</span>
                <span className="text-muted-foreground">累计 {totalLeads}/{target}</span>
              </div>
              {bestKw.length > 0 && (
                <div>
                  <p className="text-xs font-medium text-green-700 mb-1">表现最佳关键词</p>
                  <div className="flex flex-wrap gap-1">
                    {bestKw.map((kw, j) => (
                      <Badge key={j} variant="success" className="text-xs">{kw}</Badge>
                    ))}
                  </div>
                </div>
              )}
              {worstKw.length > 0 && (
                <div>
                  <p className="text-xs font-medium text-red-600 mb-1">表现较弱关键词</p>
                  <div className="flex flex-wrap gap-1">
                    {worstKw.map((kw, j) => (
                      <Badge key={j} variant="destructive" className="text-xs">{kw}</Badge>
                    ))}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    );
  }

  return <p className="text-sm text-muted-foreground">当前阶段暂无可展示数据。</p>;
}

export function HuntDetailPage() {
  const { huntId } = useParams({ from: "/hunts/$huntId" });
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [sse, setSSE] = useState<SSEState>({
    stage: null, huntRound: 0, leadsCount: 0, status: "connecting", error: null,
  });
  const [showResult, setShowResult] = useState(false);
  const [initialLoaded, setInitialLoaded] = useState(false);
  const [selectedLead, setSelectedLead] = useState<Lead | null>(null);
  const [activityLog, setActivityLog] = useState<ActivityEntry[]>([]);
  const activityIdRef = useRef(0);
  const logEndRef = useRef<HTMLDivElement>(null);
  const [stageData, setStageData] = useState<StageDataMap>({});
  const [selectedStage, setSelectedStage] = useState<string | null>(null);
  const [showContinueJobDialog, setShowContinueJobDialog] = useState(false);
  const [activeTab, setActiveTab] = useState<"overview" | "leads" | "emails" | "email-log">("overview");
  const [realtimeLeads, setRealtimeLeads] = useState<Lead[]>([]);
  const [emailFilter, setEmailFilter] = useState<"all" | "approved" | "needs_review">("all");
  const [previewSequence, setPreviewSequence] = useState<EmailSequence | null>(null);
  const [previewSequenceIndex, setPreviewSequenceIndex] = useState<number | null>(null);

  const continueJobMutation = useMutation({
    mutationFn: ({ targetLeadCount, maxRounds, minNewLeadsThreshold, enableEmailCraft, emailTemplateExamples, emailTemplateNotes }: {
      targetLeadCount: number;
      maxRounds: number;
      minNewLeadsThreshold: number;
      enableEmailCraft: boolean;
      emailTemplateExamples: string[];
      emailTemplateNotes: string;
    }) => api.createAutomationJobFromHunt(huntId, {
      target_lead_count: targetLeadCount,
      max_rounds: maxRounds,
      min_new_leads_threshold: minNewLeadsThreshold,
      enable_email_craft: enableEmailCraft,
      email_template_examples: emailTemplateExamples,
      email_template_notes: emailTemplateNotes,
    }),
    onSuccess: async (job) => {
      setShowContinueJobDialog(false);
      await queryClient.invalidateQueries({ queryKey: ["automation-jobs"] });
      navigate({ to: "/automation/$jobId", params: { jobId: job.job_id } });
    },
  });
  const emailDecisionMutation = useMutation({
    mutationFn: ({ sequenceIndex, decision }: { sequenceIndex: number; decision: "approved" | "rejected" }) =>
      api.decideEmailSequence(huntId, sequenceIndex, { decision }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["hunt-result", huntId] });
    },
  });
  const sendDraftMutation = useMutation({
    mutationFn: ({ sequenceIndex, sequenceNumber }: { sequenceIndex: number; sequenceNumber: number }) =>
      api.sendEmailDraft(huntId, sequenceIndex, { sequence_number: sequenceNumber }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["hunt-result", huntId] });
    },
  });
  const detectRepliesMutation = useMutation({
    mutationFn: ({ sequenceIndex }: { sequenceIndex: number }) =>
      api.detectReplies(huntId, sequenceIndex),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["hunt-result", huntId] });
    },
  });

  // Auto-scroll activity log to bottom
  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [activityLog]);

  const { data: result } = useQuery({
    queryKey: ["hunt-result", huntId],
    queryFn: () => api.getHuntResult(huntId),
    enabled: initialLoaded,
    refetchInterval: sse.status === "running" ? 3000 : false,
    retry: false,
  });
  const { data: automationJob } = useQuery({
    queryKey: ["automation-job-by-hunt", huntId],
    queryFn: () => api.getAutomationJobByHunt(huntId),
    retry: false,
  });
  const { data: campaigns } = useQuery({
    queryKey: ["email-campaigns", huntId],
    queryFn: () => api.listEmailCampaigns(huntId),
    enabled: !!huntId,
    refetchInterval: 5000,
    retry: false,
  });

  // Merge persisted partial leads + SSE pushes so leads tab updates immediately.
  const displayLeads = useMemo(() => {
    const merged = new Map<string, Lead>();
    for (const lead of (result?.leads || []) as Lead[]) {
      merged.set(getLeadKey(lead), lead);
    }
    for (const lead of realtimeLeads) {
      merged.set(getLeadKey(lead), lead);
    }
    return Array.from(merged.values());
  }, [result?.leads, realtimeLeads]);

  const leadsTabCount = displayLeads.length || sse.leadsCount;
  const keywordCount = result?.used_keywords?.length ?? 0;
  const roundCount = result?.hunt_round ?? sse.huntRound;
  const emailSequences = useMemo(
    () => result?.email_sequences || [],
    [result?.email_sequences],
  );
  const emailCount = emailSequences.length;
  const approvedEmailCount = useMemo(
    () => emailSequences.filter((seq) => isSequenceReadyForSend(seq)).length,
    [emailSequences],
  );
  const reviewNeededCount = emailCount - approvedEmailCount;
  const filteredEmailSequences = useMemo(() => {
    if (emailFilter === "approved") {
      return emailSequences
        .map((seq, index) => ({ seq, index }))
        .filter(({ seq }) => isSequenceReadyForSend(seq));
    }
    if (emailFilter === "needs_review") {
      return emailSequences
        .map((seq, index) => ({ seq, index }))
        .filter(({ seq }) => !isSequenceReadyForSend(seq));
    }
    return emailSequences.map((seq, index) => ({ seq, index }));
  }, [emailFilter, emailSequences]);
  const emailLogRows = useMemo(() => {
    return emailSequences.flatMap((seq, sequenceIndex) => {
      const lead = asRecord(seq.lead);
      const replyDetection = asRecord(seq.reply_detection);
      const replyCount = Number(replyDetection.reply_count || 0);
      return (seq.emails || []).map((email) => ({
        sequenceIndex,
        companyName: String(lead.company_name || "Unknown"),
        locale: seq.locale || "en_US",
        sequenceNumber: Number(email.sequence_number || 0),
        emailType: formatEmailType(String(email.email_type || "")),
        subject: String(email.subject || ""),
        sendStatus: String(email.send_status || ""),
        sentAt: String(email.sent_at || ""),
        sentTo: String(email.sent_to || ""),
        queueReason: String((email as unknown as Record<string, unknown>).queue_reason || ""),
        replyCount,
        replyStatus: replyCount > 0 ? "已回复" : "未回复",
      }));
    });
  }, [emailSequences]);
  const sentLogCount = emailLogRows.filter((row) => row.sendStatus === "sent").length;
  const queuedLogCount = emailLogRows.filter((row) => row.sendStatus === "queued").length;
  const failedLogCount = emailLogRows.filter((row) => row.sendStatus === "failed").length;
  const repliedLogCount = emailLogRows.filter((row) => row.replyCount > 0).length;
  const activeCampaignCount = useMemo(
    () => (campaigns || []).filter((item) => item.campaign.status === "active").length,
    [campaigns],
  );
  const totalCampaignSequenceCount = useMemo(
    () => (campaigns || []).reduce((sum, item) => sum + (item.sequence_count || 0), 0),
    [campaigns],
  );

  const { data: costData } = useQuery({
    queryKey: ["hunt-cost", huntId],
    queryFn: () => api.getHuntCost(huntId),
    enabled: showResult || sse.status === "failed" || sse.status === "running",
    refetchInterval: sse.status === "running" ? 10000 : false,
    retry: false,
  });

  // Step 1: Fetch hunt status first to decide whether to use SSE
  useEffect(() => {
    let cancelled = false;
    api.getHuntStatus(huntId).then((status) => {
      if (cancelled) return;
      if (status.status === "completed") {
        setSSE({
          stage: "evaluate",
          huntRound: status.hunt_round,
          leadsCount: status.leads_count,
          status: "completed",
          error: null,
        });
        setShowResult(true);
        setInitialLoaded(true);
      } else if (status.status === "failed") {
        setSSE({
          stage: status.current_stage,
          huntRound: status.hunt_round,
          leadsCount: status.leads_count,
          status: "failed",
          error: status.error,
        });
        setInitialLoaded(true);
      } else {
        // Hunt is still running/pending — use SSE for live updates
        setInitialLoaded(true);
      }
    }).catch(() => {
      // Status endpoint failed — still try SSE
      if (!cancelled) setInitialLoaded(true);
    });
    return () => { cancelled = true; };
  }, [huntId]);

  // Step 2: Only connect SSE if hunt is still running (not completed/failed)
  useEffect(() => {
    if (!initialLoaded) return;
    if (sse.status === "completed" || sse.status === "failed") return;

    const es = api.streamHunt(huntId);

    es.addEventListener("stage_change", (e) => {
      const d = JSON.parse(e.data);
      setSSE((prev) => ({ ...prev, stage: d.stage, huntRound: d.hunt_round, status: "running" }));
    });

    es.addEventListener("progress", (e) => {
      const d = JSON.parse(e.data);
      setSSE((prev) => ({ ...prev, leadsCount: d.leads_count }));
    });

    es.addEventListener("round_change", (e) => {
      const d = JSON.parse(e.data);
      setSSE((prev) => ({ ...prev, huntRound: d.hunt_round }));
    });

    es.addEventListener("completed", (e) => {
      const d = JSON.parse(e.data);
      setSSE((prev) => ({
        ...prev, status: "completed", leadsCount: d.leads_count, stage: "evaluate",
      }));
      setShowResult(true);
      es.close();
    });

    es.addEventListener("failed", (e) => {
      const d = JSON.parse(e.data);
      setSSE((prev) => ({ ...prev, status: "failed", error: d.error }));
      es.close();
    });

    es.addEventListener("stage_data", (e) => {
      const d = JSON.parse(e.data);
      const stage = d.stage as string;
      setStageData((prev) => {
        const next = { ...prev };
        if (stage === "insight") {
          next.insight = d.insight;
        } else if (stage === "keyword_gen") {
          next.keyword_gen = [...(prev.keyword_gen || []), { keywords: d.keywords, hunt_round: d.hunt_round }];
        } else if (stage === "search") {
          next.search = [...(prev.search || []), { result_count: d.result_count, keyword_search_stats: d.keyword_search_stats, hunt_round: d.hunt_round }];
        } else if (stage === "lead_extract") {
          next.lead_extract = [...(prev.lead_extract || []), { leads_count: d.leads_count, hunt_round: d.hunt_round }];
        } else if (stage === "evaluate") {
          next.evaluate = [...(prev.evaluate || []), { round_feedback: d.round_feedback, hunt_round: d.hunt_round }];
        }
        return next;
      });
    });

    es.addEventListener("lead_progress", (e) => {
      const d = JSON.parse(e.data);
      const now = new Date().toLocaleTimeString();
      let msg = "";
      let type: ActivityEntry["type"] = "info";
      const ev = d.event as string;
      if (ev === "classify") {
        msg = `Classified ${d.total} URLs: ${d.company_sites} company sites, ${d.platform} platforms, ${d.linkedin} LinkedIn, ${d.content_pages} content pages`;
      } else if (ev === "deep_scrape_start") {
        msg = `Starting deep-scrape of ${d.total_urls} URLs...`;
      } else if (ev === "scraping") {
        msg = `Scraping ${d.domain}...`;
      } else if (ev === "lead_found") {
        msg = `✓ ${d.company_name} (${d.domain}) — ${d.emails} emails, ${d.phones} phones, score ${((d.match_score ?? 0) * 100).toFixed(0)}%`;
        type = "success";
        // Add lead to realtime list immediately
        if (d.lead) {
          setRealtimeLeads((prev) => [...prev, d.lead as Lead]);
        }
      } else if (ev === "scrape_done" && !d.valid) {
        msg = `✗ ${d.domain} — ${d.reason === "not_a_lead" ? "not a valid lead" : d.reason}`;
      } else if (ev === "scrape_error") {
        msg = `✗ ${d.domain} — error: ${d.error}`;
        type = "error";
      } else {
        msg = `${ev}: ${d.domain || JSON.stringify(d)}`;
      }
      if (msg) {
        activityIdRef.current += 1;
        setActivityLog((prev) => [...prev.slice(-99), { id: activityIdRef.current, time: now, message: msg, type }]);
      }
    });

    es.addEventListener("heartbeat", (e) => {
      const d = JSON.parse(e.data);
      if (d.status === "completed") {
        setSSE((prev) => ({ ...prev, status: "completed", leadsCount: d.leads_count ?? prev.leadsCount, stage: "evaluate" }));
        setShowResult(true);
        es.close();
        return;
      }
      if (d.status === "failed") {
        setSSE((prev) => ({ ...prev, status: "failed", error: "Hunt failed" }));
        es.close();
        return;
      }
      setSSE((prev) => ({ ...prev, status: prev.status === "connecting" ? "running" : prev.status }));
    });

    es.onerror = () => {
      setSSE((prev) => ({ ...prev, status: prev.status === "completed" ? "completed" : "failed", error: "Connection lost" }));
      setShowResult(true);
      es.close();
    };

    return () => es.close();
  }, [huntId, initialLoaded, sse.status]);

  const exportReport = useCallback(() => {
    const ins = stageData.insight;
    const kwRounds = stageData.keyword_gen;
    if (!ins && !kwRounds) return;

    const lines: string[] = [];
    const now = new Date().toLocaleString();
    lines.push("=".repeat(60));
    lines.push("AI HUNTER — INSIGHT & KEYWORD REPORT");
    lines.push(`Hunt ID : ${huntId}`);
    lines.push(`Exported: ${now}`);
    lines.push("=".repeat(60));

    if (ins) {
      lines.push("");
      lines.push("── COMPANY INSIGHT ──────────────────────────────────────");
      if (ins.company_name) lines.push(`Company  : ${ins.company_name}`);
      if (ins.summary)      lines.push(`Summary  : ${ins.summary}`);
      if (Array.isArray(ins.products) && ins.products.length > 0)
        lines.push(`Products : ${(ins.products as string[]).join(", ")}`);
      if (Array.isArray(ins.industries) && ins.industries.length > 0)
        lines.push(`Industries: ${(ins.industries as string[]).join(", ")}`);
      if (ins.target_customer_profile)
        lines.push(`Target Customer:\n  ${ins.target_customer_profile}`);
      if (Array.isArray(ins.value_propositions) && ins.value_propositions.length > 0)
        lines.push(`Value Props:\n  ${(ins.value_propositions as string[]).map((v) => `• ${v}`).join("\n  ")}`);
      if (Array.isArray(ins.negative_targeting_criteria) && ins.negative_targeting_criteria.length > 0)
        lines.push(`Negative Criteria:\n  ${(ins.negative_targeting_criteria as string[]).map((v) => `• ${v}`).join("\n  ")}`);
      if (Array.isArray(ins.recommended_keywords_seed) && ins.recommended_keywords_seed.length > 0)
        lines.push(`Seed Keywords: ${(ins.recommended_keywords_seed as string[]).join(", ")}`);
      if (Array.isArray(ins.recommended_regions) && ins.recommended_regions.length > 0)
        lines.push(`Target Regions: ${(ins.recommended_regions as string[]).join(", ")}`);
    }

    if (kwRounds && kwRounds.length > 0) {
      lines.push("");
      lines.push("── GENERATED KEYWORDS ───────────────────────────────────");
      const allKw: string[] = [];
      kwRounds.forEach((round) => {
        lines.push(`Round ${round.hunt_round}: ${round.keywords.join(", ")}`);
        allKw.push(...round.keywords);
      });
      const unique = [...new Set(allKw)];
      lines.push("");
      lines.push(`Total unique keywords: ${unique.length}`);
      lines.push(unique.join("\n"));
    }

    lines.push("");
    lines.push("=".repeat(60));

    const blob = new Blob([lines.join("\n")], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `hunt-${huntId.slice(0, 8)}-report.txt`;
    a.click();
    URL.revokeObjectURL(url);
  }, [stageData, huntId]);

  const exportCSV = useCallback(() => {
    if (!displayLeads.length) return;
    const headers = [
      "company_name", "website", "industry", "country_code",
      "address", "description", "contact_person",
      "emails", "phone_numbers",
      "linkedin", "facebook", "twitter", "instagram", "youtube", "whatsapp", "wechat",
      "business_types",
      "decision_makers_count", "decision_maker_names", "decision_maker_titles",
      "decision_maker_emails", "decision_maker_email_statuses", "decision_maker_linkedins", "decision_maker_sources",
      "customs_data", "customs_records",
      "fit_score", "contactability_score", "customs_score", "priority_tier",
      "customer_role", "competitor_risk", "evidence_strength", "risk_flags", "evidence",
      "maps_title", "maps_website", "maps_type", "maps_types", "maps_address", "maps_phone", "maps_description", "maps_email",
      "source", "source_keyword", "match_score",
    ];
    const escapeCSV = (v: string) => v.includes(",") || v.includes('"') || v.includes("\n") ? `"${v.replace(/"/g, '""')}"` : v;
    const rows = displayLeads.map((l: Record<string, unknown>) =>
      headers.map((h) => {
        if (h === "linkedin" || h === "facebook" || h === "twitter" || h === "instagram" || h === "youtube" || h === "whatsapp" || h === "wechat") {
          const social = l.social_media as Record<string, string> | undefined;
          return escapeCSV(String(social?.[h] ?? ""));
        }
        if (h === "business_types") {
          const types = l.business_types as string[] | undefined;
          return escapeCSV(types ? types.join("; ") : "");
        }
        if (h.startsWith("decision_maker") || h === "decision_makers_count") {
          const dms = (l.decision_makers as Array<{name?: string; title?: string; email?: string; linkedin?: string; source_url?: string}> | undefined) || [];
          if (h === "decision_makers_count") return escapeCSV(String(dms.length));
          if (h === "decision_maker_names") return escapeCSV(dms.map((dm) => dm.name || "").filter(Boolean).join("; "));
          if (h === "decision_maker_titles") return escapeCSV(dms.map((dm) => dm.title || "").filter(Boolean).join("; "));
          if (h === "decision_maker_emails") return escapeCSV(dms.map((dm) => {
            const email = dm.email || "";
            return isGenericDecisionMakerMailbox(email) ? "" : normalizeDecisionMakerEmail(email);
          }).filter(Boolean).join("; "));
          if (h === "decision_maker_email_statuses") return escapeCSV(dms.map((dm) => getDecisionMakerEmailStatus(dm.email || "")).join("; "));
          if (h === "decision_maker_linkedins") return escapeCSV(dms.map((dm) => dm.linkedin || "").filter(Boolean).join("; "));
          if (h === "decision_maker_sources") return escapeCSV(dms.map((dm) => dm.source_url || "").filter(Boolean).join("; "));
        }
        if (h === "customs_data") {
          return escapeCSV(String(l.customs_data ?? ""));
        }
        if (h === "customs_records") {
          const records = (l.customs_records as Array<Record<string, unknown>> | undefined) || [];
          return escapeCSV(records.map((record) => {
            const provider = String(record.provider ?? "");
            const period = String(record.period ?? "");
            const direction = String(record.trade_direction ?? "");
            const countries = Array.isArray(record.partner_countries) ? (record.partner_countries as string[]).join("/") : "";
            const hsCodes = Array.isArray(record.hs_codes) ? (record.hs_codes as string[]).join("/") : "";
            const products = Array.isArray(record.product_clues) ? (record.product_clues as string[]).join("/") : "";
            const url = String(record.source_url ?? "");
            return [provider, period, direction, countries, hsCodes, products, url].filter(Boolean).join(" | ");
          }).join("; "));
        }
        if (h === "risk_flags") {
          const flags = (l.risk_flags as string[] | undefined) || [];
          return escapeCSV(flags.join("; "));
        }
        if (h === "evidence") {
          const ev = (l.evidence as Array<{claim?: string; source_url?: string}> | undefined) || [];
          return escapeCSV(ev.map((x) => `${x.claim || ""}${x.source_url ? ` @ ${x.source_url}` : ""}`).join("; "));
        }
        if (h.startsWith("maps_")) {
          const md = (l.maps_data as Record<string, unknown>) || {};
          if (h === "maps_title") return escapeCSV(String(md.title ?? ""));
          if (h === "maps_website") return escapeCSV(String(md.website ?? ""));
          if (h === "maps_type") return escapeCSV(String(md.type ?? ""));
          if (h === "maps_types") return escapeCSV(Array.isArray(md.types) ? (md.types as string[]).join("; ") : "");
          if (h === "maps_address") return escapeCSV(String(md.address ?? ""));
          if (h === "maps_phone") return escapeCSV(String(md.phoneNumber ?? md.phone_number ?? ""));
          if (h === "maps_description") return escapeCSV(String(md.description ?? ""));
          if (h === "maps_email") return escapeCSV(String(md.email ?? ""));
        }
        const v = l[h];
        return escapeCSV(Array.isArray(v) ? v.join("; ") : String(v ?? ""));
      }).join(",")
    );
    const csv = [headers.join(","), ...rows].join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `hunt-${huntId.slice(0, 8)}-leads.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }, [displayLeads, huntId]);

  // Reconstruct stageData from result API for completed hunts
  useEffect(() => {
    if (!result) return;
    setStageData((prev) => {
      const next: StageDataMap = { ...prev };
      // Always populate from result (SSE data takes priority if richer)
      if (!prev.insight) next.insight = result.insight ?? {};
      if (!prev.keyword_gen) {
        next.keyword_gen = result.used_keywords.length > 0
          ? [{ keywords: result.used_keywords, hunt_round: result.hunt_round }]
          : [{ keywords: [], hunt_round: result.hunt_round }];
      }
      if (!prev.search) {
        next.search = [{ result_count: result.search_result_count, keyword_search_stats: result.keyword_search_stats, hunt_round: result.hunt_round }];
      }
      if (!prev.lead_extract) {
        next.lead_extract = [{ leads_count: result.leads.length, hunt_round: result.hunt_round }];
      }
      if (result.round_feedback && !prev.evaluate) {
        next.evaluate = [{ round_feedback: result.round_feedback, hunt_round: result.hunt_round }];
      }
      return next;
    });
  }, [result]);

  const currentStageIdx = sse.stage ? STAGES.indexOf(sse.stage) : -1;

  return (
    <div className="space-y-8">
      <div className="flex items-center gap-4">
        <Link to="/">
          <Button variant="ghost" size="icon"><ArrowLeft className="h-4 w-4" /></Button>
        </Link>
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Hunt {huntId.slice(0, 8)}...</h1>
          <p className="text-muted-foreground text-sm">
            {sse.status === "completed" ? "已完成" : sse.status === "failed" ? "失败" : "运行中"}
          </p>
        </div>
        <div className="ml-auto flex items-center gap-3">
          <Badge variant={sse.status === "completed" ? "success" : sse.status === "failed" ? "destructive" : "warning"}>
            {sse.status}
          </Badge>
          {(sse.status === "completed" || sse.status === "failed") && (
            <Button
              size="sm"
              variant="outline"
              onClick={() => setShowContinueJobDialog(true)}
              className="gap-2"
            >
              <RefreshCw className="h-4 w-4" />
              继续挖掘
            </Button>
          )}
        </div>
      </div>

      <ContinueJobDialog
        open={showContinueJobDialog}
        onClose={() => setShowContinueJobDialog(false)}
        onConfirm={(targetLeadCount, maxRounds, minNewLeadsThreshold, enableEmailCraft, emailTemplateExamples, emailTemplateNotes) =>
          continueJobMutation.mutate({
            targetLeadCount,
            maxRounds,
            minNewLeadsThreshold,
            enableEmailCraft,
            emailTemplateExamples,
            emailTemplateNotes,
          })
        }
        isLoading={continueJobMutation.isPending}
        currentLeads={sse.leadsCount || (result?.leads?.length ?? 0)}
      />

      {/* Tab switcher */}
      <div className="flex gap-1 border-b">
        {(["overview", "leads", "emails", "email-log"] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === tab
                ? "border-primary text-primary"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            {tab === "overview"
              ? "总览"
              : tab === "leads"
                ? `线索${leadsTabCount > 0 ? ` (${leadsTabCount})` : ""}`
                : tab === "emails"
                  ? `邮件${emailCount > 0 ? ` (${emailCount})` : ""}`
                : `邮件日志${emailLogRows.length > 0 ? ` (${emailLogRows.length})` : ""}`}
          </button>
        ))}
      </div>

      {activeTab === "overview" && (<>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">队列任务</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="text-2xl font-semibold">{automationJob?.status || "-"}</p>
                <p className="text-xs text-muted-foreground">
                  {automationJob ? `尝试 ${automationJob.attempt_count} 次` : "当前 hunt 未绑定 queue job"}
                </p>
              </div>
              {automationJob && (
                <Link to="/automation/$jobId" params={{ jobId: automationJob.job_id }}>
                  <Button variant="outline" size="sm">查看任务</Button>
                </Link>
              )}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">当前阶段</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-semibold">{automationJob?.hunt_stage || sse.stage || "-"}</p>
            <p className="text-xs text-muted-foreground">
              {automationJob?.hunt_status ? `Hunt 状态：${automationJob.hunt_status}` : "由 consumer 执行搜索、抽取、评估和邮件生成"}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Campaign</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-semibold">{activeCampaignCount}</p>
            <p className="text-xs text-muted-foreground">
              {(campaigns || []).length > 0
                ? `共 ${(campaigns || []).length} 个 campaign，覆盖 ${totalCampaignSequenceCount} 条发送序列`
                : "当前还没有已创建的 campaign"}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">发送队列</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-semibold">{queuedLogCount}</p>
            <p className="text-xs text-muted-foreground">
              已发送 {sentLogCount} · 失败 {failedLogCount} · 回复 {repliedLogCount}
            </p>
          </CardContent>
        </Card>
      </div>

      {automationJob?.last_error && (
        <Card className="border-amber-300">
          <CardContent className="py-4 text-sm text-amber-700 dark:text-amber-300">
            队列任务最近错误：{automationJob.last_error}
          </CardContent>
        </Card>
      )}

      {(campaigns || []).length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Campaign 运营状态</CardTitle>
            <CardDescription>当前 hunt 关联的自动发送任务，会由持久化发送队列和 scheduler 消费。</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {(campaigns || []).map((item) => (
              <div key={item.campaign.id} className="rounded-md border p-4">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <p className="font-medium">{item.campaign.name}</p>
                    <p className="text-xs text-muted-foreground">
                      状态 {item.campaign.status} · 语言 {item.campaign.default_language} · 语气 {item.campaign.tone}
                    </p>
                  </div>
                  <div className="text-xs text-muted-foreground">
                    发送 {item.sent_count} · 待发 {item.pending_count} · 失败 {item.failed_count}
                  </div>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Stage Progress — clickable steps */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle className="text-lg">流程进度</CardTitle>
            <CardDescription>第 {sse.huntRound} 轮 · 已找到 {sse.leadsCount} 条线索</CardDescription>
          </div>
          {(stageData.insight || stageData.keyword_gen) && (
            <Button variant="outline" size="sm" onClick={exportReport} className="gap-2 shrink-0">
              <Download className="h-4 w-4" />
              导出报告
            </Button>
          )}
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center gap-2">
            {STAGES.map((stage, i) => {
              const isActive = i === currentStageIdx;
              const isDone = i < currentStageIdx || sse.status === "completed";
              const hasData = !!(stageData as Record<string, unknown>)[stage];
              const isClickable = isDone || isActive || hasData;
              const isSelected = selectedStage === stage;
              return (
                <div key={stage} className="flex items-center gap-2 flex-1">
                  <button
                    onClick={() => isClickable && setSelectedStage(isSelected ? null : stage)}
                    disabled={!isClickable}
                    className={`flex items-center gap-1.5 px-3 py-2 rounded-md text-xs font-medium w-full justify-center transition-all ${
                      isSelected ? "ring-2 ring-primary ring-offset-1 " : ""
                    }${
                      isActive ? "bg-primary text-primary-foreground" :
                      isDone ? "bg-green-100 text-green-800" :
                      "bg-muted text-muted-foreground"
                    } ${isClickable ? "cursor-pointer hover:opacity-80" : "cursor-default"}`}
                  >
                    {isActive && sse.status === "running" ? (
                      <Loader2 className="h-3 w-3 animate-spin" />
                    ) : isDone ? (
                      <CheckCircle2 className="h-3 w-3" />
                    ) : (
                      STAGE_ICONS[stage]
                    )}
                    <span className="hidden sm:inline">{STAGE_LABELS[stage]}</span>
                    {isClickable && (
                      <ChevronDown className={`h-3 w-3 transition-transform ${isSelected ? "rotate-180" : ""}`} />
                    )}
                  </button>
                  {i < STAGES.length - 1 && <div className={`h-px w-4 flex-shrink-0 ${isDone ? "bg-green-400" : "bg-border"}`} />}
                </div>
              );
            })}
          </div>

          {/* Expandable detail panel */}
          {selectedStage && (
            <div className="rounded-lg border bg-muted/30 p-4 animate-in slide-in-from-top-2 duration-200">
              <StageDetailPanel stage={selectedStage} data={stageData} />
            </div>
          )}
        </CardContent>
      </Card>

      {/* Activity Log — shown while running */}
      {activityLog.length > 0 && (
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center gap-2">
              <Activity className="h-4 w-4 text-muted-foreground" />
              <CardTitle className="text-lg">活动日志</CardTitle>
            </div>
            <CardDescription>实时显示提取进度</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-48 overflow-y-auto rounded-md border bg-muted/30 p-3 font-mono text-xs space-y-1">
              {activityLog.map((entry) => (
                <div key={entry.id} className={`flex gap-2 ${
                  entry.type === "success" ? "text-green-600" :
                  entry.type === "error" ? "text-red-500" :
                  "text-muted-foreground"
                }`}>
                  <span className="text-muted-foreground/60 flex-shrink-0">{entry.time}</span>
                  <span>{entry.message}</span>
                </div>
              ))}
              <div ref={logEndRef} />
            </div>
          </CardContent>
        </Card>
      )}

      {/* Error */}
      {sse.status === "failed" && sse.error && (
        <Card className="border-destructive">
          <CardContent className="flex items-center gap-3 py-4">
            <XCircle className="h-5 w-5 text-destructive" />
            <span className="text-sm text-destructive">{sse.error}</span>
          </CardContent>
        </Card>
      )}

      {/* Cost & Token Usage */}
      {costData?.cost_summary && Object.keys(costData.cost_summary).length > 0 && (() => {
        const cs = costData.cost_summary;
        const agents = Object.entries(cs.by_agent ?? {});
        const searchApis = Object.entries(cs.search_api ?? {});
        const rounds = Object.entries(cs.by_round ?? {});
        return (
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <DollarSign className="h-4 w-4 text-muted-foreground" />
                  <CardTitle className="text-lg">成本与 Token 用量</CardTitle>
                  {sse.status === "running" && (
                    <Badge variant="outline" className="text-xs">实时</Badge>
                  )}
                </div>
                <div className="flex items-center gap-4 text-right">
                  <div>
                    <p className="text-xl font-bold text-primary">${cs.total_cost_usd.toFixed(4)}</p>
                    <p className="text-xs text-muted-foreground">总成本</p>
                  </div>
                  <div>
                    <p className="text-xl font-bold">{cs.total_tokens.toLocaleString()}</p>
                    <p className="text-xs text-muted-foreground">总 Token</p>
                  </div>
                  <div>
                    <p className="text-xl font-bold">{cs.total_llm_calls}</p>
                    <p className="text-xs text-muted-foreground">LLM 调用次数</p>
                  </div>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* By Agent */}
              {agents.length > 0 && (
                <div>
                  <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-2 flex items-center gap-1">
                    <Zap className="h-3 w-3" /> 按智能体统计
                  </p>
                  <div className="rounded-md border overflow-hidden">
                    <table className="w-full text-xs">
                      <thead className="bg-muted/50">
                        <tr>
                          <th className="text-left px-3 py-2 font-medium">智能体</th>
                          <th className="text-right px-3 py-2 font-medium">调用数</th>
                          <th className="text-right px-3 py-2 font-medium">输入 Token</th>
                          <th className="text-right px-3 py-2 font-medium">输出 Token</th>
                          <th className="text-right px-3 py-2 font-medium">成本 (USD)</th>
                        </tr>
                      </thead>
                      <tbody>
                        {agents.sort((a, b) => b[1].cost_usd - a[1].cost_usd).map(([agent, rec]) => (
                          <tr key={agent} className="border-t">
                            <td className="px-3 py-2 font-medium capitalize">{agent.replace(/_/g, " ")}</td>
                            <td className="px-3 py-2 text-right text-muted-foreground">{rec.call_count}</td>
                            <td className="px-3 py-2 text-right text-muted-foreground">{rec.prompt_tokens.toLocaleString()}</td>
                            <td className="px-3 py-2 text-right text-muted-foreground">{rec.completion_tokens.toLocaleString()}</td>
                            <td className="px-3 py-2 text-right font-medium">${rec.cost_usd.toFixed(4)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* By Round + Search API side by side */}
              <div className="grid gap-4 md:grid-cols-2">
                {rounds.length > 0 && (
                  <div>
                    <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-2 flex items-center gap-1">
                      <TrendingUp className="h-3 w-3" /> 按轮次成本
                    </p>
                    <div className="rounded-md border overflow-hidden">
                      <table className="w-full text-xs">
                        <thead className="bg-muted/50">
                          <tr>
                            <th className="text-left px-3 py-2 font-medium">轮次</th>
                            <th className="text-right px-3 py-2 font-medium">Token</th>
                            <th className="text-right px-3 py-2 font-medium">Cost (USD)</th>
                          </tr>
                        </thead>
                        <tbody>
                          {rounds.map(([rnd, v]) => (
                            <tr key={rnd} className="border-t">
                              <td className="px-3 py-2 font-medium">第 {rnd} 轮</td>
                              <td className="px-3 py-2 text-right text-muted-foreground">{v.total_tokens.toLocaleString()}</td>
                              <td className="px-3 py-2 text-right font-medium">${v.cost_usd.toFixed(4)}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
                {searchApis.length > 0 && (
                  <div>
                    <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-2 flex items-center gap-1">
                      <Search className="h-3 w-3" /> 搜索 API 调用
                    </p>
                    <div className="rounded-md border overflow-hidden">
                      <table className="w-full text-xs">
                        <thead className="bg-muted/50">
                          <tr>
                            <th className="text-left px-3 py-2 font-medium">提供方</th>
                            <th className="text-right px-3 py-2 font-medium">调用数</th>
                            <th className="text-right px-3 py-2 font-medium">结果数</th>
                          </tr>
                        </thead>
                        <tbody>
                          {searchApis.map(([provider, rec]) => (
                            <tr key={provider} className="border-t">
                              <td className="px-3 py-2 font-medium capitalize">{provider}</td>
                              <td className="px-3 py-2 text-right text-muted-foreground">{rec.call_count}</td>
                              <td className="px-3 py-2 text-right text-muted-foreground">{rec.result_count}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        );
      })()}
      </>)}

      <LeadDetailSheet
        lead={selectedLead}
        open={selectedLead !== null}
        onClose={() => setSelectedLead(null)}
      />

      <EmailSequencePreviewSheet
        sequence={previewSequence}
        open={previewSequence !== null}
        onClose={() => {
          setPreviewSequence(null);
          setPreviewSequenceIndex(null);
        }}
        onApprove={() => {
          if (previewSequenceIndex === null) return;
          emailDecisionMutation.mutate({ sequenceIndex: previewSequenceIndex, decision: "approved" });
        }}
        onReject={() => {
          if (previewSequenceIndex === null) return;
          emailDecisionMutation.mutate({ sequenceIndex: previewSequenceIndex, decision: "rejected" });
        }}
        onSendDraft={(sequenceNumber) => {
          if (previewSequenceIndex === null) return;
          sendDraftMutation.mutate({ sequenceIndex: previewSequenceIndex, sequenceNumber });
        }}
        onDetectReplies={() => {
          if (previewSequenceIndex === null) return;
          detectRepliesMutation.mutate({ sequenceIndex: previewSequenceIndex });
        }}
        isUpdating={emailDecisionMutation.isPending}
        isSending={sendDraftMutation.isPending}
        isCheckingReplies={detectRepliesMutation.isPending}
      />

      {activeTab === "leads" && (
        <>
          {/* Stats */}
          <div className="grid gap-4 md:grid-cols-4">
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center gap-2">
                  <Users className="h-5 w-5 text-muted-foreground" />
                  <div>
                    <p className="text-2xl font-bold">{displayLeads.length || sse.leadsCount}</p>
                    <p className="text-xs text-muted-foreground">已找到线索</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center gap-2">
                  <Mail className="h-5 w-5 text-muted-foreground" />
                  <div>
                    <p className="text-2xl font-bold">{emailCount}</p>
                    <p className="text-xs text-muted-foreground">已生成邮件序列</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center gap-2">
                  <Search className="h-5 w-5 text-muted-foreground" />
                  <div>
                    <p className="text-2xl font-bold">{keywordCount}</p>
                    <p className="text-xs text-muted-foreground">已用关键词</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center gap-2">
                  <FileText className="h-5 w-5 text-muted-foreground" />
                  <div>
                    <p className="text-2xl font-bold">{roundCount}</p>
                    <p className="text-xs text-muted-foreground">轮次</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Leads Table */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle className="text-lg">线索列表</CardTitle>
                <CardDescription>
                  共 {displayLeads.length} 家企业{sse.status === "running" && realtimeLeads.length > 0 ? "（实时更新）" : ""}，点击行可查看详情
                </CardDescription>
              </div>
              {displayLeads.length > 0 && (
                <Button variant="outline" size="sm" onClick={exportCSV}>
                  <Download className="h-4 w-4 mr-2" />
                  导出 CSV
                </Button>
              )}
            </CardHeader>
            <CardContent>
              {displayLeads.length === 0 ? (
                <p className="text-sm text-muted-foreground text-center py-8">
                  {sse.status === "running" ? "正在提取线索..." : "暂未找到线索。"}
                </p>
              ) : (
                <div className="rounded-md border overflow-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b bg-muted/50">
                        <th className="h-10 px-4 text-left font-medium">企业</th>
                        <th className="h-10 px-4 text-left font-medium hidden md:table-cell">行业</th>
                        <th className="h-10 px-4 text-left font-medium hidden sm:table-cell">国家</th>
                        <th className="h-10 px-4 text-left font-medium">联系信息</th>
                        <th className="h-10 px-4 text-left font-medium">评分</th>
                        <th className="h-10 px-2 text-left font-medium w-8"></th>
                      </tr>
                    </thead>
                    <tbody>
                      {[...displayLeads].sort(compareLeads).map((lead: Lead, i: number) => {
                      const emails = getLeadEmails(lead);
                      const phones = getLeadPhones(lead);
                      const socialCount = Object.keys(getLeadSocial(lead)).length;
                      const businessTypes = (lead.business_types as string[]) || [];
                      const decisionMakers = (lead.decision_makers as Array<unknown>) || [];
                      const customsDataText = typeof lead.customs_data === "string" ? lead.customs_data : "";
                      const customsScore = Number(lead.customs_score || 0);
                      const customerRole = getLeadStr(lead, "customer_role") || "unknown";
                      const competitorRisk = getLeadStr(lead, "competitor_risk") || "low";
                      const riskFlags = Array.isArray(lead.risk_flags) ? (lead.risk_flags as string[]) : [];
                      const visibleRiskFlags = riskFlags.slice(0, 2);
                      const hasCustomsData = hasConcreteCustomsData(customsDataText);
                      return (
                        <tr
                          key={i}
                          onClick={() => setSelectedLead(lead)}
                          className="border-b hover:bg-muted/50 transition-colors cursor-pointer"
                        >
                          <td className="p-4">
                            <div className="flex items-center gap-2">
                              <Building2 className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                              <div className="min-w-0">
                              <div className="font-medium truncate max-w-[200px]">{String(lead.company_name || "—")}</div>
                                {typeof lead.website === "string" && lead.website && (
                                  <div className="text-xs text-muted-foreground truncate max-w-[200px]">
                                    {lead.website.replace(/^https?:\/\/(www\.)?/, "")}
                                  </div>
                                )}
                                <div className="flex items-center gap-1 mt-1 flex-wrap">
                                  {customerRole !== "unknown" && (
                                    <Badge variant="outline" className="text-[10px] px-1.5 py-0 h-5">
                                      {toChineseRole(customerRole)}
                                    </Badge>
                                  )}
                                  {competitorRisk !== "low" && (
                                    <Badge
                                      variant={competitorRisk === "high" ? "destructive" : "warning"}
                                      className="text-[10px] px-1.5 py-0 h-5"
                                    >
                                      {competitorRisk === "high" ? "竞争风险高" : "疑似竞争关系"}
                                    </Badge>
                                  )}
                                  {visibleRiskFlags.map((flag, idx) => (
                                    <Badge key={`${flag}-${idx}`} variant="secondary" className="text-[10px] px-1.5 py-0 h-5">
                                      {flag}
                                    </Badge>
                                  ))}
                                </div>
                              </div>
                            </div>
                          </td>
                          <td className="p-4 text-muted-foreground hidden md:table-cell">
                            <span className="truncate max-w-[120px] block">{String(lead.industry || "—")}</span>
                          </td>
                          <td className="p-4 hidden sm:table-cell">
                            <Badge variant="outline">{String(lead.country_code || "—")}</Badge>
                          </td>
                          <td className="p-4">
                            <div className="flex items-center gap-1.5">
                              {emails.length > 0 && (
                                <span className="inline-flex items-center gap-0.5 text-xs text-muted-foreground" title={`${emails.length} 个邮箱`}>
                                  <Mail className="h-3 w-3" />
                                  <span>{emails.length}</span>
                                </span>
                              )}
                              {phones.length > 0 && (
                                <span className="inline-flex items-center gap-0.5 text-xs text-muted-foreground" title={`${phones.length} 个电话`}>
                                  <Phone className="h-3 w-3" />
                                  <span>{phones.length}</span>
                                </span>
                              )}
                              {socialCount > 0 && (
                                <span className="inline-flex items-center gap-0.5 text-xs text-muted-foreground" title={`${socialCount} 个社媒链接`}>
                                  <Globe className="h-3 w-3" />
                                  <span>{socialCount}</span>
                                </span>
                              )}
                              {decisionMakers.length > 0 && (
                                <span className="inline-flex items-center gap-0.5 text-xs text-blue-600" title={`${decisionMakers.length} 位决策人`}>
                                  <Users className="h-3 w-3" />
                                  <span>{decisionMakers.length}</span>
                                </span>
                              )}
                              {businessTypes.length > 0 && (
                                <span className="inline-flex items-center gap-0.5 text-xs text-purple-600" title={`${businessTypes.length} 个业务类型`}>
                                  <Tag className="h-3 w-3" />
                                </span>
                              )}
                              {hasCustomsData && (
                                <span className="inline-flex items-center gap-0.5 text-xs text-green-600" title={customsScore > 0 ? `海关评分 ${(customsScore * 100).toFixed(0)}%` : "有海关/贸易数据"}>
                                  <BarChart3 className="h-3 w-3" />
                                  {customsScore > 0 && <span>{(customsScore * 100).toFixed(0)}</span>}
                                </span>
                              )}
                              {emails.length === 0 && phones.length === 0 && socialCount === 0 && decisionMakers.length === 0 && businessTypes.length === 0 && !hasCustomsData && (
                                <span className="text-xs text-muted-foreground">—</span>
                              )}
                            </div>
                          </td>
                          <td className="p-4">
                            <Badge variant={Number(lead.fit_score ?? lead.match_score) >= 0.7 ? "success" : Number(lead.fit_score ?? lead.match_score) >= 0.4 ? "warning" : "secondary"}>
                              {(Number(lead.fit_score ?? lead.match_score ?? 0) * 100).toFixed(0)}%
                            </Badge>
                          </td>
                          <td className="p-2">
                            <ChevronRight className="h-4 w-4 text-muted-foreground" />
                          </td>
                        </tr>
                      );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>

        </>
      )}

      {activeTab === "emails" && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">AI 邮件预览</CardTitle>
            <CardDescription>
              {emailCount > 0
                ? `已生成 ${emailCount} 组个性化邮件序列，可在这里预览、审核并进入发送流程。`
                : "当前任务还没有可预览的 AI 邮件。请先在创建任务或继续挖掘时开启 AI 邮件生成。"}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {emailCount > 0 && result ? (
              <>
                <div className="flex flex-wrap gap-2">
                  {([
                    ["all", `全部 (${emailCount})`],
                    ["approved", `可进入发送流程 (${approvedEmailCount})`],
                    ["needs_review", `需复核 (${reviewNeededCount})`],
                  ] as const).map(([value, label]) => (
                    <Button
                      key={value}
                      type="button"
                      variant={emailFilter === value ? "default" : "outline"}
                      size="sm"
                      onClick={() => setEmailFilter(value)}
                    >
                      {label}
                    </Button>
                  ))}
                </div>

                <div className="grid gap-3 md:grid-cols-3">
                  <div className="rounded-md border bg-muted/30 p-3">
                    <p className="text-xs uppercase tracking-wide text-muted-foreground">邮件总数</p>
                    <p className="mt-1 text-2xl font-semibold">{emailCount}</p>
                    <p className="text-xs text-muted-foreground">每组包含 3 封邮件</p>
                  </div>
                  <div className="rounded-md border bg-emerald-50 p-3 dark:bg-emerald-950/20">
                    <p className="text-xs uppercase tracking-wide text-muted-foreground">发送流程候选</p>
                    <p className="mt-1 text-2xl font-semibold text-emerald-700 dark:text-emerald-400">{approvedEmailCount}</p>
                    <p className="text-xs text-muted-foreground">reviewer gate 已通过，可手动发送或创建 campaign</p>
                  </div>
                  <div className="rounded-md border bg-amber-50 p-3 dark:bg-amber-950/20">
                    <p className="text-xs uppercase tracking-wide text-muted-foreground">需人工复核</p>
                    <p className="mt-1 text-2xl font-semibold text-amber-700 dark:text-amber-400">{reviewNeededCount}</p>
                    <p className="text-xs text-muted-foreground">建议预览后再进入发送链路</p>
                  </div>
                </div>

                {filteredEmailSequences.map(({ seq, index }) => {
                  const lead = asRecord(seq.lead);
                  const emails = seq.emails || [];
                  const reviewSummary = asRecord(seq.review_summary);
                  const validationSummary = asRecord(seq.validation_summary);
                  const templateProfile = asRecord(seq.template_profile);
                  const templatePlan = asRecord(seq.template_plan);
                  const templatePerformance = asRecord(seq.template_performance);
                  const reviewStatus = String(reviewSummary.status || "needs_review");
                  const reviewIssues = asStringArray(reviewSummary.issues);
                  const reviewSuggestions = asStringArray(reviewSummary.suggestions);
                  const proofPoints = asStringArray(templatePlan.proof_points);
                  const forbiddenClaims = asStringArray(templatePlan.forbidden_claims);
                  const autoSendEligible = Boolean(seq.auto_send_eligible);
                  const manualReview = asRecord(seq.manual_review);
                  return (
                    <details key={index} className="rounded-md border p-4">
                      <summary className="cursor-pointer font-medium flex items-center gap-2">
                        <Mail className="h-4 w-4 text-muted-foreground" />
                        {String(lead.company_name || `序列 ${index + 1}`)}
                        <div className="ml-auto flex items-center gap-2 pr-6">
                          <Badge variant="outline">{String(seq.locale || "en")}</Badge>
                          <Badge className={reviewStatus === "approved" ? "bg-emerald-600 hover:bg-emerald-600" : "bg-amber-600 hover:bg-amber-600"}>
                            {formatReviewStatus(reviewStatus)}
                          </Badge>
                          {Boolean(manualReview.decision) && (
                            <Badge variant="outline">
                              {String(manualReview.decision) === "approved" ? "人工已批准" : "人工已拦截"}
                            </Badge>
                          )}
                        </div>
                      </summary>
                      <div className="mt-4 space-y-3">
                        <div className="flex flex-wrap gap-2">
                          <Button
                            type="button"
                            size="sm"
                            onClick={() => {
                              setPreviewSequence(seq);
                              setPreviewSequenceIndex(index);
                            }}
                          >
                            预览序列
                          </Button>
                          <div
                            className="inline-flex items-center gap-2 rounded-md border px-3 py-2 text-sm text-muted-foreground"
                            onClick={(e) => e.stopPropagation()}
                          >
                            <CopyButton text={buildSequencePreviewText(seq)} />
                            <span>复制整组</span>
                          </div>
                        </div>

                        <div className="grid gap-3 md:grid-cols-4">
                          <div className="rounded-md border bg-muted/30 p-3">
                            <p className="text-xs uppercase tracking-wide text-muted-foreground">Reviewer Score</p>
                            <p className="mt-1 text-xl font-semibold">{String(reviewSummary.score || "0")}</p>
                          </div>
                          <div className="rounded-md border bg-muted/30 p-3">
                            <p className="text-xs uppercase tracking-wide text-muted-foreground">Blocking Issues</p>
                            <p className="mt-1 text-xl font-semibold">{String(reviewSummary.blocking_issue_count || 0)}</p>
                          </div>
                          <div className="rounded-md border bg-muted/30 p-3">
                            <p className="text-xs uppercase tracking-wide text-muted-foreground">模板来源</p>
                            <p className="mt-1 text-sm font-semibold">{formatTemplateSource(String(templateProfile.source || "auto_generated"))}</p>
                            <p className="mt-1 text-xs text-muted-foreground">{formatGenerationMode(String(seq.generation_mode || "personalized"))}</p>
                          </div>
                          <div className="rounded-md border bg-muted/30 p-3">
                            <p className="text-xs uppercase tracking-wide text-muted-foreground">发送资格</p>
                            <p className={`mt-1 text-sm font-semibold ${autoSendEligible ? "text-emerald-700 dark:text-emerald-400" : "text-amber-700 dark:text-amber-400"}`}>
                              {autoSendEligible ? "可进入发送流程" : "仅草稿/待确认"}
                            </p>
                          </div>
                        </div>

                        <div className="grid gap-3 md:grid-cols-2">
                          <div className="rounded-md border p-3 space-y-2">
                            <div className="flex items-center gap-2">
                              <CheckCircle2 className="h-4 w-4 text-muted-foreground" />
                              <p className="text-sm font-medium">模板策略</p>
                            </div>
                            <div className="space-y-1 text-sm">
                              <p><span className="text-muted-foreground">Tone:</span> {String(templateProfile.tone || "n/a")}</p>
                              <p><span className="text-muted-foreground">Opening:</span> {String(templatePlan.opening_strategy || "n/a")}</p>
                              <p><span className="text-muted-foreground">Value Prop:</span> {String(templatePlan.value_angle || "n/a")}</p>
                              <p><span className="text-muted-foreground">CTA:</span> {String(templatePlan.cta_strategy || "n/a")}</p>
                              <p><span className="text-muted-foreground">Validation:</span> {String(validationSummary.status || "n/a")}</p>
                              <p><span className="text-muted-foreground">Template Perf:</span> {formatTemplatePerfStatus(String(templatePerformance.status || "warming_up"))}</p>
                              <p><span className="text-muted-foreground">Next Action:</span> {formatTemplateAction(String(templatePerformance.recommended_action || "keep_collecting_data"))}</p>
                            </div>
                            {proofPoints.length > 0 && (
                              <div>
                                <p className="mb-1 text-xs uppercase tracking-wide text-muted-foreground">Proof Points</p>
                                <div className="flex flex-wrap gap-2">
                                  {proofPoints.map((item) => (
                                    <Badge key={item} variant="secondary">{item}</Badge>
                                  ))}
                                </div>
                              </div>
                            )}
                            {forbiddenClaims.length > 0 && (
                              <div>
                                <p className="mb-1 text-xs uppercase tracking-wide text-muted-foreground">Avoid</p>
                                <div className="flex flex-wrap gap-2">
                                  {forbiddenClaims.map((item) => (
                                    <Badge key={item} variant="outline">{item}</Badge>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>

                          <div className="rounded-md border p-3 space-y-2">
                            <div className="flex items-center gap-2">
                              <BarChart3 className="h-4 w-4 text-muted-foreground" />
                              <p className="text-sm font-medium">Review Summary</p>
                            </div>
                            <p className="text-sm text-muted-foreground">
                              最低通过分 {String(reviewSummary.min_score_required || "75")}，当前状态为 {formatReviewStatus(reviewStatus)}。
                            </p>
                            {reviewIssues.length > 0 ? (
                              <div className="space-y-2">
                                <div>
                                  <p className="mb-1 text-xs uppercase tracking-wide text-muted-foreground">Issues</p>
                                  <ul className="space-y-1 text-sm text-amber-700 dark:text-amber-400">
                                    {reviewIssues.map((issue) => <li key={issue}>• {issue}</li>)}
                                  </ul>
                                </div>
                                {reviewSuggestions.length > 0 && (
                                  <div>
                                    <p className="mb-1 text-xs uppercase tracking-wide text-muted-foreground">Suggestions</p>
                                    <ul className="space-y-1 text-sm text-muted-foreground">
                                      {reviewSuggestions.map((item) => <li key={item}>• {item}</li>)}
                                    </ul>
                                  </div>
                                )}
                              </div>
                            ) : (
                              <p className="text-sm text-emerald-700 dark:text-emerald-400">当前没有阻断性问题。</p>
                            )}
                          </div>
                        </div>

                        {emails.map((email, j) => (
                          <div key={j} className="rounded-md bg-muted p-3">
                            <div className="flex items-center gap-2 mb-2">
                              <Badge variant="secondary">#{Number(email.sequence_number)}</Badge>
                              <span className="text-sm font-medium">{String(email.subject)}</span>
                            </div>
                            <p className="text-sm text-muted-foreground whitespace-pre-wrap">{String(email.body_text)}</p>
                          </div>
                        ))}
                      </div>
                    </details>
                  );
                })}
              </>
            ) : (
              <div className="rounded-md border border-dashed p-8 text-center text-sm text-muted-foreground">
                当前还没有 AI 邮件可预览。请在创建任务或继续挖掘时开启邮件生成。
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {activeTab === "email-log" && (
        <>
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">邮件发送与回信日志</CardTitle>
              <CardDescription>汇总当前任务中所有邮件的发送状态、排队状态和回信情况。</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-3 md:grid-cols-4">
                <div className="rounded-md border bg-muted/30 p-3">
                  <p className="text-xs uppercase tracking-wide text-muted-foreground">已发送</p>
                  <p className="mt-1 text-2xl font-semibold">{sentLogCount}</p>
                </div>
                <div className="rounded-md border bg-muted/30 p-3">
                  <p className="text-xs uppercase tracking-wide text-muted-foreground">排队中</p>
                  <p className="mt-1 text-2xl font-semibold">{queuedLogCount}</p>
                </div>
                <div className="rounded-md border bg-muted/30 p-3">
                  <p className="text-xs uppercase tracking-wide text-muted-foreground">发送失败</p>
                  <p className="mt-1 text-2xl font-semibold">{failedLogCount}</p>
                </div>
                <div className="rounded-md border bg-muted/30 p-3">
                  <p className="text-xs uppercase tracking-wide text-muted-foreground">已回复</p>
                  <p className="mt-1 text-2xl font-semibold">{repliedLogCount}</p>
                </div>
              </div>

              {emailLogRows.length === 0 ? (
                <div className="rounded-md border border-dashed p-8 text-center text-sm text-muted-foreground">
                  当前还没有邮件日志数据。
                </div>
              ) : (
                <div className="rounded-md border overflow-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b bg-muted/50">
                        <th className="p-3 text-left font-medium">公司</th>
                        <th className="p-3 text-left font-medium">邮件</th>
                        <th className="p-3 text-left font-medium">状态</th>
                        <th className="p-3 text-left font-medium">发送对象</th>
                        <th className="p-3 text-left font-medium">发送时间</th>
                        <th className="p-3 text-left font-medium">回信</th>
                      </tr>
                    </thead>
                    <tbody>
                      {emailLogRows.map((row) => (
                        <tr key={`${row.sequenceIndex}-${row.sequenceNumber}-${row.subject}`} className="border-b last:border-0">
                          <td className="p-3">
                            <div>
                              <p className="font-medium">{row.companyName}</p>
                              <p className="text-xs text-muted-foreground">{row.locale}</p>
                            </div>
                          </td>
                          <td className="p-3">
                            <div>
                              <p className="font-medium">{row.subject || "（无主题）"}</p>
                              <p className="text-xs text-muted-foreground">
                                #{row.sequenceNumber} · {row.emailType}
                              </p>
                            </div>
                          </td>
                          <td className="p-3">
                            <div className="flex flex-wrap gap-2">
                              <Badge
                                variant={
                                  row.sendStatus === "sent"
                                    ? "success"
                                    : row.sendStatus === "failed"
                                      ? "destructive"
                                      : row.sendStatus === "queued"
                                        ? "outline"
                                        : "secondary"
                                }
                              >
                                {formatSendStatus(row.sendStatus)}
                              </Badge>
                              {row.queueReason && <Badge variant="outline">{row.queueReason}</Badge>}
                            </div>
                          </td>
                          <td className="p-3 text-muted-foreground">{row.sentTo || "—"}</td>
                          <td className="p-3 text-muted-foreground">{row.sentAt || "—"}</td>
                          <td className="p-3">
                            <div className="flex flex-wrap gap-2">
                              <Badge variant={row.replyCount > 0 ? "success" : "secondary"}>
                                {row.replyStatus}
                              </Badge>
                              {row.replyCount > 0 && (
                                <Badge variant="outline">{row.replyCount} 封</Badge>
                              )}
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
