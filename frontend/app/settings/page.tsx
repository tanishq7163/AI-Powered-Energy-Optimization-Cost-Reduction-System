"use client";

import { PageState } from "@/components/common/page-state";
import { AppShell } from "@/components/layout/app-shell";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { useApiResource } from "@/hooks/use-api-resource";
import type { SettingsResponse } from "@/lib/types";

export default function SettingsPage() {
  const { data, error, loading } = useApiResource<SettingsResponse>("/settings");

  return (
    <AppShell>
      <div className="space-y-6">
        <div>
          <h1 className="font-display text-4xl font-semibold">Settings</h1>
          <p className="mt-2 text-[var(--muted-foreground)]">
            Environment and local storage paths used by the project runtime.
          </p>
        </div>

        {loading ? <PageState title="Loading settings" description="Reading backend configuration and storage directories." /> : null}
        {error ? <PageState title="Unable to load settings" description={error} /> : null}

        {data ? (
          <Card>
            <CardTitle>Runtime configuration</CardTitle>
            <CardDescription className="mt-2">Values are returned directly from the backend environment.</CardDescription>
            <div className="mt-6 grid gap-4 md:grid-cols-2">
              {Object.entries(data).map(([key, value]) => (
                <div key={key} className="rounded-[24px] border border-black/8 bg-[#f8fafc] p-4">
                  <p className="text-xs uppercase tracking-[0.28em] text-[var(--muted-foreground)]">{key}</p>
                  <p className="mt-2 break-all text-sm font-semibold">{String(value)}</p>
                </div>
              ))}
            </div>
          </Card>
        ) : null}
      </div>
    </AppShell>
  );
}