import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Settings, Clock3 } from "lucide-react";

export function SettingsPage() {
  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">系统设置</h1>
        <p className="text-muted-foreground mt-1">当前版本暂不开放浏览器端配置入口。</p>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Settings className="h-5 w-5 text-primary" />
            <CardTitle className="text-lg">功能状态</CardTitle>
            <Badge variant="secondary">待开发</Badge>
          </div>
          <CardDescription>
            为避免误操作和服务端配置暴露，设置页已临时下线，后续会以更安全的方式重新开放。
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4 text-sm text-muted-foreground">
          <div className="rounded-lg border bg-muted/40 p-4">
            <p className="font-medium text-foreground mb-1">当前建议</p>
            <p>模型、搜索和运行参数请直接通过后端环境变量维护，前端暂不提供在线修改能力。</p>
          </div>

          <div className="flex items-center gap-2 rounded-lg border border-dashed p-4">
            <Clock3 className="h-4 w-4 shrink-0" />
            <p>该页面后续会以“待开发功能”方式逐步恢复。</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
