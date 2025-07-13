import os
import time
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from datetime import date, timedelta

def connect_to_db():
    """Establishes a connection to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(os.environ["DATABASE_URL"])
        print("Worker successfully connected to database.")
        return conn
    except psycopg2.OperationalError as e:
        print(f"Error connecting to database: {e}")
        return None

def find_cheap_weeklies(conn):
    """
    A simple screener that looks for options expiring in the next 10 days,
    costing less than $1.00 (midpoint of bid/ask), with decent volume.
    (Note: Volume is not in our schema yet, so we'll omit that for now).
    """
    print("Running screener: 'find_cheap_weeklies'...")
    query = """
    SELECT id, underlying, expiry, strike, call_put, bid, ask
    FROM option_chains
    WHERE expiry BETWEEN %s AND %s
      AND (bid + ask) / 2 < 1.00
      AND bid > 0;
    """
    
    today = date.today()
    ten_days_from_now = today + timedelta(days=10)
    
    df = pd.read_sql_query(query, conn, params=(today, ten_days_from_now))
    
    if df.empty:
        print("Screener found no matching options.")
        return []
    
    print(f"Screener found {len(df)} matching options.")
    # Format for insertion into the results table
    results = [('find_cheap_weeklies', option_id) for option_id in df['id']]
    return results

def save_results(conn, results):
    """Saves the results of a screener to the database."""
    if not results:
        return
        
    query = "INSERT INTO screener_results (screener_name, option_chain_id) VALUES %s ON CONFLICT DO NOTHING;"
    with conn.cursor() as cursor:
        execute_values(cursor, query, results)
        conn.commit()
    print(f"Saved {len(results)} new results to the database.")

def main_loop():
    """Main worker loop to run screeners and save results."""
    db_url = os.environ.get("DATABASE_URL")
    conn = psycopg2.connect(db_url)
    
    while True:
        # Run screeners
        cheap_weekly_results = find_cheap_weeklies(conn)
        
        # Save results
        save_results(conn, cheap_weekly_results)

        print("--- Completed worker cycle. Waiting 15 minutes. ---")
        time.sleep(900) # Run every 15 minutes

if __name__ == "__main__":
    print("Starting worker process...")
    main_loop() 