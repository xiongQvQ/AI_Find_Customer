import { Link, Outlet } from "@tanstack/react-router";
import { Crosshair, LayoutDashboard, Plus, Settings } from "lucide-react";

export function RootLayout() {
  return (
    <div className="min-h-screen bg-background">
      <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container mx-auto flex h-14 items-center px-4">
          <Link to="/" className="mr-8 flex items-center gap-2 text-lg font-bold">
            <Crosshair className="h-5 w-5 text-primary" />
            <span>AI Hunter</span>
          </Link>
          <nav className="flex items-center gap-4 text-sm">
            <Link
              to="/"
              className="flex items-center gap-1.5 text-muted-foreground transition-colors hover:text-foreground [&.active]:text-foreground"
            >
              <LayoutDashboard className="h-4 w-4" />
              任务看板
            </Link>
            <Link
              to="/hunts/new"
              className="flex items-center gap-1.5 text-muted-foreground transition-colors hover:text-foreground [&.active]:text-foreground"
            >
              <Plus className="h-4 w-4" />
              新建任务
            </Link>
          </nav>
          <div className="ml-auto">
            <Link
              to="/settings"
              className="flex items-center gap-1.5 text-sm text-muted-foreground transition-colors hover:text-foreground [&.active]:text-foreground"
            >
              <Settings className="h-4 w-4" />
              系统设置
            </Link>
          </div>
        </div>
      </header>
      <main className="container mx-auto px-4 py-8">
        <Outlet />
      </main>
    </div>
  );
}
