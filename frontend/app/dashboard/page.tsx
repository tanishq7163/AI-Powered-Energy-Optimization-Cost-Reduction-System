"use client";

import { useMemo, useState } from "react";

import { ConsumptionLineChart } from "@/components/charts/consumption-line-chart";
import { CostBreakdownChart } from "@/components/charts/cost-breakdown-chart";
import { PeakHeatmap } from "@/components/charts/peak-heatmap";
import { MetricCard } from "@/components/common/metric-card";
import { PageState } from "@/components/common/page-state";
import { AppShell } from "@/components/layout/app-shell";
import { Button } from "@/components/ui/button";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useApiResource } from "@/hooks/use-api-resource";
import type { AnalyticsSummary, DashboardResponse } from "@/lib/types";
import { formatCurrency, formatNumber } from "@/lib/utils";

export default function DashboardPage() {
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const query = useMemo(() => {
    const params = new URLSearchParams();
    if (startDate) {
      params.set("start_date", startDate);
    }
    if (endDate) {
      params.set("end_date", endDate);
    }
    const queryString = params.toString();
    return `/analytics${queryString ? `?${queryString}` : ""}`;
  }, [endDate, startDate]);

  const { data: analytics, error, loading } = useApiResource<AnalyticsSummary>(query, query);
  const { data: overview } = useApiResource<DashboardResponse>("/dashboard");

  return (
    <AppShell>
      <div className="space-y-6">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <h1 className="font-display text-4xl font-semibold">Analytics Dashboard</h1>
            <p className="mt-2 text-[var(--muted-foreground)]">
              Monitor overall consumption, costs, forecast pressure, heatmap intensity, and device-level trends.
            </p>
          </div>
          <div className="flex flex-wrap items-end gap-3">
            <div>
              <label className="mb-2 block text-sm font-medium">Start date</label>
              <Input type="date" value={startDate} onChange={(event) => setStartDate(event.target.value)} />
            </div>
            <div>
              <label className="mb-2 block text-sm font-medium">End date</label>
              <Input type="date" value={endDate} onChange={(event) => setEndDate(event.target.value)} />
            </div>
            <Button variant="secondary" onClick={() => { setStartDate(""); setEndDate(""); }}>Reset</Button>
          </div>
        </div>

        {loading ? <PageState title="Loading analytics" description="Pulling current energy KPIs from the FastAPI backend." /> : null}
        {error ? <PageState title="Unable to load analytics" description={error} /> : null}

        {analytics ? (
          <>
            <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
              <MetricCard label="Total Consumption" value={`${formatNumber(analytics.total_energy)} kWh`} hint="Aggregated over the selected range." tone="up" />
              <MetricCard label="Estimated Monthly Cost" value={formatCurrency(analytics.estimated_monthly_cost)} hint="Based on current tariff exposure." tone="down" />
              <MetricCard label="Predicted Consumption" value={`${formatNumber(overview?.forecast.forecast[0]?.predicted_consumption_kwh ?? 0)} kWh`} hint="First upcoming forecasted interval." tone="up" />
              <MetricCard label="Savings Opportunity" value={formatCurrency(analytics.savings_opportunity)} hint="Estimated from peak and off-hour inefficiencies." tone="neutral" />
            </section>

            <section className="grid gap-6 2xl:grid-cols-2">
              <Card>
                <CardTitle>Daily Consumption Trend</CardTitle>
                <CardDescription className="mt-2">Daily totals and daily average consumption.</CardDescription>
                <div className="mt-6">
                  <ConsumptionLineChart data={analytics.daily_trend} mode="aggregate" />
                </div>
              </Card>
              <Card>
                <CardTitle>Weekly Trend</CardTitle>
                <CardDescription className="mt-2">Weekly usage progression and rolling average.</CardDescription>
                <div className="mt-6">
                  <ConsumptionLineChart data={analytics.weekly_trend} mode="aggregate" />
                </div>
              </Card>
              <Card>
                <CardTitle>Monthly Trend</CardTitle>
                <CardDescription className="mt-2">Monthly aggregation for long-range planning.</CardDescription>
                <div className="mt-6">
                  <ConsumptionLineChart data={analytics.monthly_trend} mode="aggregate" />
                </div>
              </Card>
              <Card>
                <CardTitle>Cost Breakdown</CardTitle>
                <CardDescription className="mt-2">Cost concentration across the highest-impact devices.</CardDescription>
                <div className="mt-6">
                  <CostBreakdownChart data={analytics.device_breakdown} />
                </div>
              </Card>
            </section>

            <section className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
              <Card>
                <CardTitle>Peak Hour Heatmap</CardTitle>
                <CardDescription className="mt-2">Hour-by-weekday load intensity to expose peak operating windows.</CardDescription>
                <div className="mt-6">
                  <PeakHeatmap data={analytics.peak_hour_heatmap as Array<{ weekday?: number; hour?: number; value?: number }>} />
                </div>
              </Card>
              <Card>
                <CardTitle>Seasonal Profile</CardTitle>
                <CardDescription className="mt-2">Average energy and cost across the seasonal cycle.</CardDescription>
                <div className="mt-6 space-y-4">
                  {analytics.seasonal_profile.map((item) => (
                    <div key={String(item.season)} className="rounded-2xl border border-black/8 bg-[#f8fafc] p-4">
                      <div className="flex items-center justify-between gap-3">
                        <p className="font-semibold capitalize">{String(item.season)}</p>
                        <p className="text-sm text-[var(--muted-foreground)]">
                          Avg energy {formatNumber(Number(item.average_energy))} kWh
                        </p>
                      </div>
                      <p className="mt-2 text-sm text-[var(--muted-foreground)]">
                        Avg cost {formatCurrency(Number(item.average_cost))}
                      </p>
                    </div>
                  ))}
                </div>
              </Card>
            </section>
          </>
        ) : null}
      </div>
    </AppShell>
  );
}
