"use client";

import { CostBreakdownChart } from "@/components/charts/cost-breakdown-chart";
import { MetricCard } from "@/components/common/metric-card";
import { PageState } from "@/components/common/page-state";
import { AppShell } from "@/components/layout/app-shell";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { useApiResource } from "@/hooks/use-api-resource";
import type { CostSummary } from "@/lib/types";
import { formatCurrency, formatNumber } from "@/lib/utils";

export default function CostsPage() {
  const { data, error, loading } = useApiResource<CostSummary>("/costs");

  return (
    <AppShell>
      <div className="space-y-6">
        <div>
          <h1 className="font-display text-4xl font-semibold">Cost Estimation</h1>
          <p className="mt-2 text-[var(--muted-foreground)]">
            Translate demand and tariff patterns into current, daily, weekly, monthly, and forecast cost exposure.
          </p>
        </div>

        {loading ? <PageState title="Calculating costs" description="Loading cost estimations and peak cost contribution." /> : null}
        {error ? <PageState title="Unable to load cost estimations" description={error} /> : null}

        {data ? (
          <>
            <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
              <MetricCard label="Current Cost" value={formatCurrency(data.current_cost)} hint="Latest measured interval." tone="neutral" />
              <MetricCard label="Daily Cost" value={formatCurrency(data.daily_cost)} hint="Rolling 24-hour estimate." tone="up" />
              <MetricCard label="Monthly Cost" value={formatCurrency(data.monthly_cost)} hint="Rolling 30-day estimate." tone="down" />
              <MetricCard label="Potential Savings" value={formatCurrency(data.potential_savings)} hint={`Peak share ${formatNumber(data.peak_cost_contribution * 100)}%`} tone="up" />
            </section>

            <Card>
              <CardTitle>Cost Breakdown Chart</CardTitle>
              <CardDescription className="mt-2">Device-level cost contribution across the highest-impact assets.</CardDescription>
              <div className="mt-6">
                <CostBreakdownChart data={data.breakdown} />
              </div>
            </Card>
          </>
        ) : null}
      </div>
    </AppShell>
  );
}
