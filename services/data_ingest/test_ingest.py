"""Unit tests for the data ingest service."""

import pytest
import responses
import pandas as pd
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

from ingest import OptionChainIngester, Settings

@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    with patch('ingest.Settings') as mock:
        mock.return_value.data_api_key = "test_key"
        mock.return_value.data_api_base_url = "https://cloud.iexapis.com/stable"
        mock.return_value.database_url = "postgresql://test:test@localhost/test"
        mock.return_value.symbols = ["SPY"]
        yield mock.return_value

@pytest.fixture
def ingester(mock_settings):
    """Create an ingester instance for testing."""
    return OptionChainIngester()

@pytest.fixture
def sample_option_data():
    """Sample option data from IEX Cloud API."""
    return [
        {
            "expirationDate": "2024-01-19",
            "strikePrice": 450.0,
            "side": "call",
            "bid": 5.25,
            "ask": 5.35
        },
        {
            "expirationDate": "2024-01-19", 
            "strikePrice": 450.0,
            "side": "put",
            "bid": 2.10,
            "ask": 2.20
        }
    ]

def test_normalize_option_data(ingester, sample_option_data):
    """Test option data normalization."""
    df = ingester.normalize_option_data("SPY", sample_option_data)
    
    assert len(df) == 2
    assert df.iloc[0]["underlying"] == "SPY"
    assert df.iloc[0]["call_put"] == "C"
    assert df.iloc[1]["call_put"] == "P"
    assert df.iloc[0]["strike"] == 450.0
    assert df.iloc[0]["bid"] == 5.25
    assert df.iloc[0]["ask"] == 5.35

@responses.activate
def test_fetch_option_chain_success(ingester):
    """Test successful API call."""
    responses.add(
        responses.GET,
        "https://cloud.iexapis.com/stable/stock/SPY/options?token=test_key",
        json=[{"expirationDate": "2024-01-19", "strikePrice": 450.0, "side": "call"}],
        status=200
    )
    
    data = ingester.fetch_option_chain("SPY")
    assert len(data) == 1
    assert data[0]["expirationDate"] == "2024-01-19"

@responses.activate
def test_fetch_option_chain_retry_on_error(ingester):
    """Test retry logic on API errors."""
    # First call fails, second succeeds
    responses.add(
        responses.GET,
        "https://cloud.iexapis.com/stable/stock/SPY/options?token=test_key",
        status=502
    )
    responses.add(
        responses.GET,
        "https://cloud.iexapis.com/stable/stock/SPY/options?token=test_key",
        json=[{"expirationDate": "2024-01-19", "strikePrice": 450.0, "side": "call"}],
        status=200
    )
    
    data = ingester.fetch_option_chain("SPY")
    assert len(data) == 1

@patch('ingest.psycopg2.connect')
def test_insert_options_data(mock_connect, ingester):
    """Test database insertion."""
    mock_cursor = MagicMock()
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_conn.commit.return_value = None
    mock_connect.return_value = mock_conn
    
    # Mock the connection encoding to avoid KeyError
    mock_conn.encoding = 'utf8'
    
    df = pd.DataFrame({
        "underlying": ["SPY"],
        "as_of": [datetime.now(timezone.utc)],
        "expiry": ["2024-01-19"],
        "strike": [450.0],
        "call_put": ["C"],
        "bid": [5.25],
        "ask": [5.35],
        "iv": [None],
        "delta": [None],
        "theta": [None],
        "gamma": [None],
        "vega": [None],
        "rho": [None]
    })
    
    rows_inserted = ingester.insert_options_data(df)
    assert rows_inserted == 1

def test_empty_dataframe_insert(ingester):
    """Test handling of empty DataFrame."""
    df = pd.DataFrame()
    rows_inserted = ingester.insert_options_data(df)
    assert rows_inserted == 0

if __name__ == "__main__":
    pytest.main([__file__]) 