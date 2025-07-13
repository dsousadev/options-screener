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