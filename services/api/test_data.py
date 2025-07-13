#!/usr/bin/env python3
"""
Script to insert test data for Phase 6 verification.
"""

import psycopg2
import os
from datetime import date, timedelta

def insert_test_data():
    """Insert test option data and screener results."""
    conn = psycopg2.connect(os.environ.get("DATABASE_URL", "postgresql://postgres:changeme@localhost:5432/opt_screener"))
    cursor = conn.cursor()
    
    try:
        # Insert test option chains
        test_options = [
            ("AAPL", date.today() + timedelta(days=7), 150.0, "C", 0.85, 0.95),
            ("AAPL", date.today() + timedelta(days=7), 150.0, "P", 0.75, 0.85),
            ("TSLA", date.today() + timedelta(days=5), 200.0, "C", 0.65, 0.75),
            ("NVDA", date.today() + timedelta(days=10), 800.0, "C", 0.45, 0.55),
        ]
        
        for underlying, expiry, strike, call_put, bid, ask in test_options:
            cursor.execute("""
                INSERT INTO option_chains (underlying, as_of, expiry, strike, call_put, bid, ask)
                VALUES (%s, NOW(), %s, %s, %s, %s, %s)
                RETURNING id
            """, (underlying, expiry, strike, call_put, bid, ask))
            option_id = cursor.fetchone()[0]
            
            # Insert screener result
            cursor.execute("""
                INSERT INTO screener_results (screener_name, option_chain_id)
                VALUES (%s, %s)
            """, ("find_cheap_weeklies", option_id))
        
        conn.commit()
        print(f"✅ Inserted {len(test_options)} test options and screener results")
        
    except Exception as e:
        print(f"❌ Error inserting test data: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    insert_test_data() 