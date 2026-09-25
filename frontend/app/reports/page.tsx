"use client";

import { useState } from "react";

import { AppShell } from "@/components/layout/app-shell";
import { Button } from "@/components/ui/button";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { apiRequest, downloadUrl } from "@/lib/api";
import type { ReportItem } from "@/lib/types";
import { formatDateTime } from "@/lib/utils";

export default function ReportsPage() {
  const [reports, setReports] = useState<ReportItem[]>([]);
  const [message, setMessage] = useState<string>("Generate a PDF report to list it here.");

  async function refreshReports() {
    const response = await apiRequest<ReportItem[]>("/reports");
    setReports(response);
  }

  async function generateReport() {
    try {
      setMessage("Generating PDF report...");
      const response = await apiRequest<ReportItem>("/reports/generate", { method: "POST" });
      setMessage(`Generated ${response.report_name}`);
      await refreshReports();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Report generation failed.");
    }
  }

  return (
    <AppShell>
      <div className="space-y-6">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <h1 className="font-display text-4xl font-semibold">Reports</h1>
            <p className="mt-2 text-[var(--muted-foreground)]">
              Generate and export PDF reports containing summary metrics, forecast output, anomaly findings, costs, and recommendations.
            </p>
          </div>
          <div className="flex gap-3">
            <Button onClick={() => void generateReport()}>Generate PDF report</Button>
            <Button variant="secondary" onClick={() => void refreshReports()}>Refresh list</Button>
          </div>
        </div>

        <Card>
          <CardTitle>Generated reports</CardTitle>
          <CardDescription className="mt-2">{message}</CardDescription>
          <div className="mt-6 space-y-4">
            {reports.map((report) => (
              <div key={report.id} className="flex flex-col gap-3 rounded-[24px] border border-black/8 bg-[#f8fafc] p-4 lg:flex-row lg:items-center lg:justify-between">
                <div>
                  <p className="font-semibold">{report.report_name}</p>
                  <p className="mt-1 text-sm text-[var(--muted-foreground)]">{formatDateTime(report.created_at)}</p>
                </div>
                <a
                  href={downloadUrl(`/reports/download?path=${encodeURIComponent(report.file_path)}`)}
                  className="inline-flex h-11 items-center justify-center rounded-full bg-[#16324f] px-5 text-sm font-semibold text-white"
                >
                  Download report
                </a>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </AppShell>
  );
}
