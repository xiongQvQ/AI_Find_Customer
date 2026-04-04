import { useQuery } from "@tanstack/react-query";
import { Link } from "@tanstack/react-router";
import { api, AutomationJob } from "@/api/client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Plus, Crosshair, Users, Loader2, Globe, Clock, MapPin, Tag } from "lucide-react";

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
  const { data: jobs, isLoading } = useQuery({
    queryKey: ["automation-jobs"],
    queryFn: api.listAutomationJobs,
    refetchInterval: 5000,
  });

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">任务看板</h1>
          <p className="text-muted-foreground mt-1">管理你的 B2B 智能获客任务</p>
        </div>
        <Link to="/hunts/new">
          <Button>
            <Plus className="h-4 w-4 mr-2" />
            新建任务
          </Button>
        </Link>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      ) : !jobs?.length ? (
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
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {jobs.map((job) => {
            const detailLink = job.last_hunt_id ? (
              <Link to="/hunts/$huntId" params={{ huntId: job.last_hunt_id }} className="text-primary hover:underline">
                查看 Hunt 详情
              </Link>
            ) : null;
            return (
              <Card key={job.job_id} className="hover:shadow-md transition-shadow">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium truncate max-w-[70%]">
                    {jobTitle(job)}
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
                    {job.last_error && (
                      <div className="text-destructive">最近错误：{job.last_error}</div>
                    )}
                    {detailLink}
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
