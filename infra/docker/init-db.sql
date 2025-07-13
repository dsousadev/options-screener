-- Create database if it doesn't exist
SELECT 'CREATE DATABASE opt_screener'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'opt_screener')\gexec

-- Connect to the database
\c opt_screener;

-- Create the option_chains table
CREATE TABLE IF NOT EXISTS option_chains (
  id BIGSERIAL PRIMARY KEY,
  underlying TEXT NOT NULL,
  as_of TIMESTAMPTZ NOT NULL,
  expiry DATE NOT NULL,
  strike NUMERIC NOT NULL,
  call_put CHAR(1) NOT NULL,
  bid NUMERIC,
  ask NUMERIC,
  iv NUMERIC,
  delta NUMERIC,
  theta NUMERIC,
  gamma NUMERIC,
  vega NUMERIC,
  rho NUMERIC
);

-- Create indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_option_chains_underlying_as_of ON option_chains(underlying, as_of);
CREATE INDEX IF NOT EXISTS idx_option_chains_expiry ON option_chains(expiry);

-- Create the notifications table
CREATE TABLE IF NOT EXISTS notifications (
    id SERIAL PRIMARY KEY,
    request_id VARCHAR(255) NOT NULL,
    recipient_email VARCHAR(255) NOT NULL,
    subject TEXT,
    body TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for notifications table
CREATE INDEX IF NOT EXISTS idx_notifications_status ON notifications(status);
CREATE INDEX IF NOT EXISTS idx_notifications_request_id ON notifications(request_id);

-- Create the screener_results table
CREATE TABLE IF NOT EXISTS screener_results (
    id SERIAL PRIMARY KEY,
    screener_name VARCHAR(100) NOT NULL,
    option_chain_id INTEGER REFERENCES option_chains(id) ON DELETE CASCADE,
    found_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for screener_results table
CREATE INDEX IF NOT EXISTS idx_results_lookup ON screener_results (screener_name);

-- Create market parameters table for risk-free rates
CREATE TABLE IF NOT EXISTS market_parameters (
    id SERIAL PRIMARY KEY,
    as_of_date DATE UNIQUE NOT NULL,
    risk_free_rate NUMERIC(6, 4)
);

-- Create stock metadata table for dividend yields
CREATE TABLE IF NOT EXISTS stock_metadata (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(10) UNIQUE NOT NULL,
    dividend_yield NUMERIC(6, 4)
);

-- Create indexes for new tables
CREATE INDEX IF NOT EXISTS idx_market_parameters_date ON market_parameters(as_of_date);
CREATE INDEX IF NOT EXISTS idx_stock_metadata_ticker ON stock_metadata(ticker); 