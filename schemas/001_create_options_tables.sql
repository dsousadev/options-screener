CREATE TABLE option_chains (
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

-- Index for efficient queries by underlying and date
CREATE INDEX idx_option_chains_underlying_as_of ON option_chains(underlying, as_of);
CREATE INDEX idx_option_chains_expiry ON option_chains(expiry); 