"use client";

import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import type { AggregatedPoint, ForecastPoint } from "@/lib/types";
import { formatShortDate } from "@/lib/utils";

type ConsumptionLineChartProps = {
  data: AggregatedPoint[] | ForecastPoint[];
  mode: "aggregate" | "forecast";
};

export function ConsumptionLineChart({ data, mode }: ConsumptionLineChartProps) {
  const chartData =
    mode === "aggregate"
      ? (data as AggregatedPoint[]).map((item) => ({
          label: formatShortDate(item.period),
          value: item.energy_consumption_kwh,
          secondary: item.average_consumption_kwh,
        }))
      : (data as ForecastPoint[]).map((item) => ({
          label: formatShortDate(item.timestamp),
          value: item.predicted_consumption_kwh,
          lower: item.lower_bound,
          upper: item.upper_bound,
        }));

  return (
    <div className="h-80 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={chartData}>
          <defs>
            <linearGradient id="energyGradient" x1="0" x2="0" y1="0" y2="1">
              <stop offset="5%" stopColor="#0f766e" stopOpacity={0.35} />
              <stop offset="95%" stopColor="#0f766e" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="secondaryGradient" x1="0" x2="0" y1="0" y2="1">
              <stop offset="5%" stopColor="#fb923c" stopOpacity={0.35} />
              <stop offset="95%" stopColor="#fb923c" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#dbe4ef" />
          <XAxis dataKey="label" tickLine={false} axisLine={false} />
          <YAxis tickLine={false} axisLine={false} />
          <Tooltip />
          <Area type="monotone" dataKey="value" stroke="#0f766e" fill="url(#energyGradient)" strokeWidth={3} />
          {mode === "aggregate" ? (
            <Area type="monotone" dataKey="secondary" stroke="#fb923c" fill="url(#secondaryGradient)" strokeWidth={2} />
          ) : (
            <>
              <Area type="monotone" dataKey="lower" stroke="#94a3b8" fillOpacity={0} strokeDasharray="4 4" />
              <Area type="monotone" dataKey="upper" stroke="#94a3b8" fillOpacity={0} strokeDasharray="4 4" />
            </>
          )}
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
