import os
import time
import psycopg2
import pandas as pd # Example dependency

def connect_to_db():
    """Establishes a connection to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(os.environ["DATABASE_URL"])
        print("Worker successfully connected to database.")
        return conn
    except psycopg2.OperationalError as e:
        print(f"Error connecting to database: {e}")
        return None

if __name__ == "__main__":
    print("Starting worker process...")
    conn = connect_to_db()

    # Main worker loop
    while True:
        if conn:
            # In a future phase, this will poll a job queue (e.g., Redis or a DB table).
            print("Worker heartbeat: polling for jobs...")
        else:
            print("Worker heartbeat: database connection not available. Retrying...")
            conn = connect_to_db()

        time.sleep(15) 