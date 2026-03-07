import { useEffect, useState, useCallback, useRef, useMemo } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useParams } from "@tanstack/react-router";
import { api } from "@/api/client";
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

// ── Resume Dialog ────────────────────────────────────────────────────
function ResumeDialog({
  open, onClose, onConfirm, isLoading, currentLeads,
}: {
  open: boolean;
  onClose: () => void;
  onConfirm: (targetLeadCount: number, maxRounds: number, enableEmailCraft: boolean) => void;
  isLoading: boolean;
  currentLeads: number;
}) {
  const [targetLeadCount, setTargetLeadCount] = useState(Math.max(currentLeads + 100, 200));
  const [maxRounds, setMaxRounds] = useState(10);
  const [enableEmailCraft, setEnableEmailCraft] = useState(false);

  // Sync default when dialog opens
  useEffect(() => {
    if (open) {
      setTargetLeadCount(Math.max(currentLeads + 100, 200));
      setMaxRounds(10);
      setEnableEmailCraft(false);
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
            <h2 className="text-lg font-bold">继续挖掘客户</h2>
            <p className="text-sm text-muted-foreground">在已有 {currentLeads} 条线索基础上继续</p>
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

          <div className="flex items-center justify-between rounded-md border p-3">
            <div>
              <p className="text-sm font-medium">生成邮件序列</p>
              <p className="text-xs text-muted-foreground">完成后为新线索生成个性化邮件</p>
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
            onClick={() => onConfirm(targetLeadCount, maxRounds, enableEmailCraft)}
            disabled={isLoading}
          >
            {isLoading ? (
              <><Loader2 className="h-4 w-4 mr-2 animate-spin" />启动中...</>
            ) : (
              <><PlayCircle className="h-4 w-4 mr-2" />开始继续挖掘</>
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
              {decisionMakers.map((dm, i) => (
                <div key={i} className="rounded-md border p-3 space-y-1.5">
                  <div className="flex items-center gap-2">
                    <User className="h-3.5 w-3.5 text-muted-foreground" />
                    <span className="font-medium text-sm">{dm.name || "未知联系人"}</span>
                    {dm.title && <span className="text-xs text-muted-foreground">· {dm.title}</span>}
                  </div>
                  {dm.email && (
                    <div className="flex items-center gap-2 text-sm pl-5">
                      <Mail className="h-3 w-3 text-muted-foreground" />
                      <a href={`mailto:${normalizeDecisionMakerEmail(dm.email)}`} className="text-primary hover:underline">{normalizeDecisionMakerEmail(dm.email)}</a>
                      <Badge variant={getDecisionMakerEmailStatus(dm.email) === "verified" ? "outline" : "secondary"}>
                        {getDecisionMakerEmailStatus(dm.email) === "verified" ? "已验证" : "按邮箱规则推断"}
                      </Badge>
                      <CopyButton text={normalizeDecisionMakerEmail(dm.email)} />
                    </div>
                  )}
                  {!dm.email && (
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
              ))}
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
  email_craft?: { email_count: number };
}

const STAGE_ICONS: Record<string, React.ReactNode> = {
  insight: <Brain className="h-4 w-4" />,
  keyword_gen: <FileText className="h-4 w-4" />,
  search: <Search className="h-4 w-4" />,
  lead_extract: <Users className="h-4 w-4" />,
  evaluate: <CheckCircle2 className="h-4 w-4" />,
  email_craft: <Mail className="h-4 w-4" />,
};

const STAGE_LABELS: Record<string, string> = {
  insight: "分析企业画像",
  keyword_gen: "生成关键词",
  search: "搜索 Google Maps",
  lead_extract: "提取线索",
  evaluate: "评估结果",
  email_craft: "生成邮件",
};

const STAGES = ["insight", "keyword_gen", "search", "lead_extract", "evaluate", "email_craft"];

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

  if (stage === "email_craft") {
    if (!data.email_craft) return <p className="text-sm text-muted-foreground">当前暂无邮件生成数据。</p>;
    return (
      <div className="space-y-2">
        <h4 className="font-semibold flex items-center gap-2">
          <Mail className="h-4 w-4" /> 邮件生成
        </h4>
        <p className="text-sm">
          <span className="font-medium">{data.email_craft.email_count}</span> personalized email sequences generated
        </p>
      </div>
    );
  }

  return <p className="text-sm text-muted-foreground">No data available for this stage yet.</p>;
}

export function HuntDetailPage() {
  const { huntId } = useParams({ from: "/hunts/$huntId" });
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
  const [showResumeDialog, setShowResumeDialog] = useState(false);
  const [activeTab, setActiveTab] = useState<"overview" | "leads">("overview");
  const [realtimeLeads, setRealtimeLeads] = useState<Lead[]>([]);

  const resumeMutation = useMutation({
    mutationFn: ({ targetLeadCount, maxRounds, enableEmailCraft }: {
      targetLeadCount: number; maxRounds: number; enableEmailCraft: boolean;
    }) => api.resumeHunt(huntId, {
      target_lead_count: targetLeadCount,
      max_rounds: maxRounds,
      enable_email_craft: enableEmailCraft,
    }),
    onSuccess: () => {
      setShowResumeDialog(false);
      // Reset all local state so the page reconnects via SSE
      setSSE({ stage: null, huntRound: 0, leadsCount: 0, status: "connecting", error: null });
      setShowResult(false);
      setInitialLoaded(false);
      setActivityLog([]);
      setStageData({});
      setSelectedStage(null);
      setRealtimeLeads([]);
      queryClient.removeQueries({ queryKey: ["hunt-result", huntId] });
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
  const emailCount = result?.email_sequences?.length ?? 0;
  const keywordCount = result?.used_keywords?.length ?? 0;
  const roundCount = result?.hunt_round ?? sse.huntRound;

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
          stage: "email_craft",
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
        ...prev, status: "completed", leadsCount: d.leads_count, stage: "email_craft",
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
        } else if (stage === "email_craft") {
          next.email_craft = { email_count: d.email_count };
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
        setSSE((prev) => ({ ...prev, status: "completed", leadsCount: d.leads_count ?? prev.leadsCount, stage: "email_craft" }));
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
          if (h === "decision_maker_emails") return escapeCSV(dms.map((dm) => normalizeDecisionMakerEmail(dm.email || "")).filter(Boolean).join("; "));
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
      if (!prev.email_craft) {
        next.email_craft = { email_count: result.email_sequences.length };
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
            {sse.status === "completed" ? "Completed" : sse.status === "failed" ? "Failed" : "In progress..."}
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
              onClick={() => setShowResumeDialog(true)}
              className="gap-2"
            >
              <RefreshCw className="h-4 w-4" />
              继续挖掘
            </Button>
          )}
        </div>
      </div>

      <ResumeDialog
        open={showResumeDialog}
        onClose={() => setShowResumeDialog(false)}
        onConfirm={(targetLeadCount, maxRounds, enableEmailCraft) =>
          resumeMutation.mutate({ targetLeadCount, maxRounds, enableEmailCraft })
        }
        isLoading={resumeMutation.isPending}
        currentLeads={sse.leadsCount || (result?.leads?.length ?? 0)}
      />

      {/* Tab switcher */}
      <div className="flex gap-1 border-b">
        {(["overview", "leads"] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === tab
                ? "border-primary text-primary"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            {tab === "overview" ? "总览" : `线索${leadsTabCount > 0 ? ` (${leadsTabCount})` : ""}`}
          </button>
        ))}
      </div>

      {activeTab === "overview" && (<>
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
                    <p className="text-xs text-muted-foreground">邮件序列</p>
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

          {/* Lead Detail Sheet */}
          <LeadDetailSheet
            lead={selectedLead}
            open={selectedLead !== null}
            onClose={() => setSelectedLead(null)}
          />

          {/* Email Sequences */}
          {emailCount > 0 && result && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">邮件序列</CardTitle>
                <CardDescription>已生成 {result.email_sequences.length} 组个性化邮件序列</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {result.email_sequences.map((seq: Record<string, unknown>, i: number) => {
                  const lead = seq.lead as Record<string, unknown> | undefined;
                  const emails = (seq.emails as Record<string, unknown>[]) || [];
                  return (
                    <details key={i} className="rounded-md border p-4">
                      <summary className="cursor-pointer font-medium flex items-center gap-2">
                        <Mail className="h-4 w-4 text-muted-foreground" />
                        {String(lead?.company_name || `序列 ${i + 1}`)}
                        <Badge variant="outline" className="ml-auto">{String(seq.locale || "en")}</Badge>
                      </summary>
                      <div className="mt-4 space-y-3">
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
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  );
}
