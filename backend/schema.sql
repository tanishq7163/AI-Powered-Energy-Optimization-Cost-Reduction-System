CREATE TABLE IF NOT EXISTS energy_records (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    energy_consumption_kwh DOUBLE PRECISION NOT NULL,
    voltage DOUBLE PRECISION NOT NULL,
    current DOUBLE PRECISION NOT NULL,
    power_factor DOUBLE PRECISION NOT NULL,
    tariff_rate DOUBLE PRECISION NOT NULL,
    temperature DOUBLE PRECISION NOT NULL,
    occupancy DOUBLE PRECISION NOT NULL,
    device_name VARCHAR(120) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_energy_records_timestamp ON energy_records (timestamp);

CREATE TABLE IF NOT EXISTS forecasts (
    id SERIAL PRIMARY KEY,
    model_name VARCHAR(50) NOT NULL,
    horizon VARCHAR(20) NOT NULL,
    forecast_time TIMESTAMP NOT NULL,
    predicted_consumption_kwh DOUBLE PRECISION NOT NULL,
    lower_bound DOUBLE PRECISION NOT NULL,
    upper_bound DOUBLE PRECISION NOT NULL,
    generated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_forecasts_time ON forecasts (forecast_time);

CREATE TABLE IF NOT EXISTS anomalies (
    id SERIAL PRIMARY KEY,
    record_id INTEGER REFERENCES energy_records(id) ON DELETE SET NULL,
    timestamp TIMESTAMP NOT NULL,
    method VARCHAR(50) NOT NULL,
    anomaly_score DOUBLE PRECISION NOT NULL,
    severity_level VARCHAR(20) NOT NULL,
    description TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_anomalies_time ON anomalies (timestamp);

CREATE TABLE IF NOT EXISTS recommendations (
    id SERIAL PRIMARY KEY,
    category VARCHAR(50) NOT NULL,
    priority VARCHAR(20) NOT NULL,
    title VARCHAR(160) NOT NULL,
    description TEXT NOT NULL,
    estimated_savings DOUBLE PRECISION NOT NULL DEFAULT 0,
    source_context JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS cost_estimations (
    id SERIAL PRIMARY KEY,
    period_type VARCHAR(20) NOT NULL,
    period_start TIMESTAMP NOT NULL,
    period_end TIMESTAMP NOT NULL,
    energy_kwh DOUBLE PRECISION NOT NULL,
    estimated_cost DOUBLE PRECISION NOT NULL,
    peak_cost_contribution DOUBLE PRECISION NOT NULL,
    potential_savings DOUBLE PRECISION NOT NULL,
    forecasted BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS generated_reports (
    id SERIAL PRIMARY KEY,
    report_name VARCHAR(200) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    filters JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
