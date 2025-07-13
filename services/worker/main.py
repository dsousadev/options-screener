import os
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from datetime import date, timedelta
from redis import Redis
from rq import Queue

# NOTE: The worker no longer runs its own loop.
# 'rq' runs this file and calls functions based on jobs in the queue.

def get_db_connection():
    """Establishes a new database connection."""
    db_url = os.environ.get("DATABASE_URL")
    return psycopg2.connect(db_url)

def save_results(conn, results):
    """Saves the results of a screener to the database."""
    if not results:
        return
        
    query = "INSERT INTO screener_results (screener_name, option_chain_id) VALUES %s ON CONFLICT DO NOTHING;"
    with conn.cursor() as cursor:
        execute_values(cursor, query, results)
        conn.commit()
    print(f"Saved {len(results)} new results to the database.")

def find_cheap_weeklies(conn):
    """
    A simple screener that looks for options expiring in the next 10 days,
    costing less than $1.00 (midpoint of bid/ask), with decent volume.
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
        return pd.DataFrame()
    
    print(f"Screener found {len(df)} matching options.")
    return df

# This is the main function the API will enqueue
def run_screener_by_name(screener_name: str, recipient_email: str):
    """
    Looks up and runs the requested screener, saves results,
    and queues a notification job.
    """
    print(f"Worker processing job: running screener '{screener_name}'")
    conn = get_db_connection()
    
    results_df = pd.DataFrame()
    if screener_name == 'find_cheap_weeklies':
        results_df = find_cheap_weeklies(conn)
        # Save results to database
        if not results_df.empty:
            results = [('find_cheap_weeklies', option_id) for option_id in results_df['id']]
            save_results(conn, results)
    else:
        print(f"Error: Unknown screener '{screener_name}'")

    conn.close()
    
    # After work is done, queue a notification
    redis_conn = Redis(host='redis', port=6379)
    q_notifications = Queue('notifications', connection=redis_conn)
    subject = f"Your options screening for '{screener_name}' is complete!"
    body = f"Found {len(results_df)} results."
    q_notifications.enqueue(
        'main.send_notification_job', # Assumes a function in the notifier's main.py
        args=(recipient_email, subject, body)
    )
    
    print(f"Job finished. Notification queued for {recipient_email}.") 