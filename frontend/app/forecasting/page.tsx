"use client";

import { useState } from "react";

import { ConsumptionLineChart } from "@/components/charts/consumption-line-chart";
import { PageState } from "@/components/common/page-state";
import { AppShell } from "@/components/layout/app-shell";
import { Button } from "@/components/ui/button";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { useApiResource } from "@/hooks/use-api-resource";
import type { ForecastResponse } from "@/lib/types";
import { formatNumber } from "@/lib/utils";

export default function ForecastingPage() {
  const [horizon, setHorizon] = useState<"24h" | "7d" | "30d">("24h");
  const { data, error, loading } = useApiResource<ForecastResponse>(`/forecasts?horizon=${horizon}`, horizon);

  return (
    <AppShell>
      <div className="space-y-6">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <h1 className="font-display text-4xl font-semibold">Forecasting</h1>
            <p className="mt-2 text-[var(--muted-foreground)]">
              Compare model metrics, inspect prediction intervals, and choose between 24-hour, 7-day, and 30-day outlooks.
            </p>
          </div>
          <div className="flex gap-3">
            {(["24h", "7d", "30d"] as const).map((item) => (
              <Button key={item} variant={horizon === item ? "default" : "secondary"} onClick={() => setHorizon(item)}>
                {item}
              </Button>
            ))}
          </div>
        </div>

        {loading ? <PageState title="Generating forecast" description="Running the selected forecasting horizon and loading model comparison metrics." /> : null}
        {error ? <PageState title="Unable to forecast" description={error} /> : null}

        {data ? (
          <>
            <Card>
              <CardTitle>Forecast Chart</CardTitle>
              <CardDescription className="mt-2">Best model selected automatically: {data.best_model}</CardDescription>
              <div className="mt-6">
                <ConsumptionLineChart data={data.forecast} mode="forecast" />
              </div>
            </Card>

            <Card>
              <CardTitle>Model Evaluation</CardTitle>
              <CardDescription className="mt-2">Selection metrics: MAE, MSE, RMSE, MAPE, and R².</CardDescription>
              <div className="mt-6 overflow-x-auto">
                <table className="min-w-full text-left text-sm">
                  <thead>
                    <tr className="border-b border-black/10 text-[var(--muted-foreground)]">
                      <th className="px-3 py-3">Model</th>
                      <th className="px-3 py-3">MAE</th>
                      <th className="px-3 py-3">MSE</th>
                      <th className="px-3 py-3">RMSE</th>
                      <th className="px-3 py-3">MAPE</th>
                      <th className="px-3 py-3">R²</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.metrics.map((metric) => (
                      <tr key={metric.model_name} className="border-b border-black/5">
                        <td className="px-3 py-3 font-medium">{metric.model_name}</td>
                        <td className="px-3 py-3">{formatNumber(metric.mae)}</td>
                        <td className="px-3 py-3">{formatNumber(metric.mse)}</td>
                        <td className="px-3 py-3">{formatNumber(metric.rmse)}</td>
                        <td className="px-3 py-3">{formatNumber(metric.mape)}</td>
                        <td className="px-3 py-3">{formatNumber(metric.r2)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          </>
        ) : null}
      </div>
    </AppShell>
  );
}
