import { useState, useRef } from "react";
import { useMutation } from "@tanstack/react-query";
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
  const [enableEmailCraft, setEnableEmailCraft] = useState(false);

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
      enable_email_craft: enableEmailCraft,
    });
  };

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
          <CardContent className="grid grid-cols-2 gap-4">
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
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">AI 邮件生成</CardTitle>
            <CardDescription>可选为已发现线索生成个性化开发邮件</CardDescription>
          </CardHeader>
          <CardContent>
            <label className="flex items-center justify-between cursor-pointer">
              <div className="flex items-center gap-3">
                <Mail className="h-5 w-5 text-muted-foreground" />
                <div>
                  <p className="text-sm font-medium">生成 AI 邮件</p>
                  <p className="text-xs text-muted-foreground">任务完成后自动生成多语言邮件序列</p>
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
            </label>
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
