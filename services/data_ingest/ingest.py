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
    
    @retry(
        stop=stop_after_attempt(8),
        wait=wait_exponential(multiplier=1, min=4, max=60)
    )
    def fetch_risk_free_rate(self) -> float:
        """Fetch 10-year Treasury yield as risk-free rate from IEX Cloud."""
        url = f"{self.settings.data_api_base_url}/data-points/market/T10Y"
        params = {"token": self.settings.data_api_key}
        
        response = self.session.get(url, params=params, timeout=30)
        
        if response.status_code != 200:
            API_ERRORS.inc()
            raise requests.RequestException(
                f"API error {response.status_code}: {response.text}"
            )
        
        data = response.json()
        # Convert percentage to decimal (e.g., 4.5% -> 0.045)
        return float(data) / 100 if data else 0.0
    
    @retry(
        stop=stop_after_attempt(8),
        wait=wait_exponential(multiplier=1, min=4, max=60)
    )
    def fetch_dividend_yield(self, symbol: str) -> float:
        """Fetch dividend yield for a stock from IEX Cloud."""
        url = f"{self.settings.data_api_base_url}/stock/{symbol}/stats/dividendYield"
        params = {"token": self.settings.data_api_key}
        
        response = self.session.get(url, params=params, timeout=30)
        
        if response.status_code != 200:
            API_ERRORS.inc()
            raise requests.RequestException(
                f"API error {response.status_code}: {response.text}"
            )
        
        data = response.json()
        # Convert percentage to decimal (e.g., 2.1% -> 0.021)
        return float(data) / 100 if data else 0.0
    
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
    
    def insert_market_parameters(self, risk_free_rate: float) -> int:
        """Insert risk-free rate into market_parameters table."""
        conn = psycopg2.connect(self.settings.database_url)
        cursor = conn.cursor()
        
        try:
            today = datetime.now().date()
            
            # Use UPSERT to handle duplicate dates
            insert_query = """
                INSERT INTO market_parameters (as_of_date, risk_free_rate)
                VALUES (%s, %s)
                ON CONFLICT (as_of_date) 
                DO UPDATE SET risk_free_rate = EXCLUDED.risk_free_rate
            """
            
            cursor.execute(insert_query, (today, risk_free_rate))
            conn.commit()
            
            return 1
            
        finally:
            cursor.close()
            conn.close()
    
    def insert_stock_metadata(self, symbol: str, dividend_yield: float) -> int:
        """Insert dividend yield into stock_metadata table."""
        conn = psycopg2.connect(self.settings.database_url)
        cursor = conn.cursor()
        
        try:
            # Use UPSERT to handle duplicate tickers
            insert_query = """
                INSERT INTO stock_metadata (ticker, dividend_yield)
                VALUES (%s, %s)
                ON CONFLICT (ticker) 
                DO UPDATE SET dividend_yield = EXCLUDED.dividend_yield
            """
            
            cursor.execute(insert_query, (symbol, dividend_yield))
            conn.commit()
            
            return 1
            
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
    
    def ingest_market_data(self) -> Dict[str, float]:
        """Ingest market parameters (risk-free rate and dividend yields)."""
        results = {}
        
        try:
            # Fetch risk-free rate
            logging.info("Fetching risk-free rate (10-year Treasury yield)")
            risk_free_rate = self.fetch_risk_free_rate()
            self.insert_market_parameters(risk_free_rate)
            results['risk_free_rate'] = risk_free_rate
            logging.info(f"Risk-free rate ingested: {risk_free_rate:.4f}")
            
        except Exception as e:
            logging.error(f"Failed to ingest risk-free rate: {e}")
            results['risk_free_rate'] = 0.0
        
        # Fetch dividend yields for each symbol
        for symbol in self.settings.symbols:
            try:
                logging.info(f"Fetching dividend yield for {symbol}")
                dividend_yield = self.fetch_dividend_yield(symbol)
                self.insert_stock_metadata(symbol, dividend_yield)
                results[f'{symbol}_dividend_yield'] = dividend_yield
                logging.info(f"Dividend yield for {symbol}: {dividend_yield:.4f}")
                
            except Exception as e:
                logging.error(f"Failed to ingest dividend yield for {symbol}: {e}")
                results[f'{symbol}_dividend_yield'] = 0.0
        
        return results
    
    def run_ingest(self) -> Dict[str, int]:
        """Run ingest for all configured symbols and market data."""
        results = {}
        total_rows = 0
        
        # Ingest market parameters first
        market_data = self.ingest_market_data()
        results['market_data'] = market_data
        
        # Ingest option chains
        for symbol in self.settings.symbols:
            try:
                rows = self.ingest_symbol(symbol)
                results[symbol] = rows
                total_rows += rows
            except Exception as e:
                logging.error(f"Failed to ingest {symbol}: {e}")
                results[symbol] = 0
        
        logging.info(f"Ingest OK – total option rows: {total_rows}")
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