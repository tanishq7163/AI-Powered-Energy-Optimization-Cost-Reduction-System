import Link from "next/link";
import { ArrowRight, BarChart3, BrainCircuit, FileBarChart2, Upload } from "lucide-react";

import { AppShell } from "@/components/layout/app-shell";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";

const modules = [
  {
    title: "Data Ingestion & Cleaning",
    description: "Import CSV or Excel files, add manual records, validate schema, and preprocess features automatically.",
    icon: Upload,
  },
  {
    title: "Forecasting Engine",
    description: "Compare Linear Regression, Random Forest, XGBoost, Prophet, and LSTM, then pick the best performer by RMSE.",
    icon: BrainCircuit,
  },
  {
    title: "Analytics Dashboard",
    description: "Explore trends, anomalies, peak-hour heatmaps, cost breakdowns, and savings opportunities from one workspace.",
    icon: BarChart3,
  },
  {
    title: "Reports & Recommendations",
    description: "Generate PDF summaries with optimization actions tied to anomalies, forecast pressure, and tariff exposure.",
    icon: FileBarChart2,
  },
];

export default function HomePage() {
  return (
    <AppShell>
      <section className="rounded-[32px] bg-[linear-gradient(135deg,#fffaf4_0%,#ffffff_50%,#f0fdfa_100%)] px-6 py-8 shadow-[0_30px_100px_-70px_rgba(15,23,42,0.6)] lg:px-10 lg:py-12">
        <p className="text-sm uppercase tracking-[0.35em] text-[var(--muted-foreground)]">AI Energy Intelligence</p>
        <div className="mt-5 grid gap-10 lg:grid-cols-[1.4fr_0.9fr] lg:items-end">
          <div>
            <h1 className="max-w-4xl font-display text-4xl font-semibold leading-tight text-[#10253e] md:text-6xl">
              Cut energy waste, forecast demand, and surface savings opportunities with a local AI analytics stack.
            </h1>
            <p className="mt-5 max-w-2xl text-base leading-8 text-[var(--muted-foreground)]">
              This platform combines ingestion, preprocessing, forecasting, anomaly detection, cost estimation, recommendations, and PDF reporting across a full FastAPI + Next.js workflow.
            </p>
            <div className="mt-8 flex flex-wrap gap-4">
              <Link
                href="/upload"
                className="inline-flex items-center gap-2 rounded-full bg-[var(--accent)] px-6 py-3 font-semibold text-white"
              >
                Upload dataset
                <ArrowRight className="h-4 w-4" />
              </Link>
              <Link
                href="/dashboard"
                className="inline-flex items-center gap-2 rounded-full border border-black/10 bg-white px-6 py-3 font-semibold"
              >
                Open dashboard
              </Link>
            </div>
          </div>

          <Card className="bg-[#16324f] text-white">
            <CardDescription className="text-white/70">System workflow</CardDescription>
            <CardTitle className="mt-3 text-white">Ingest → Clean → Analyze → Forecast → Detect → Recommend</CardTitle>
            <div className="mt-6 grid gap-3 text-sm text-white/75">
              <p>1. Upload energy records or generate synthetic data.</p>
              <p>2. Engineer time-based features and remove noise.</p>
              <p>3. Compare forecasting models and monitor anomalies.</p>
              <p>4. Convert usage into costs and optimization actions.</p>
            </div>
          </Card>
        </div>
      </section>

      <section className="mt-8 grid gap-5 lg:grid-cols-2 2xl:grid-cols-4">
        {modules.map(({ title, description, icon: Icon }) => (
          <Card key={title} className="group transition hover:-translate-y-1 hover:shadow-[0_28px_80px_-60px_rgba(15,23,42,0.9)]">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-[#eff6ff] text-[#0f766e]">
              <Icon className="h-5 w-5" />
            </div>
            <CardTitle className="mt-5">{title}</CardTitle>
            <CardDescription className="mt-3 leading-7">{description}</CardDescription>
          </Card>
        ))}
      </section>
    </AppShell>
  );
}
