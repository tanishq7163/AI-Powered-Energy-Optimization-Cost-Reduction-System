"use client";

import { AnomalyPlot } from "@/components/charts/anomaly-plot";
import { PageState } from "@/components/common/page-state";
import { AppShell } from "@/components/layout/app-shell";
import { Badge } from "@/components/ui/badge";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { useApiResource } from "@/hooks/use-api-resource";
import type { AnomalyResponse } from "@/lib/types";
import { formatDateTime, formatNumber } from "@/lib/utils";

export default function AnomaliesPage() {
  const { data, error, loading } = useApiResource<AnomalyResponse>("/anomalies/detect");

  return (
    <AppShell>
      <div className="space-y-6">
        <div>
          <h1 className="font-display text-4xl font-semibold">Anomaly Detection</h1>
          <p className="mt-2 text-[var(--muted-foreground)]">
            Isolation Forest and Local Outlier Factor identify sudden spikes, unusual usage, and probable energy waste patterns.
          </p>
        </div>

        {loading ? <PageState title="Detecting anomalies" description="Running anomaly scoring across the current energy dataset." /> : null}
        {error ? <PageState title="Unable to detect anomalies" description={error} /> : null}

        {data ? (
          <>
            <Card>
              <CardTitle>Anomaly Visualization</CardTitle>
              <CardDescription className="mt-2">Bubble size and color intensity reflect anomaly score severity.</CardDescription>
              <div className="mt-6">
                <AnomalyPlot anomalies={data.anomalies} />
              </div>
            </Card>

            <Card>
              <CardTitle>Flagged Events</CardTitle>
              <CardDescription className="mt-2">Top detected anomalies ranked by score.</CardDescription>
              <div className="mt-6 space-y-4">
                {data.anomalies.map((anomaly) => (
                  <div key={`${anomaly.timestamp}-${anomaly.device_name}`} className="rounded-[24px] border border-black/8 bg-[#f8fafc] p-4">
                    <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                      <div>
                        <p className="font-semibold">{anomaly.device_name}</p>
                        <p className="mt-1 text-sm text-[var(--muted-foreground)]">{formatDateTime(anomaly.timestamp)}</p>
                        <p className="mt-3 text-sm leading-7 text-[var(--muted-foreground)]">{anomaly.description}</p>
                      </div>
                      <div className="flex items-center gap-3">
                        <Badge>{anomaly.severity_level}</Badge>
                        <span className="text-sm font-semibold">Score {formatNumber(anomaly.anomaly_score, 3)}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          </>
        ) : null}
      </div>
    </AppShell>
  );
}
