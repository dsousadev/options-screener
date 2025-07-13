#!/usr/bin/env python3
"""
Options data ingest service for IEX Cloud API.
Fetches option chains for SPY, AAPL, NVDA and stores in PostgreSQL.
"""

import os
import sys
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any
import requests
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from tenacity import retry, stop_after_attempt, wait_exponential
from pydantic_settings import BaseSettings
from prometheus_client import start_http_server, Summary, Counter

# Prometheus metrics
REQUEST_LATENCY = Summary("ingest_duration_seconds", "Time spent ingesting")
API_ERRORS = Counter("api_errors_total", "API error responses")
ROWS_INSERTED = Counter("rows_inserted_total", "Rows inserted into database")

# Start Prometheus metrics server
start_http_server(9100)

class Settings(BaseSettings):
    """Configuration settings."""
    data_api_key: str
    data_api_base_url: str = "https://cloud.iexapis.com/stable"
    database_url: str = "postgresql://postgres:changeme@db:5432/opt_screener"
    symbols: List[str] = ["SPY", "AAPL", "NVDA"]
    
    class Config:
        env_file = ".env"

class OptionChainIngester:
    """Handles option chain data ingestion from IEX Cloud."""
    
    def __init__(self):
        self.settings = Settings()
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "OptionsScreener/1.0"
        })
        
    @retry(
        stop=stop_after_attempt(8),
        wait=wait_exponential(multiplier=1, min=4, max=60)
    )
    def fetch_option_chain(self, symbol: str) -> Dict[str, Any]:
        """Fetch option chain data from IEX Cloud with retry logic."""
        url = f"{self.settings.data_api_base_url}/stock/{symbol}/options"
        params = {"token": self.settings.data_api_key}
        
        response = self.session.get(url, params=params, timeout=30)
        
        if response.status_code != 200:
            API_ERRORS.inc()
            raise requests.RequestException(
                f"API error {response.status_code}: {response.text}"
            )
            
        return response.json()
    
    def normalize_option_data(self, symbol: str, raw_data: List[Dict]) -> pd.DataFrame:
        """Normalize raw option data into structured DataFrame."""
        if not raw_data:
            return pd.DataFrame()
            
        records = []
        as_of = datetime.now(timezone.utc)
        
        for option in raw_data:
            record = {
                "underlying": symbol,
                "as_of": as_of,
                "expiry": option.get("expirationDate"),
                "strike": option.get("strikePrice"),
                "call_put": "C" if option.get("side", "").lower() == "call" else "P",
                "bid": option.get("bid"),
                "ask": option.get("ask"),
                "iv": None,  # IEX Cloud free tier doesn't include Greeks
                "delta": None,
                "theta": None,
                "gamma": None,
                "vega": None,
                "rho": None
            }
            records.append(record)
            
        return pd.DataFrame(records)
    
    def insert_options_data(self, df: pd.DataFrame) -> int:
        """Insert option data into PostgreSQL using bulk insert."""
        if df.empty:
            return 0
            
        conn = psycopg2.connect(self.settings.database_url)
        cursor = conn.cursor()
        
        try:
            # Convert DataFrame to list of tuples for bulk insert
            data = [tuple(row) for row in df.itertuples(index=False)]
            
            insert_query = """
                INSERT INTO option_chains (
                    underlying, as_of, expiry, strike, call_put,
                    bid, ask, iv, delta, theta, gamma, vega, rho
                ) VALUES %s
            """
            
            execute_values(cursor, insert_query, data)
            conn.commit()
            
            rows_inserted = len(data)
            ROWS_INSERTED.inc(rows_inserted)
            return rows_inserted
            
        finally:
            cursor.close()
            conn.close()
    
    @REQUEST_LATENCY.time()
    def ingest_symbol(self, symbol: str) -> int:
        """Ingest option chain data for a single symbol."""
        try:
            logging.info(f"Fetching option chain for {symbol}")
            raw_data = self.fetch_option_chain(symbol)
            
            df = self.normalize_option_data(symbol, raw_data)
            rows_inserted = self.insert_options_data(df)
            
            logging.info(f"Ingest OK - {symbol}: {rows_inserted} rows")
            return rows_inserted
            
        except Exception as e:
            logging.error(f"Error ingesting {symbol}: {e}")
            raise
    
    def run_ingest(self) -> Dict[str, int]:
        """Run ingest for all configured symbols."""
        results = {}
        total_rows = 0
        
        for symbol in self.settings.symbols:
            try:
                rows = self.ingest_symbol(symbol)
                results[symbol] = rows
                total_rows += rows
            except Exception as e:
                logging.error(f"Failed to ingest {symbol}: {e}")
                results[symbol] = 0
        
        logging.info(f"Ingest OK – total rows: {total_rows}")
        return results

def main():
    """Main entry point."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    
    ingester = OptionChainIngester()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        # Single run mode
        ingester.run_ingest()
    else:
        # Continuous mode (for scheduler)
        ingester.run_ingest()

if __name__ == "__main__":
    main() 