import { useState, useRef } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useNavigate } from "@tanstack/react-router";
import { api, UploadedFile } from "@/api/client";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Crosshair, Loader2, X, Plus, Mail, Upload, FileText, MessageSquare } from "lucide-react";
import { Badge } from "@/components/ui/badge";

export function NewHuntPage() {
  const navigate = useNavigate();
  const [description, setDescription] = useState("");
  const [websiteUrl, setWebsiteUrl] = useState("");
  const [keywordInput, setKeywordInput] = useState("");
  const [keywords, setKeywords] = useState<string[]>([]);
  const [targetCustomerProfile, setTargetCustomerProfile] = useState("");
  const [regionInput, setRegionInput] = useState("");
  const [regions, setRegions] = useState<string[]>([]);
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [uploadError, setUploadError] = useState("");
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [targetLeadCount, setTargetLeadCount] = useState(200);
  const [maxRounds, setMaxRounds] = useState(10);
  const [minNewLeadsThreshold, setMinNewLeadsThreshold] = useState(5);
  const [enableEmailCraft, setEnableEmailCraft] = useState(false);
  const [emailTemplateExamplesText, setEmailTemplateExamplesText] = useState("");
  const [emailTemplateNotes, setEmailTemplateNotes] = useState("");
  const settingsQuery = useQuery({
    queryKey: ["settings", "email-readiness"],
    queryFn: api.getSettings,
    retry: false,
  });

  const createHunt = useMutation({
    mutationFn: api.createHunt,
    onSuccess: (data) => {
      navigate({ to: "/hunts/$huntId", params: { huntId: data.hunt_id } });
    },
  });

  const addKeyword = () => {
    const kw = keywordInput.trim();
    if (kw && !keywords.includes(kw)) {
      setKeywords([...keywords, kw]);
      setKeywordInput("");
    }
  };

  const addRegion = () => {
    const r = regionInput.trim();
    if (r && !regions.includes(r)) {
      setRegions([...regions, r]);
      setRegionInput("");
    }
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    if (!files.length) return;
    setUploadError("");
    setIsUploading(true);
    try {
      const result = await api.uploadFiles(files);
      setUploadedFiles((prev) => [...prev, ...result]);
    } catch (err: unknown) {
      setUploadError(err instanceof Error ? err.message : "上传失败");
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const removeFile = (fileId: string) => {
    setUploadedFiles((prev) => prev.filter((f) => f.file_id !== fileId));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // Auto-add any pending text in inputs so the user doesn't lose typed values
    const finalKeywords = [...keywords];
    const pendingKw = keywordInput.trim();
    if (pendingKw && !finalKeywords.includes(pendingKw)) {
      finalKeywords.push(pendingKw);
      setKeywords(finalKeywords);
      setKeywordInput("");
    }
    const finalRegions = [...regions];
    const pendingRegion = regionInput.trim();
    if (pendingRegion && !finalRegions.includes(pendingRegion)) {
      finalRegions.push(pendingRegion);
      setRegions(finalRegions);
      setRegionInput("");
    }
    createHunt.mutate({
      website_url: websiteUrl.trim(),
      description: description.trim(),
      product_keywords: finalKeywords,
      target_customer_profile: targetCustomerProfile.trim(),
      uploaded_file_ids: uploadedFiles.map((f) => f.file_id),
      target_regions: finalRegions,
      target_lead_count: targetLeadCount,
      max_rounds: maxRounds,
      min_new_leads_threshold: minNewLeadsThreshold,
      enable_email_craft: enableEmailCraft,
      email_template_examples: emailTemplateExamplesText
        .split(/\n\s*\n/)
        .map((item) => item.trim())
        .filter(Boolean),
      email_template_notes: emailTemplateNotes.trim(),
    });
  };

  const settingsValues = settingsQuery.data?.settings ?? {};
  const smtpConfigured = Boolean(
    settingsValues.EMAIL_FROM_ADDRESS &&
    settingsValues.EMAIL_SMTP_HOST &&
    settingsValues.EMAIL_SMTP_PORT &&
    settingsValues.EMAIL_SMTP_USERNAME &&
    settingsValues.EMAIL_SMTP_PASSWORD
  );
  const imapConfigured = Boolean(
    settingsValues.EMAIL_IMAP_HOST &&
    settingsValues.EMAIL_IMAP_PORT &&
    settingsValues.EMAIL_IMAP_USERNAME &&
    settingsValues.EMAIL_IMAP_PASSWORD
  );
  const smtpTested = Boolean(settingsValues.EMAIL_SMTP_LAST_TEST_AT);
  const imapTested = Boolean(settingsValues.EMAIL_IMAP_LAST_TEST_AT);
  const autoSendEnabled = (settingsValues.EMAIL_AUTO_SEND_ENABLED ?? "false") === "true";

  return (
    <div className="max-w-2xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight">新建任务</h1>
        <p className="text-muted-foreground mt-1">配置你的 AI B2B 获客任务</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* ── Description ───────────────────────────── */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <MessageSquare className="h-5 w-5 text-primary" />
              <CardTitle className="text-lg">你想找什么客户？</CardTitle>
            </div>
            <CardDescription>
              用自然语言描述你的目标市场、客户类型和产品，系统会自动提取关键信息。（可选）
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Input
              placeholder="e.g. 我想找东南亚的旅行社公司  /  Looking for US importers of industrial LED lighting"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
            {description && (
              <p className="text-xs text-muted-foreground mt-2">
                系统会自动从这段描述中提取目标地区、客户画像和产品关键词。
              </p>
            )}
          </CardContent>
        </Card>

        {/* ── Company Website ────────────────────────── */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">企业官网 <span className="text-muted-foreground font-normal text-sm">（可选）</span></CardTitle>
            <CardDescription>用于更深入地分析你的客户画像和产品定位</CardDescription>
          </CardHeader>
          <CardContent>
            <Input
              placeholder="https://yourcompany.com"
              value={websiteUrl}
              onChange={(e) => setWebsiteUrl(e.target.value)}
            />
          </CardContent>
        </Card>

        {/* ── File Upload ────────────────────────────── */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Upload className="h-5 w-5 text-primary" />
              <CardTitle className="text-lg">上传企业资料 <span className="text-muted-foreground font-normal text-sm">（可选）</span></CardTitle>
            </div>
            <CardDescription>
              支持上传产品目录、公司介绍或其他资料，支持 PDF、Word、Excel、TXT、MD、CSV。
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div
              className="border-2 border-dashed border-border rounded-lg p-6 text-center cursor-pointer hover:border-primary/50 transition-colors"
              onClick={() => fileInputRef.current?.click()}
            >
              <Upload className="h-8 w-8 text-muted-foreground mx-auto mb-2" />
              <p className="text-sm text-muted-foreground">
                {isUploading ? (
                  <span className="flex items-center justify-center gap-2">
                    <Loader2 className="h-4 w-4 animate-spin" /> 上传中…
                  </span>
                ) : (
                  "点击选择文件，或直接拖拽到这里"
                )}
              </p>
              <p className="text-xs text-muted-foreground mt-1">PDF, DOCX, XLSX, TXT, MD, CSV</p>
            </div>
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept=".pdf,.docx,.doc,.xlsx,.xls,.csv,.txt,.md,.json"
              className="hidden"
              onChange={handleFileChange}
            />
            {uploadError && (
              <p className="text-destructive text-sm">{uploadError}</p>
            )}
            {uploadedFiles.length > 0 && (
              <div className="space-y-2">
                {uploadedFiles.map((f) => (
                  <div key={f.file_id} className="flex items-center gap-2 text-sm bg-muted/50 rounded px-3 py-2">
                    <FileText className="h-4 w-4 text-muted-foreground shrink-0" />
                    <span className="flex-1 truncate">{f.original_name}</span>
                    <button type="button" onClick={() => removeFile(f.file_id)} className="text-muted-foreground hover:text-destructive">
                      <X className="h-4 w-4" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">产品关键词</CardTitle>
            <CardDescription>描述你的产品或服务的核心关键词</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex gap-2">
              <Input
                placeholder="例如：micro switch"
                value={keywordInput}
                onChange={(e) => setKeywordInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), addKeyword())}
              />
              <Button type="button" variant="outline" size="icon" onClick={addKeyword}>
                <Plus className="h-4 w-4" />
              </Button>
            </div>
            {keywords.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {keywords.map((kw) => (
                  <Badge key={kw} variant="secondary" className="gap-1">
                    {kw}
                    <button type="button" onClick={() => setKeywords(keywords.filter((k) => k !== kw))}>
                      <X className="h-3 w-3" />
                    </button>
                  </Badge>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">目标客户画像</CardTitle>
            <CardDescription>描述你的理想客户类型（可选）</CardDescription>
          </CardHeader>
          <CardContent>
            <Input
              placeholder="e.g. 批发商和代理商, distributors and wholesalers, importers"
              value={targetCustomerProfile}
              onChange={(e) => setTargetCustomerProfile(e.target.value)}
            />
            <p className="text-xs text-muted-foreground mt-2">
              这有助于生成更贴合批发商、分销商、代理商等客户类型的搜索关键词。
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">目标地区</CardTitle>
            <CardDescription>希望重点搜索的国家或地区</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex gap-2">
              <Input
                placeholder="e.g. Europe"
                value={regionInput}
                onChange={(e) => setRegionInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), addRegion())}
              />
              <Button type="button" variant="outline" size="icon" onClick={addRegion}>
                <Plus className="h-4 w-4" />
              </Button>
            </div>
            {regions.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {regions.map((r) => (
                  <Badge key={r} variant="secondary" className="gap-1">
                    {r}
                    <button type="button" onClick={() => setRegions(regions.filter((x) => x !== r))}>
                      <X className="h-3 w-3" />
                    </button>
                  </Badge>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">任务参数</CardTitle>
            <CardDescription>配置线索数量和搜索轮次</CardDescription>
          </CardHeader>
          <CardContent className="grid grid-cols-1 gap-4 md:grid-cols-3">
            <div className="space-y-2">
              <label className="text-sm font-medium">目标线索数量</label>
              <Input
                type="number"
                min={1}
                max={10000}
                value={targetLeadCount}
                onChange={(e) => setTargetLeadCount(Number(e.target.value))}
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">最大轮次</label>
              <Input
                type="number"
                min={1}
                max={50}
                value={maxRounds}
                onChange={(e) => setMaxRounds(Number(e.target.value))}
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">每轮最少新增线索</label>
              <Input
                type="number"
                min={1}
                max={100}
                value={minNewLeadsThreshold}
                onChange={(e) => setMinNewLeadsThreshold(Number(e.target.value))}
              />
              <p className="text-xs text-muted-foreground">
                若某轮新增线索少于这个值，系统会判定收益递减并停止。默认 5。
              </p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <CardTitle className="text-lg">AI 邮件生成</CardTitle>
            </div>
            <CardDescription>基于 ICP 和官网洞察生成 3 步英文开发邮件，也支持从你的历史邮件中提取模板风格。</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="rounded-lg border border-dashed p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Mail className="h-5 w-5 text-muted-foreground" />
                  <div>
                    <p className="text-sm font-medium">生成 AI 邮件序列</p>
                    <p className="text-xs text-muted-foreground">启用后会为线索生成邮件模板计划、3 封开发邮件和发送审核信息。</p>
                  </div>
                </div>
                <button
                  type="button"
                  role="switch"
                  aria-checked={enableEmailCraft}
                  onClick={() => setEnableEmailCraft(!enableEmailCraft)}
                  className={`relative inline-flex h-6 w-11 shrink-0 rounded-full border-2 border-transparent transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 ${
                    enableEmailCraft ? "bg-primary" : "bg-input"
                  }`}
                >
                  <span
                    className={`pointer-events-none block h-5 w-5 rounded-full bg-background shadow-lg ring-0 transition-transform ${
                      enableEmailCraft ? "translate-x-5" : "translate-x-0"
                    }`}
                  />
                </button>
              </div>
              {enableEmailCraft && (
                <div className="mt-4 space-y-4">
                  <div className={`rounded-md border px-3 py-3 text-sm ${smtpConfigured ? "border-emerald-200 bg-emerald-50 text-emerald-900" : "border-amber-200 bg-amber-50 text-amber-900"}`}>
                    <div className="flex flex-wrap items-center gap-2">
                      <Badge variant={smtpConfigured ? "success" : "warning"}>
                        {smtpConfigured ? (smtpTested ? "SMTP 已验证" : "SMTP 已配置") : "SMTP 未配置"}
                      </Badge>
                      <span>邮件草稿可以正常生成和预览。</span>
                    </div>
                    <p className="mt-2 text-xs leading-5 text-current/80">
                      {smtpConfigured
                        ? (
                          smtpTested
                            ? "当前邮箱授权信息已配置并测试成功，后续可以进入自动发送链路。"
                            : "当前邮箱参数已填写，但还没有测试成功。可以先生成和预览；自动发送启动前仍会被后端拦截。"
                        )
                        : "当前仅建议用于生成和预览。未完成 SMTP 授权前，手动发送、创建自动发送 campaign 和调度器发送都会被后端拦截。"}
                    </p>
                    {autoSendEnabled && !smtpConfigured && (
                      <p className="mt-2 text-xs leading-5 text-current/80">
                        你在设置里开启了自动发送，但 SMTP 还没配好，这种状态下不会通过发送前置校验。
                      </p>
                    )}
                    <p className="mt-2 text-xs leading-5 text-current/80">
                      {imapConfigured
                        ? (
                          imapTested
                            ? "IMAP 已配置并测试成功，可用于自动回信检测。"
                            : "IMAP 参数已填写，但尚未测试成功；自动回信检测暂时不会启动。"
                        )
                        : "IMAP 未配置时仍可生成和发送，但无法自动检测回信。"}
                    </p>
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">历史邮件样例 / 模板样例 <span className="text-muted-foreground font-normal">（可选）</span></label>
                    <textarea
                      className="min-h-[180px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm shadow-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
                      placeholder={"把你以前发过的英文开发邮件贴进来。支持多封邮件，用空行隔开。\n\nExample 1:\nSubject: Quick intro\nHello ...\n\nExample 2:\nSubject: Potential fit\nHi ..."}
                      value={emailTemplateExamplesText}
                      onChange={(e) => setEmailTemplateExamplesText(e.target.value)}
                    />
                    <p className="text-xs text-muted-foreground">
                      如果你提供历史邮件，系统会先提取你的写作风格和模板结构，再结合 ICP/官网洞察生成邮件。
                    </p>
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">邮件模板备注 <span className="text-muted-foreground font-normal">（可选）</span></label>
                    <textarea
                      className="min-h-[100px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm shadow-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
                      placeholder="例如：保持简洁直接；避免夸张表述；优先强调渠道合作；默认使用英文；CTA 不要太强。"
                      value={emailTemplateNotes}
                      onChange={(e) => setEmailTemplateNotes(e.target.value)}
                    />
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {createHunt.isError && (
          <div className="rounded-md bg-destructive/10 p-4 text-sm text-destructive">
            {createHunt.error.message}
          </div>
        )}

        <Button type="submit" size="lg" className="w-full" disabled={createHunt.isPending}>
          {createHunt.isPending ? (
            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
          ) : (
            <Crosshair className="h-4 w-4 mr-2" />
          )}
          {createHunt.isPending ? "任务启动中..." : "开始挖掘"}
        </Button>
      </form>
    </div>
  );
}
