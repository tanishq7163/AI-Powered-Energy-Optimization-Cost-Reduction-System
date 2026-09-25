"use client";

import { FormEvent, useState } from "react";

import { AppShell } from "@/components/layout/app-shell";
import { PageState } from "@/components/common/page-state";
import { Button } from "@/components/ui/button";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { apiRequest, downloadUrl, uploadDataset } from "@/lib/api";

type ManualFormState = {
  date: string;
  timestamp: string;
  energy_consumption_kwh: string;
  voltage: string;
  current: string;
  power_factor: string;
  tariff_rate: string;
  temperature: string;
  occupancy: string;
  device_name: string;
};

const initialFormState: ManualFormState = {
  date: "",
  timestamp: "",
  energy_consumption_kwh: "",
  voltage: "230",
  current: "32",
  power_factor: "0.94",
  tariff_rate: "0.12",
  temperature: "24",
  occupancy: "18",
  device_name: "HVAC",
};

export default function UploadPage() {
  const [message, setMessage] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [formState, setFormState] = useState<ManualFormState>(initialFormState);

  async function handleFileChange(fileList: FileList | null) {
    const file = fileList?.[0];
    if (!file) {
      return;
    }

    try {
      setBusy(true);
      const response = await uploadDataset(file);
      setMessage(`${response.message} Imported ${response.imported_rows} cleaned rows.`);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Upload failed.");
    } finally {
      setBusy(false);
    }
  }

  async function handleManualSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    try {
      setBusy(true);
      await apiRequest("/records/manual", {
        method: "POST",
        body: JSON.stringify({
          ...formState,
          energy_consumption_kwh: Number(formState.energy_consumption_kwh),
          voltage: Number(formState.voltage),
          current: Number(formState.current),
          power_factor: Number(formState.power_factor),
          tariff_rate: Number(formState.tariff_rate),
          temperature: Number(formState.temperature),
          occupancy: Number(formState.occupancy),
        }),
      });
      setMessage("Manual record created successfully.");
      setFormState(initialFormState);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Manual entry failed.");
    } finally {
      setBusy(false);
    }
  }

  async function handleSyntheticGeneration() {
    try {
      setBusy(true);
      const response = await apiRequest<{ csv_path: string; records: number }>("/datasets/generate", {
        method: "POST",
        body: JSON.stringify({ records: 50000 }),
      });
      setMessage(`Synthetic dataset generated with ${response.records} rows at ${response.csv_path}.`);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Synthetic generation failed.");
    } finally {
      setBusy(false);
    }
  }

  async function handlePublicDatasetFetch() {
    try {
      setBusy(true);
      const response = await apiRequest<{ dataset_path: string }>("/datasets/fetch-public", {
        method: "POST",
      });
      setMessage(`Public dataset downloaded to ${response.dataset_path}.`);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Public dataset fetch failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <AppShell>
      <div className="space-y-6">
        <div>
          <h1 className="font-display text-4xl font-semibold">Dataset Upload</h1>
          <p className="mt-2 text-[var(--muted-foreground)]">
            Import CSV or Excel data, create single records manually, or generate the synthetic 50,000-row dataset for testing.
          </p>
        </div>

        {message ? <PageState title="Latest action" description={message} /> : null}

        <div className="grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
          <Card>
            <CardTitle>Import and export</CardTitle>
            <CardDescription className="mt-2">Accepted inputs: CSV and Excel files with the required energy schema.</CardDescription>
            <div className="mt-6 grid gap-4 md:grid-cols-2">
              <label className="rounded-[24px] border border-dashed border-black/15 bg-[#f8fafc] p-5">
                <span className="mb-3 block text-sm font-semibold">Upload dataset</span>
                <Input type="file" accept=".csv,.xlsx,.xls" onChange={(event) => void handleFileChange(event.target.files)} />
              </label>
              <div className="rounded-[24px] border border-black/10 bg-[#fffaf4] p-5">
                <span className="block text-sm font-semibold">Data utilities</span>
                <div className="mt-4 flex flex-wrap gap-3">
                  <Button onClick={() => void handleSyntheticGeneration()} disabled={busy}>Generate 50k synthetic data</Button>
                  <Button variant="secondary" onClick={() => void handlePublicDatasetFetch()} disabled={busy}>Fetch public dataset</Button>
                  <a href={downloadUrl("/records/export")} className="inline-flex h-11 items-center rounded-full border border-black/10 bg-white px-5 text-sm font-semibold">Export current records</a>
                </div>
              </div>
            </div>
          </Card>

          <Card>
            <CardTitle>Manual data entry</CardTitle>
            <CardDescription className="mt-2">Add validated records directly from the UI.</CardDescription>
            <form className="mt-6 grid gap-4 md:grid-cols-2" onSubmit={handleManualSubmit}>
              {Object.entries(formState).map(([key, value]) => (
                <div key={key} className={key === "device_name" ? "md:col-span-2" : undefined}>
                  <label className="mb-2 block text-sm font-medium capitalize">
                    {key.replaceAll("_", " ")}
                  </label>
                  <Input
                    required
                    type={key.includes("date") || key.includes("timestamp") ? (key === "date" ? "date" : "datetime-local") : key === "device_name" ? "text" : "number"}
                    step={key === "occupancy" ? "1" : "0.01"}
                    value={value}
                    onChange={(event) =>
                      setFormState((current) => ({ ...current, [key]: event.target.value }))
                    }
                  />
                </div>
              ))}
              <div className="md:col-span-2">
                <Button type="submit" disabled={busy}>Save manual record</Button>
              </div>
            </form>
          </Card>
        </div>
      </div>
    </AppShell>
  );
}
