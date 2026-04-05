import { useQuery } from "@tanstack/react-query";
import { Link } from "@tanstack/react-router";
import { api, AutomationJob } from "@/api/client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Plus, Crosshair, Users, Loader2, Globe, Clock, MapPin, Tag, Mail, Send, AlertTriangle, Workflow, Reply, Bell } from "lucide-react";

function formatTime(iso: string) {
  if (!iso) return "";
  try {
    const d = new Date(iso);
    return d.toLocaleString(undefined, {
      month: "short", day: "numeric", hour: "2-digit", minute: "2-digit",
    });
  } catch {
    return "";
  }
}

function jobTitle(job: { website_url: string; product_keywords: string[]; job_id: string }) {
  if (job.website_url) {
    try {
      return new URL(job.website_url).hostname.replace(/^www\./, "");
    } catch { /* fall through */ }
  }
  if (job.product_keywords?.length) {
    return job.product_keywords.slice(0, 2).join(", ");
  }
  return job.job_id.slice(0, 8);
}

function getStatusLabel(status: string) {
  if (status === "completed") return "已完成";
  if (status === "running") return "进行中";
  if (status === "failed") return "失败";
  if (status === "queued") return "排队中";
  return "待处理";
}

function queueStatusVariant(job: AutomationJob) {
  if (job.status === "failed") return "destructive" as const;
  if (job.status === "running") return "warning" as const;
  if (job.status === "completed") return "success" as const;
  if (job.attempt_count > 1 || job.last_error) return "warning" as const;
  return "secondary" as const;
}

