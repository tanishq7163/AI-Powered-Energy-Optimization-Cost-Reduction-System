import { ArrowDownRight, ArrowUpRight, Minus } from "lucide-react";

import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

type MetricCardProps = {
  label: string;
  value: string;
  tone?: "up" | "down" | "neutral";
  hint: string;
};

export function MetricCard({ label, value, tone = "neutral", hint }: MetricCardProps) {
  const Icon = tone === "up" ? ArrowUpRight : tone === "down" ? ArrowDownRight : Minus;

  return (
    <Card className="overflow-hidden">
      <div className="flex items-start justify-between gap-4">
        <div>
          <CardDescription>{label}</CardDescription>
          <CardTitle className="mt-3 text-3xl">{value}</CardTitle>
        </div>
        <div
          className={cn(
            "rounded-full p-2",
            tone === "up" && "bg-[#ecfdf3] text-[#039855]",
            tone === "down" && "bg-[#fff1f2] text-[#e11d48]",
            tone === "neutral" && "bg-[#f8fafc] text-[#334155]",
          )}
        >
          <Icon className="h-4 w-4" />
        </div>
      </div>
      <p className="mt-4 text-sm text-[var(--muted-foreground)]">{hint}</p>
    </Card>
  );
}
