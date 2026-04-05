import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useParams } from "@tanstack/react-router";
import { api } from "@/api/client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Clock, Globe, Loader2, RotateCcw, Target, Workflow } from "lucide-react";

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

export function AutomationJobPage() {
  const { jobId } = useParams({ from: "/automation/$jobId" });
  const queryClient = useQueryClient();
  const { data: job, isLoading, error } = useQuery({
    queryKey: ["automation-job", jobId],
    queryFn: () => api.getAutomationJob(jobId),
    refetchInterval: 5000,
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
      </div>

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
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>执行链路</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
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
    </div>
  );
}