export function DashboardPage() {
  const { data: jobs, isLoading, isFetching, error: jobsError } = useQuery({
    queryKey: ["automation-jobs"],
    queryFn: api.listAutomationJobs,
    refetchInterval: 5000,
  });
  const { data: automationStatus, error: statusError } = useQuery({
    queryKey: ["automation-status"],
    queryFn: api.getAutomationStatus,
    refetchInterval: 5000,
  });
  const { data: automationMetrics, error: metricsError } = useQuery({
    queryKey: ["automation-metrics", 24],
    queryFn: () => api.getAutomationMetrics(24),
    refetchInterval: 10000,
  });
  const { data: settings } = useQuery({
    queryKey: ["app-settings"],
    queryFn: api.getSettings,
    refetchInterval: 15000,
  });
  const jobList = jobs ?? [];
  const consumer = automationStatus?.workers?.consumer;
  const dashboardErrors = [jobsError, statusError, metricsError].filter(Boolean) as Error[];
  const feishuWebhook = settings?.settings?.AUTOMATION_FEISHU_WEBHOOK_URL || "";
  const feishuConfigured = Boolean(feishuWebhook && !feishuWebhook.includes("****") ? feishuWebhook : feishuWebhook.includes("****"));
  const summaryEnabled = (settings?.settings?.AUTOMATION_SUMMARY_ENABLED || "true") === "true";
  const alertsEnabled = (settings?.settings?.AUTOMATION_ALERTS_ENABLED || "true") === "true";

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">自动化控制台</h1>
          <p className="text-muted-foreground mt-1">前端负责提交 queue job，后端 consumer 负责准备模板 seed、执行 hunt、创建 campaign 和发送队列</p>
        </div>
        <Link to="/hunts/new">
          <Button>
            <Plus className="h-4 w-4 mr-2" />
            新建任务
          </Button>
        </Link>
      </div>

      {dashboardErrors.length > 0 && (
        <Card className="border-amber-300">
          <CardHeader>
            <CardTitle className="text-lg">数据加载异常</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm text-amber-700">
            {dashboardErrors.map((err, index) => (
              <div key={`${err.message}-${index}`}>{err.message}</div>
            ))}
            <div className="text-muted-foreground">
              如果你刚更新了后端或前端，请重启 dev 服务后再刷新。
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-6">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">任务队列</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2 text-2xl font-semibold">
                <Workflow className="h-5 w-5 text-muted-foreground" />
                {(automationStatus?.hunt_jobs.queued || 0) + (automationStatus?.hunt_jobs.running || 0)}
              </div>
              <p className="mt-1 text-xs text-muted-foreground">
                排队 {automationStatus?.hunt_jobs.queued || 0} · 运行 {automationStatus?.hunt_jobs.running || 0} · 重试中 {automationMetrics?.hunt_jobs.retrying || 0}
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Consumer</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2 text-2xl font-semibold">
                <Workflow className="h-5 w-5 text-muted-foreground" />
                {consumer?.running ? "在线" : "离线"}
              </div>
              <p className="mt-1 text-xs text-muted-foreground">
                {consumer?.active_job_id
                  ? `正在处理 ${consumer.active_job_id.slice(0, 8)}`
                  : "当前没有正在执行的 queue job"}
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">新增企业</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2 text-2xl font-semibold">
                <Users className="h-5 w-5 text-muted-foreground" />
                {automationMetrics?.hunts.new_leads || 0}
              </div>
              <p className="mt-1 text-xs text-muted-foreground">
                最近 {automationMetrics?.window_hours || 24} 小时完成 {automationMetrics?.hunts.completed || 0} 个 hunt
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">邮件发送</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2 text-2xl font-semibold">
                <Send className="h-5 w-5 text-muted-foreground" />
                {automationMetrics?.emails.sent || 0}
              </div>
              <p className="mt-1 text-xs text-muted-foreground">
                待发 {automationStatus?.email_queue.pending || 0} · 失败 {automationMetrics?.emails.failed || 0} · 回复 {automationMetrics?.emails.replied || 0}
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Campaign</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2 text-2xl font-semibold">
                <Mail className="h-5 w-5 text-muted-foreground" />
                {automationStatus?.email_queue.active_campaigns || 0}
              </div>
              <p className="mt-1 text-xs text-muted-foreground">
                活跃序列 {automationStatus?.email_queue.active_sequences || 0} · 已回复序列 {automationStatus?.email_queue.replied_sequences || 0}
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">飞书通知</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2 text-2xl font-semibold">
                <Bell className="h-5 w-5 text-muted-foreground" />
                {feishuConfigured ? "已配置" : "未配置"}
              </div>
              <p className="mt-1 text-xs text-muted-foreground">
                {feishuConfigured
                  ? `汇总 ${summaryEnabled ? "已开" : "已关"} · 告警 ${alertsEnabled ? "已开" : "已关"}`
                  : "去系统设置填写 webhook 并点测试通知"}
              </p>
              <div className="mt-3">
                <Link to="/settings" className="text-xs text-primary hover:underline">
                  前往通知设置
                </Link>
              </div>
            </CardContent>
          </Card>
      </div>

      {automationMetrics?.recent_failed_hunts?.length ? (
        <Card className="border-amber-300">
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-amber-600" />
              最近失败任务
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {automationMetrics.recent_failed_hunts.slice(0, 3).map((hunt) => (
              <div key={hunt.hunt_id} className="rounded-md border p-3 text-sm">
                <p className="font-medium">{hunt.website_url || hunt.hunt_id}</p>
                <p className="text-muted-foreground">
                  阶段 {hunt.current_stage || "-"} · 重试状态 {hunt.retry_status || "-"} · 已尝试 {hunt.retry_attempts || 0} 次
                </p>
                <p className="mt-1 text-destructive">{hunt.error || "未知错误"}</p>
              </div>
            ))}
          </CardContent>
        </Card>
      ) : null}

      {automationStatus?.hunts.running_details?.length ? (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">正在运行的 Hunt</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {automationStatus.hunts.running_details.map((hunt) => (
              <div key={hunt.hunt_id} className="rounded-md border p-3 text-sm">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <p className="font-medium">{hunt.website_url || hunt.hunt_id}</p>
                    <p className="text-muted-foreground">
                      当前阶段 {hunt.current_stage || "-"} · 已发现 {hunt.leads_count} 家企业 · 邮件序列 {hunt.email_sequences_count}
                    </p>
                  </div>
                  <Link to="/hunts/$huntId" params={{ huntId: hunt.hunt_id }} className="text-primary hover:underline">
                    查看详情
                  </Link>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      ) : null}

      {(automationMetrics?.recent_completed_hunts?.length || automationMetrics?.recent_sent_messages?.length || automationMetrics?.recent_reply_events?.length) ? (
        <div className="grid gap-4 xl:grid-cols-3">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">最近发现企业</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              {automationMetrics?.recent_completed_hunts?.length ? automationMetrics.recent_completed_hunts.slice(0, 5).map((hunt) => (
                <div key={hunt.hunt_id} className="rounded-md border p-3">
                  <p className="font-medium">{hunt.website_url || hunt.hunt_id}</p>
                  <p className="text-muted-foreground">
                    新增企业 {hunt.lead_count} · 生成序列 {hunt.email_sequence_count}
                  </p>
                </div>
              )) : (
                <div className="rounded-md border border-dashed p-6 text-center text-muted-foreground">暂无最近发现企业</div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg">最近发送邮件</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              {automationMetrics?.recent_sent_messages?.length ? automationMetrics.recent_sent_messages.slice(0, 5).map((message) => (
                <div key={message.id} className="rounded-md border p-3">
                  <p className="font-medium">{message.lead_name || message.lead_email}</p>
                  <p className="text-muted-foreground break-all">{message.lead_email}</p>
                  <p className="mt-1">{message.subject || "-"}</p>
                  <p className="mt-1 text-xs text-muted-foreground">{formatTime(message.sent_at)}</p>
                </div>
              )) : (
                <div className="rounded-md border border-dashed p-6 text-center text-muted-foreground">暂无最近发送邮件</div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <Reply className="h-4 w-4 text-muted-foreground" />
                最近回复
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              {automationMetrics?.recent_reply_events?.length ? automationMetrics.recent_reply_events.slice(0, 5).map((reply) => (
                <div key={reply.id} className="rounded-md border p-3">
                  <p className="font-medium">{reply.lead_name || reply.from_email}</p>
                  <p className="text-muted-foreground break-all">{reply.from_email}</p>
                  <p className="mt-1">{reply.subject || "-"}</p>
                  <p className="mt-1 text-xs text-muted-foreground line-clamp-2">{reply.snippet || "无摘要"}</p>
                </div>
              )) : (
                <div className="rounded-md border border-dashed p-6 text-center text-muted-foreground">暂无最近回复</div>
              )}
            </CardContent>
          </Card>
        </div>
      ) : null}

      {isLoading ? (
        <Card className="border-dashed">
          <CardContent className="flex items-center justify-center gap-3 py-16 text-muted-foreground">
            <Loader2 className="h-6 w-6 animate-spin" />
            <span>正在加载队列任务…</span>
          </CardContent>
        </Card>
      ) : !jobList.length ? (
        <Card className="border-dashed">
          <CardContent className="flex flex-col items-center justify-center py-16">
            <Crosshair className="h-12 w-12 text-muted-foreground mb-4" />
          <h3 className="text-lg font-semibold mb-2">还没有排队任务</h3>
          <p className="text-muted-foreground mb-6">开始你的第一个生产者消费者任务</p>
            <Link to="/hunts/new">
              <Button>
                <Plus className="h-4 w-4 mr-2" />
                创建任务
              </Button>
            </Link>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          <div className="flex items-center justify-between text-sm text-muted-foreground">
            <span>队列任务</span>
            {isFetching && (
              <span className="inline-flex items-center gap-2">
                <Loader2 className="h-4 w-4 animate-spin" />
                正在刷新
              </span>
            )}
          </div>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {jobList.map((job) => {
            const detailLink = job.last_hunt_id ? (
              <Link to="/hunts/$huntId" params={{ huntId: job.last_hunt_id }} className="text-primary hover:underline">
                查看 Hunt 详情
              </Link>
            ) : null;
            return (
              <Card key={job.job_id} className="hover:shadow-md transition-shadow">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium truncate max-w-[70%]">
                    <Link to="/automation/$jobId" params={{ jobId: job.job_id }} className="hover:underline">
                      {jobTitle(job)}
                    </Link>
                  </CardTitle>
                  <Badge variant={queueStatusVariant(job)}>{getStatusLabel(job.status)}</Badge>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex items-center gap-4">
                    <div className="flex items-center gap-1.5 text-2xl font-bold">
                      <Users className="h-5 w-5 text-muted-foreground" />
                      {job.leads_count}
                      <span className="text-sm font-normal text-muted-foreground">线索</span>
                    </div>
                  </div>
                  <div className="space-y-1.5 text-xs text-muted-foreground">
                    {job.product_keywords?.length > 0 && (
                      <div className="flex items-center gap-1.5 truncate">
                        <Tag className="h-3 w-3 shrink-0" />
                        <span className="truncate">{job.product_keywords.join(", ")}</span>
                      </div>
                    )}
                    {job.target_regions?.length > 0 && (
                      <div className="flex items-center gap-1.5 truncate">
                        <MapPin className="h-3 w-3 shrink-0" />
                        <span className="truncate">{job.target_regions.join(", ")}</span>
                      </div>
                    )}
                    {job.website_url && (
                      <div className="flex items-center gap-1.5 truncate">
                        <Globe className="h-3 w-3 shrink-0" />
                        <span className="truncate">{job.website_url}</span>
                      </div>
                    )}
                    {job.created_at && (
                      <div className="flex items-center gap-1.5">
                        <Clock className="h-3 w-3 shrink-0" />
                        <span>{formatTime(job.created_at)}</span>
                        <span className="ml-1">· 尝试 {job.attempt_count}</span>
                      </div>
                    )}
                  {job.hunt_stage && (
                    <div>当前阶段：{job.hunt_stage}</div>
                  )}
                  {job.progress_stage && (
                    <div>队列阶段：{job.progress_stage}</div>
                  )}
                  <div>模板 Seed：{job.template_seed_status || "pending"}</div>
                  {job.last_error && (
                    <div className="text-destructive">最近错误：{job.last_error}</div>
                  )}
                    <Link to="/automation/$jobId" params={{ jobId: job.job_id }} className="text-primary hover:underline">
                      查看队列任务详情
                    </Link>
                    {detailLink}
                  </div>
                </CardContent>
              </Card>
            );
          })}
          </div>
        </div>
      )}
    </div>
  );
}
