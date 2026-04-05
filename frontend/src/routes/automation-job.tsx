import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useParams } from "@tanstack/react-router";
import { api, type EmailCampaignListItem, type EmailSequence, type HuntResult } from "@/api/client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Clock, Globe, Loader2, RotateCcw, Target, Workflow, Mail, Building2, Send } from "lucide-react";

const EXECUTION_STAGES = [
  ["queued", "等待 consumer 领取"],
  ["claimed", "已被 consumer 领取"],
  ["template_seed", "准备模板 seed"],
  ["create_hunt", "创建 Hunt"],
  ["hunt_created", "Hunt 已创建"],
  ["wait_hunt", "等待 Hunt 完成"],
  ["load_result", "加载结果"],
  ["create_campaign", "创建 Campaign"],
  ["start_campaign", "启动 Campaign"],
  ["completed", "已完成"],
  ["failed", "失败"],
] as const;

function formatTime(iso: string) {
  if (!iso) return "-";
  try {
    return new Date(iso).toLocaleString();
  } catch {
    return iso;
  }
}

function statusLabel(status: string) {
  if (status === "queued") return "排队中";
  if (status === "running") return "执行中";
  if (status === "completed") return "已完成";
  if (status === "failed") return "失败";
  return status || "未知";
}

function statusVariant(status: string) {
  if (status === "completed") return "success" as const;
  if (status === "running") return "warning" as const;
  if (status === "failed") return "destructive" as const;
  return "secondary" as const;
}

function templateSeedLabel(status: string) {
  if (status === "ready") return "已准备";
  if (status === "preparing") return "准备中";
  if (status === "failed") return "准备失败";
  return "未准备";
}

function streamLabel(state: string) {
  if (state === "connected") return "实时更新已连接";
  if (state === "connecting") return "实时更新连接中";
  if (state === "fallback") return "实时流断开，回退轮询";
  return "等待连接";
}

function stageStatus(current: string, target: string) {
  if (!current) return "pending";
  if (current === target) return "current";
  const currentIndex = EXECUTION_STAGES.findIndex(([id]) => id === current);
  const targetIndex = EXECUTION_STAGES.findIndex(([id]) => id === target);
  if (current === "completed" && target !== "failed") return "done";
  if (current === "failed" && target === "failed") return "current";
  if (currentIndex > targetIndex && targetIndex >= 0) return "done";
  return "pending";
}

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" ? (value as Record<string, unknown>) : {};
}

function cleanEmail(value: unknown): string {
  return String(value || "").trim().toLowerCase();
}

function extractSequenceTargets(sequence: EmailSequence): string[] {
  const targets: string[] = [];
  const primary = asRecord((sequence as unknown as Record<string, unknown>).target);
  const primaryEmail = cleanEmail(primary.target_email);
  if (primaryEmail) targets.push(primaryEmail);

  const rawTargets = (sequence as unknown as Record<string, unknown>).targets;
  if (Array.isArray(rawTargets)) {
    for (const item of rawTargets) {
      const email = cleanEmail(asRecord(item).target_email);
      if (email) targets.push(email);
    }
  }

  if (!targets.length) {
    const lead = asRecord(sequence.lead);
    const emails = lead.emails;
    if (Array.isArray(emails)) {
      for (const email of emails) {
        const normalized = cleanEmail(email);
        if (normalized) targets.push(normalized);
      }
    }
  }
  return Array.from(new Set(targets));
}

function flattenCampaignSequences(campaigns: EmailCampaignListItem[] | undefined) {
  return (campaigns || []).flatMap((item) =>
    (item.sequences || []).map((sequence) => ({
      ...sequence,
      campaignName: item.campaign.name,
      campaignStatus: item.campaign.status,
    })),
  );
}

