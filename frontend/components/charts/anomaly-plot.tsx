"use client";

import dynamic from "next/dynamic";

import type { AnomalyItem } from "@/lib/types";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

export function AnomalyPlot({ anomalies }: { anomalies: AnomalyItem[] }) {
  return (
    <div className="h-[360px] w-full overflow-hidden rounded-[24px]">
      <Plot
        data={[
          {
            x: anomalies.map((item) => item.timestamp),
            y: anomalies.map((item) => item.energy_consumption_kwh),
            mode: "markers",
            type: "scatter",
            text: anomalies.map((item) => `${item.device_name} | ${item.severity_level}`),
            marker: {
              size: anomalies.map((item) => 10 + item.anomaly_score * 20),
              color: anomalies.map((item) => item.anomaly_score),
              colorscale: "Portland",
              opacity: 0.85,
            },
          },
        ]}
        layout={{
          autosize: true,
          paper_bgcolor: "rgba(255,255,255,0)",
          plot_bgcolor: "rgba(255,255,255,0)",
          margin: { l: 36, r: 12, t: 18, b: 34 },
          xaxis: { title: "Timestamp", gridcolor: "#dbe4ef" },
          yaxis: { title: "Energy (kWh)", gridcolor: "#dbe4ef" },
        }}
        config={{ displayModeBar: false, responsive: true }}
        style={{ width: "100%", height: "100%" }}
      />
    </div>
  );
}
