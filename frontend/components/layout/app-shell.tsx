"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { BarChart3, Bolt, FileText, Gauge, Home, Settings2, Sparkles, Upload } from "lucide-react";

import { cn } from "@/lib/utils";

const navigation = [
  { href: "/", label: "Home", icon: Home },
  { href: "/upload", label: "Dataset Upload", icon: Upload },
  { href: "/dashboard", label: "Dashboard", icon: BarChart3 },
  { href: "/forecasting", label: "Forecasting", icon: Gauge },
  { href: "/anomalies", label: "Anomaly Detection", icon: Bolt },
  { href: "/costs", label: "Cost Estimation", icon: Sparkles },
  { href: "/recommendations", label: "Recommendations", icon: FileText },
  { href: "/reports", label: "Reports", icon: FileText },
  { href: "/settings", label: "Settings", icon: Settings2 },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="mx-auto grid min-h-screen max-w-[1600px] gap-6 px-4 py-4 lg:grid-cols-[280px_1fr] lg:px-6">
      <aside className="rounded-[32px] border border-white/60 bg-[linear-gradient(180deg,rgba(22,50,79,0.98),rgba(6,18,31,0.96))] p-6 text-white shadow-[0_35px_80px_-50px_rgba(2,6,23,0.9)]">
        <div>
          <p className="text-xs uppercase tracking-[0.35em] text-white/60">Energy AI</p>
          <h1 className="mt-3 font-display text-2xl font-semibold leading-tight">
            Consumption Optimization System
          </h1>
          <p className="mt-3 text-sm text-white/70">
            Forecast, detect waste, estimate costs, and generate recommendations from one local analytics workspace.
          </p>
        </div>

        <nav className="mt-8 space-y-2">
          {navigation.map(({ href, label, icon: Icon }) => {
            const active = pathname === href;
            return (
              <Link
                key={href}
                href={href}
                className={cn(
                  "flex items-center gap-3 rounded-2xl px-4 py-3 text-sm transition",
                  active
                    ? "bg-white text-[#09233b] shadow-lg"
                    : "text-white/75 hover:bg-white/10 hover:text-white",
                )}
              >
                <Icon className="h-4 w-4" />
                <span>{label}</span>
              </Link>
            );
          })}
        </nav>

        <div className="mt-10 rounded-[24px] border border-white/10 bg-white/8 p-4">
          <p className="text-xs uppercase tracking-[0.3em] text-white/50">Local Run</p>
          <p className="mt-2 text-sm text-white/80">Frontend expects the FastAPI backend at http://127.0.0.1:8000/api.</p>
        </div>
      </aside>

      <main className="min-w-0 py-2">{children}</main>
    </div>
  );
}
