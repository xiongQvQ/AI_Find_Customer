import { Link, Outlet } from "@tanstack/react-router";
import { Crosshair, Plus, LayoutDashboard, Settings } from "lucide-react";

// TODO: License gate is temporarily disabled for desktop functionality testing.
// To re-enable: restore the full LicenseGate component from git history.
function LicenseGate({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}

export function RootLayout() {
  return (
    <LicenseGate>
      <div className="min-h-screen bg-background">
        <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
          <div className="container flex h-14 items-center mx-auto px-4">
            <Link to="/" className="flex items-center gap-2 font-bold text-lg mr-8">
              <Crosshair className="h-5 w-5 text-primary" />
              <span>AI Hunter</span>
            </Link>
            <nav className="flex items-center gap-4 text-sm">
              <Link
                to="/"
                className="flex items-center gap-1.5 text-muted-foreground hover:text-foreground transition-colors [&.active]:text-foreground"
              >
                <LayoutDashboard className="h-4 w-4" />
                Dashboard
              </Link>
              <Link
                to="/hunts/new"
                className="flex items-center gap-1.5 text-muted-foreground hover:text-foreground transition-colors [&.active]:text-foreground"
              >
                <Plus className="h-4 w-4" />
                New Hunt
              </Link>
            </nav>
            <div className="ml-auto">
              <Link
                to="/settings"
                className="flex items-center gap-1.5 text-muted-foreground hover:text-foreground transition-colors [&.active]:text-foreground text-sm"
              >
                <Settings className="h-4 w-4" />
                Settings
              </Link>
            </div>
          </div>
        </header>
        <main className="container mx-auto px-4 py-8">
          <Outlet />
        </main>
      </div>
    </LicenseGate>
  );
}