export function AutomationJobPage() {
  const { jobId } = useParams({ from: "/automation/$jobId" });
  const queryClient = useQueryClient();
  const [streamState, setStreamState] = useState<"idle" | "connecting" | "connected" | "fallback">("idle");
  const { data: automationStatus } = useQuery({
    queryKey: ["automation-status"],
    queryFn: api.getAutomationStatus,
    refetchInterval: 5000,
  });
  const { data: job, isLoading, error } = useQuery({
    queryKey: ["automation-job", jobId],
    queryFn: () => api.getAutomationJob(jobId),
    refetchInterval: 10000,
  });
  const huntId = job?.last_hunt_id || "";
  const { data: huntResult } = useQuery<HuntResult>({
    queryKey: ["automation-job-hunt-result", huntId],
    queryFn: () => api.getHuntResult(huntId),
    enabled: !!huntId,
    refetchInterval: job?.status === "running" ? 5000 : false,
    retry: false,
  });
  const { data: campaigns } = useQuery<EmailCampaignListItem[]>({
    queryKey: ["automation-job-campaigns", huntId],
    queryFn: () => api.listEmailCampaigns(huntId),
    enabled: !!huntId,
    refetchInterval: 5000,
    retry: false,
  });
  const cancelMutation = useMutation({
    mutationFn: () => api.cancelAutomationJob(jobId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["automation-job", jobId] });
      await queryClient.invalidateQueries({ queryKey: ["automation-jobs"] });
      await queryClient.invalidateQueries({ queryKey: ["automation-status"] });
      await queryClient.invalidateQueries({ queryKey: ["automation-metrics", 24] });
    },
  });
  const retryMutation = useMutation({
    mutationFn: () => api.retryAutomationJob(jobId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["automation-job", jobId] });
      await queryClient.invalidateQueries({ queryKey: ["automation-jobs"] });
      await queryClient.invalidateQueries({ queryKey: ["automation-status"] });
      await queryClient.invalidateQueries({ queryKey: ["automation-metrics", 24] });
    },
  });

  useEffect(() => {
    if (!jobId) return;
    setStreamState("connecting");
    const source = api.streamAutomationJob(jobId);
    const sync = () => {
      void queryClient.invalidateQueries({ queryKey: ["automation-job", jobId] });
      void queryClient.invalidateQueries({ queryKey: ["automation-jobs"] });
      void queryClient.invalidateQueries({ queryKey: ["automation-status"] });
      void queryClient.invalidateQueries({ queryKey: ["automation-metrics", 24] });
    };

    source.onopen = () => setStreamState("connected");
    source.addEventListener("heartbeat", sync);
    source.addEventListener("update", sync);
    source.addEventListener("completed", () => {
      sync();
      setStreamState("connected");
      source.close();
    });
    source.addEventListener("failed", () => {
      sync();
      setStreamState("connected");
      source.close();
    });
    source.onerror = () => {
      setStreamState("fallback");
      source.close();
    };

    return () => {
      source.close();
    };
  }, [jobId, queryClient]);

  const leads = useMemo(() => huntResult?.leads || [], [huntResult?.leads]);
  const emailSequences = useMemo(() => huntResult?.email_sequences || [], [huntResult?.email_sequences]);
  const campaignSequences = useMemo(() => flattenCampaignSequences(campaigns), [campaigns]);
  const generatedTargetEmails = useMemo(() => {
    const emails = new Set<string>();
    emailSequences.forEach((sequence) => {
      extractSequenceTargets(sequence).forEach((email) => emails.add(email));
    });
    return Array.from(emails);
  }, [emailSequences]);
  const queuedOrSentEmails = useMemo(() => {
    const emails = new Set<string>();
    campaignSequences.forEach((sequence) => {
      const email = cleanEmail(sequence.lead_email);
      if (email) emails.add(email);
    });
    return Array.from(emails);
  }, [campaignSequences]);
  const missingTargetEmails = useMemo(
    () => generatedTargetEmails.filter((email) => !queuedOrSentEmails.includes(email)),
    [generatedTargetEmails, queuedOrSentEmails],
  );

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error || !job) {
    return (
      <Card>
        <CardContent className="py-10 text-sm text-destructive">
          {error instanceof Error ? error.message : "任务不存在"}
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">队列任务详情</h1>
          <p className="text-muted-foreground mt-1">查看 producer / consumer 模式下单个任务的执行状态</p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="outline">{streamLabel(streamState)}</Badge>
          <Badge variant={statusVariant(job.status)}>{statusLabel(job.status)}</Badge>
          {(job.status === "queued" || job.status === "running") && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => cancelMutation.mutate()}
              disabled={cancelMutation.isPending}
            >
              {cancelMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : "取消任务"}
            </Button>
          )}
          {(job.status === "failed" || job.status === "completed") && (
            <Button
              size="sm"
              onClick={() => retryMutation.mutate()}
              disabled={retryMutation.isPending}
            >
              {retryMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : "重新入队"}
            </Button>
          )}
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">任务状态</CardTitle>
          </CardHeader>
          <CardContent className="text-2xl font-semibold">{statusLabel(job.status)}</CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">已尝试次数</CardTitle>
          </CardHeader>
          <CardContent className="flex items-center gap-2 text-2xl font-semibold">
            <RotateCcw className="h-5 w-5 text-muted-foreground" />
            {job.attempt_count}
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">目标线索数</CardTitle>
          </CardHeader>
          <CardContent className="flex items-center gap-2 text-2xl font-semibold">
            <Target className="h-5 w-5 text-muted-foreground" />
            {job.target_lead_count}
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">当前线索数</CardTitle>
          </CardHeader>
          <CardContent className="flex items-center gap-2 text-2xl font-semibold">
            <Workflow className="h-5 w-5 text-muted-foreground" />
            {job.leads_count}
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">模板 Seed</CardTitle>
          </CardHeader>
          <CardContent className="text-2xl font-semibold">
            {templateSeedLabel(job.template_seed_status)}
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Consumer</CardTitle>
          </CardHeader>
          <CardContent className="text-2xl font-semibold">
            {automationStatus?.workers?.consumer?.running ? "在线" : "离线"}
          </CardContent>
        </Card>
      </div>

      {!automationStatus?.workers?.consumer?.running && (
        <Card className="border-amber-300">
          <CardContent className="py-4 text-sm text-amber-700">
            当前没有检测到运行中的 consumer。queue job 会停留在排队状态，直到 API 内嵌 consumer 或独立 consumer 进程开始消费。
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>任务信息</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <div className="flex items-start gap-2">
            <Globe className="h-4 w-4 mt-0.5 text-muted-foreground" />
            <div>
              <div className="font-medium">官网</div>
              <div className="text-muted-foreground break-all">{job.website_url || "-"}</div>
            </div>
          </div>
          <div>
            <div className="font-medium">描述</div>
            <div className="text-muted-foreground">{job.description || "-"}</div>
          </div>
          <div>
            <div className="font-medium">关键词</div>
            <div className="text-muted-foreground">{job.product_keywords.join(", ") || "-"}</div>
          </div>
          <div>
            <div className="font-medium">地区</div>
            <div className="text-muted-foreground">{job.target_regions.join(", ") || "-"}</div>
          </div>
          <div className="grid gap-3 md:grid-cols-2">
            <div>
              <div className="font-medium">创建时间</div>
              <div className="text-muted-foreground">{formatTime(job.created_at)}</div>
            </div>
            <div>
              <div className="font-medium">最近更新时间</div>
              <div className="text-muted-foreground">{formatTime(job.updated_at)}</div>
            </div>
            <div>
              <div className="font-medium">开始时间</div>
              <div className="text-muted-foreground">{formatTime(job.started_at)}</div>
            </div>
            <div>
              <div className="font-medium">结束时间</div>
              <div className="text-muted-foreground">{formatTime(job.finished_at)}</div>
            </div>
            <div>
              <div className="font-medium">Consumer</div>
              <div className="text-muted-foreground break-all">{job.claimed_by || "-"}</div>
            </div>
            <div>
              <div className="font-medium">当前活跃 Job</div>
              <div className="text-muted-foreground break-all">{automationStatus?.workers?.consumer?.active_job_id || "-"}</div>
            </div>
            <div>
              <div className="font-medium">模板 Seed 来源</div>
              <div className="text-muted-foreground">{job.template_seed_source || "-"}</div>
            </div>
            <div>
              <div className="font-medium">最近 Consumer 活动</div>
              <div className="text-muted-foreground">{formatTime(automationStatus?.workers?.consumer?.last_activity_at || "")}</div>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>执行链路</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <div>
            <div className="font-medium">队列执行阶段</div>
            <div className="text-muted-foreground">{job.progress_stage || "-"}</div>
          </div>
          <div>
            <div className="font-medium">当前执行说明</div>
            <div className="text-muted-foreground">{job.progress_message || "-"}</div>
          </div>
          <div>
            <div className="font-medium">Hunt 状态</div>
            <div className="text-muted-foreground">{job.hunt_status || "-"}</div>
          </div>
          <div>
            <div className="font-medium">Hunt 阶段</div>
            <div className="text-muted-foreground">{job.hunt_stage || "-"}</div>
          </div>
          <div>
            <div className="font-medium">最近错误</div>
            <div className="text-destructive break-all">{job.last_error || job.hunt_error || "-"}</div>
          </div>
          {job.last_hunt_id && (
            <Link to="/hunts/$huntId" params={{ huntId: job.last_hunt_id }}>
              <Button variant="outline">
                <Clock className="h-4 w-4 mr-2" />
                查看 Hunt 详情
              </Button>
            </Link>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>阶段时间线</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-2 md:grid-cols-2 xl:grid-cols-3">
          {EXECUTION_STAGES.map(([stageId, label]) => {
            const state = stageStatus(job.progress_stage, stageId);
            return (
              <div
                key={stageId}
                className={
                  state === "current"
                    ? "rounded-md border border-amber-400 bg-amber-50 p-3 text-sm"
                    : state === "done"
                      ? "rounded-md border border-emerald-300 bg-emerald-50 p-3 text-sm"
                      : "rounded-md border p-3 text-sm text-muted-foreground"
                }
              >
                <div className="font-medium">{label}</div>
                <div className="mt-1 text-xs">{stageId}</div>
              </div>
            );
          })}
        </CardContent>
      </Card>

      <div className="grid gap-4 xl:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <Building2 className="h-4 w-4 text-muted-foreground" />
              已挖掘企业
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            {leads.length ? leads.slice(0, 20).map((lead, index) => {
              const item = asRecord(lead);
              const emails = Array.isArray(item.emails) ? item.emails : [];
              return (
                <div key={`${item.company_name || "lead"}-${index}`} className="rounded-md border p-3">
                  <div className="font-medium">{String(item.company_name || "Unknown")}</div>
                  <div className="text-muted-foreground break-all">{String(item.website || "-")}</div>
                  <div className="mt-1 text-xs text-muted-foreground">
                    邮箱 {(emails as unknown[]).filter(Boolean).length} · 国家 {String(item.country || "-")}
                  </div>
                </div>
              );
            }) : (
              <div className="rounded-md border border-dashed p-6 text-center text-muted-foreground">
                当前还没有可展示的企业结果
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <Mail className="h-4 w-4 text-muted-foreground" />
              邮件模板
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            {emailSequences.length ? emailSequences.slice(0, 10).map((sequence, index) => {
              const lead = asRecord(sequence.lead);
              const targets = extractSequenceTargets(sequence);
              return (
                <div key={`${lead.company_name || "sequence"}-${index}`} className="rounded-md border p-3">
                  <div className="flex items-center justify-between gap-3">
                    <div className="font-medium">{String(lead.company_name || "Unknown")}</div>
                    <Badge variant="outline">{targets.length} 个目标邮箱</Badge>
                  </div>
                  <div className="mt-1 text-xs text-muted-foreground break-all">
                    {targets.join(", ") || "暂未解析到目标邮箱"}
                  </div>
                  <div className="mt-3 space-y-3">
                    {(sequence.emails || []).map((email) => (
                      <div key={`${index}-${email.sequence_number}`} className="rounded-md bg-muted/40 p-3">
                        <div className="text-xs font-medium text-muted-foreground">
                          第 {email.sequence_number} 封 · {email.email_type || "-"}
                        </div>
                        <div className="mt-1 font-medium">{email.subject || "(无主题)"}</div>
                        <pre className="mt-2 whitespace-pre-wrap break-words text-xs text-muted-foreground">{email.body_text || ""}</pre>
                      </div>
                    ))}
                  </div>
                </div>
              );
            }) : (
              <div className="rounded-md border border-dashed p-6 text-center text-muted-foreground">
                当前还没有生成邮件模板
              </div>
            )}
          </CardContent>
        </Card>

        <Card className={missingTargetEmails.length ? "border-amber-300" : undefined}>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <Send className="h-4 w-4 text-muted-foreground" />
              发送覆盖对账
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4 text-sm">
            <div className="grid grid-cols-2 gap-3">
              <div className="rounded-md border p-3">
                <div className="text-xs text-muted-foreground">模板目标邮箱</div>
                <div className="mt-1 text-2xl font-semibold">{generatedTargetEmails.length}</div>
              </div>
              <div className="rounded-md border p-3">
                <div className="text-xs text-muted-foreground">已创建发送序列</div>
                <div className="mt-1 text-2xl font-semibold">{queuedOrSentEmails.length}</div>
              </div>
            </div>

            <div>
              <div className="font-medium">实际发送/入队邮箱</div>
              {campaignSequences.length ? (
                <div className="mt-2 space-y-2">
                  {campaignSequences.slice(0, 20).map((sequence) => (
                    <div key={sequence.id} className="rounded-md border p-3">
                      <div className="flex items-center justify-between gap-3">
                        <div className="font-medium">{sequence.lead_name || sequence.lead_email}</div>
                        <Badge variant="outline">{sequence.status || "-"}</Badge>
                      </div>
                      <div className="mt-1 break-all text-muted-foreground">{sequence.lead_email || "-"}</div>
                      <div className="mt-1 text-xs text-muted-foreground">
                        {sequence.campaignName} · 当前步骤 {sequence.current_step}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="mt-2 rounded-md border border-dashed p-4 text-center text-muted-foreground">
                  当前还没有创建 campaign 或发送序列
                </div>
              )}
            </div>

            <div>
              <div className="font-medium">未进入发送序列的目标邮箱</div>
              {missingTargetEmails.length ? (
                <div className="mt-2 space-y-2">
                  {missingTargetEmails.slice(0, 20).map((email) => (
                    <div key={email} className="rounded-md border border-amber-300 bg-amber-50 p-2 break-all text-amber-800">
                      {email}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="mt-2 rounded-md border border-emerald-300 bg-emerald-50 p-4 text-center text-emerald-800">
                  当前模板里的目标邮箱都已经进入发送序列，没有发现明显漏发。
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
