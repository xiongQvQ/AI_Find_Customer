import { useQuery } from "@tanstack/react-query";
import { Link } from "@tanstack/react-router";
import { api } from "@/api/client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Plus, Crosshair, Users, Loader2, Globe, Clock, MapPin, Tag } from "lucide-react";

const statusVariant = (s: string) => {
  switch (s) {
    case "completed": return "success" as const;
    case "running": return "warning" as const;
    case "failed": return "destructive" as const;
    default: return "secondary" as const;
  }
};

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

function huntTitle(hunt: { website_url: string; product_keywords: string[]; hunt_id: string }) {
  if (hunt.website_url) {
    try {
      return new URL(hunt.website_url).hostname.replace(/^www\./, "");
    } catch { /* fall through */ }
  }
  if (hunt.product_keywords?.length) {
    return hunt.product_keywords.slice(0, 2).join(", ");
  }
  return hunt.hunt_id.slice(0, 8);
}

function getStatusLabel(status: string) {
  if (status === "completed") return "已完成";
  if (status === "running") return "进行中";
  if (status === "failed") return "失败";
  return "待处理";
}

export function DashboardPage() {
  const { data: hunts, isLoading } = useQuery({
    queryKey: ["hunts"],
    queryFn: api.listHunts,
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
      ) : !hunts?.length ? (
        <Card className="border-dashed">
          <CardContent className="flex flex-col items-center justify-center py-16">
            <Crosshair className="h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">还没有任务</h3>
            <p className="text-muted-foreground mb-6">开始你的第一个 AI 获客任务</p>
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
          {hunts.map((hunt) => (
            <Link key={hunt.hunt_id} to="/hunts/$huntId" params={{ huntId: hunt.hunt_id }}>
              <Card className="hover:shadow-md transition-shadow cursor-pointer">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium truncate max-w-[70%]">
                    {huntTitle(hunt)}
                  </CardTitle>
                  <Badge variant={statusVariant(hunt.status)}>{getStatusLabel(hunt.status)}</Badge>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex items-center gap-4">
                    <div className="flex items-center gap-1.5 text-2xl font-bold">
                      <Users className="h-5 w-5 text-muted-foreground" />
                      {hunt.leads_count}
                      <span className="text-sm font-normal text-muted-foreground">线索</span>
                    </div>
                  </div>
                  <div className="space-y-1.5 text-xs text-muted-foreground">
                    {hunt.product_keywords?.length > 0 && (
                      <div className="flex items-center gap-1.5 truncate">
                        <Tag className="h-3 w-3 shrink-0" />
                        <span className="truncate">{hunt.product_keywords.join(", ")}</span>
                      </div>
                    )}
                    {hunt.target_regions?.length > 0 && (
                      <div className="flex items-center gap-1.5 truncate">
                        <MapPin className="h-3 w-3 shrink-0" />
                        <span className="truncate">{hunt.target_regions.join(", ")}</span>
                      </div>
                    )}
                    {hunt.website_url && (
                      <div className="flex items-center gap-1.5 truncate">
                        <Globe className="h-3 w-3 shrink-0" />
                        <span className="truncate">{hunt.website_url}</span>
                      </div>
                    )}
                    {hunt.created_at && (
                      <div className="flex items-center gap-1.5">
                        <Clock className="h-3 w-3 shrink-0" />
                        <span>{formatTime(hunt.created_at)}</span>
                        {hunt.hunt_round > 0 && (
                          <span className="ml-1">· 第 {hunt.hunt_round} 轮</span>
                        )}
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
