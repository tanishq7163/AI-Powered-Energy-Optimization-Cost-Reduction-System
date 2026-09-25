export type AggregatedPoint = {
  period: string;
  energy_consumption_kwh: number;
  average_consumption_kwh: number;
  cost: number;
};

export type AnalyticsSummary = {
  total_energy: number;
  average_consumption: number;
  peak_consumption: number;
  minimum_consumption: number;
  estimated_monthly_cost: number;
  savings_opportunity: number;
  trend_direction: string;
  peak_hour: number;
  peak_hour_average: number;
  seasonal_profile: Array<Record<string, string | number>>;
  daily_trend: AggregatedPoint[];
  weekly_trend: AggregatedPoint[];
  monthly_trend: AggregatedPoint[];
  yearly_trend: AggregatedPoint[];
  peak_hour_heatmap: Array<Record<string, number>>;
  device_breakdown: Array<Record<string, string | number>>;
};

export type ModelMetric = {
  model_name: string;
  mae: number;
  mse: number;
  rmse: number;
  mape: number;
  r2: number;
  status: string;
};

export type ForecastPoint = {
  timestamp: string;
  predicted_consumption_kwh: number;
  lower_bound: number;
  upper_bound: number;
};

export type ForecastResponse = {
  best_model: string;
  selected_horizon: "24h" | "7d" | "30d";
  metrics: ModelMetric[];
  forecast: ForecastPoint[];
};

export type AnomalyItem = {
  timestamp: string;
  device_name: string;
  energy_consumption_kwh: number;
  anomaly_score: number;
  severity_level: string;
  description: string;
  method: string;
};

export type AnomalyResponse = {
  count: number;
  anomalies: AnomalyItem[];
  severity_breakdown: Array<Record<string, string | number>>;
};

export type CostSummary = {
  current_cost: number;
  daily_cost: number;
  weekly_cost: number;
  monthly_cost: number;
  forecast_cost: number;
  potential_savings: number;
  peak_cost_contribution: number;
  breakdown: Array<Record<string, string | number>>;
};

export type RecommendationItem = {
  category: string;
  priority: string;
  title: string;
  description: string;
  estimated_savings: number;
  source_context: Record<string, string | number>;
};

export type RecommendationResponse = {
  generated_at: string;
  recommendations: RecommendationItem[];
};

export type ReportItem = {
  id: number;
  report_name: string;
  file_path: string;
  created_at: string;
};

export type DashboardResponse = {
  analytics: AnalyticsSummary;
  forecast: ForecastResponse;
  anomalies: AnomalyResponse;
  costs: CostSummary;
  recommendations: RecommendationResponse;
};

export type EnergyRecord = {
  id: number;
  date: string;
  timestamp: string;
  energy_consumption_kwh: number;
  voltage: number;
  current: number;
  power_factor: number;
  tariff_rate: number;
  temperature: number;
  occupancy: number;
  device_name: string;
};

export type SettingsResponse = {
  app_name: string;
  database_url: string;
  reports_dir: string;
  dataset_dir: string;
  models_dir: string;
};
