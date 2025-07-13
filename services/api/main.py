from fastapi import FastAPI
from pydantic import BaseModel
import psycopg2
import psycopg2.extras
import os
from redis import Redis
from rq import Queue

app = FastAPI()

# Connect to Redis
redis_conn = Redis(host='redis', port=6379)
q = Queue(connection=redis_conn)

class ScreenerRequest(BaseModel):
    tickers: list[str]
    strategy: str
    email: str

@app.post("/screen")
async def start_screening(req: ScreenerRequest):
    """
    Accepts a screening request and queues it for the worker.
    """
    # The API's job is to enqueue a task for the worker.
    # We will enqueue the 'run_screener_by_name' function from the worker's code.
    job = q.enqueue(
        'main.run_screener_by_name', # The function path inside the worker service
        args=[req.strategy, req.email]
    )

    return {"status": "queued", "job_id": job.get_id()}

@app.get("/health")
def health():
    try:
        conn = psycopg2.connect(os.environ["DATABASE_URL"])
        conn.close()
        db_status = "ok"
    except Exception as e:
        db_status = f"error: {e}"

    return {"status": "ok", "database": db_status}

@app.get("/results/{screener_name}")
def get_results(screener_name: str):
    """Retrieves screening results for a given screener name."""
    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    query = """
    SELECT
        r.found_at,
        o.underlying,
        o.expiry,
        o.strike,
        o.call_put,
        o.bid,
        o.ask
    FROM screener_results r
    JOIN option_chains o ON r.option_chain_id = o.id
    WHERE r.screener_name = %s
    ORDER BY r.found_at DESC
    LIMIT 100;
    """
    # Using a dictionary cursor to get key-value pairs
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
        cursor.execute(query, (screener_name,))
        results = cursor.fetchall()

    conn.close()
    return {"screener": screener_name, "results": results} 