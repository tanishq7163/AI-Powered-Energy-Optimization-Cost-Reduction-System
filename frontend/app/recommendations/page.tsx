"use client";

import { PageState } from "@/components/common/page-state";
import { AppShell } from "@/components/layout/app-shell";
import { Badge } from "@/components/ui/badge";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { useApiResource } from "@/hooks/use-api-resource";
import type { RecommendationResponse } from "@/lib/types";
import { formatCurrency } from "@/lib/utils";

export default function RecommendationsPage() {
  const { data, error, loading } = useApiResource<RecommendationResponse>("/recommendations/generate");

  return (
    <AppShell>
      <div className="space-y-6">
        <div>
          <h1 className="font-display text-4xl font-semibold">Recommendations</h1>
          <p className="mt-2 text-[var(--muted-foreground)]">
            Dynamic actions generated from consumption patterns, anomalies, forecast pressure, and cost concentration.
          </p>
        </div>

        {loading ? <PageState title="Generating recommendations" description="Analyzing patterns and preparing optimization actions." /> : null}
        {error ? <PageState title="Unable to generate recommendations" description={error} /> : null}

        {data ? (
          <div className="grid gap-5 xl:grid-cols-2">
            {data.recommendations.map((recommendation) => (
              <Card key={`${recommendation.category}-${recommendation.title}`}>
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <CardDescription>{recommendation.category}</CardDescription>
                    <CardTitle className="mt-2">{recommendation.title}</CardTitle>
                  </div>
                  <Badge>{recommendation.priority}</Badge>
                </div>
                <p className="mt-4 text-sm leading-7 text-[var(--muted-foreground)]">{recommendation.description}</p>
                <p className="mt-5 text-sm font-semibold text-[#0f766e]">
                  Estimated savings {formatCurrency(recommendation.estimated_savings)}
                </p>
              </Card>
            ))}
          </div>
        ) : null}
      </div>
    </AppShell>
  );
}
