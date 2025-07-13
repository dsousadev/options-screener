from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
import psycopg2
import os
import time

app = FastAPI()

class ScreenerRequest(BaseModel):
    tickers: list[str]
    strategy: str

def run_screening_task(request_id: str, tickers: list[str]):
    """Placeholder for the actual screening logic."""
    print(f"[{request_id}] Starting screening for: {', '.join(tickers)}")
    # In Phase 4, this will trigger the worker.
    time.sleep(15) # Simulate work
    print(f"[{request_id}] Completed screening.")


@app.post("/screen")
async def start_screening(req: ScreenerRequest, background_tasks: BackgroundTasks):
    """
    Accepts a list of tickers and a strategy, then queues the job.
    """
    # Generate a unique ID for this request
    request_id = f"req_{int(time.time())}"

    # Add the intensive screening task to the background
    background_tasks.add_task(run_screening_task, request_id, req.tickers)

    return {"status": "queued", "request_id": request_id}

@app.get("/health")
def health():
    try:
        conn = psycopg2.connect(os.environ["DATABASE_URL"])
        conn.close()
        db_status = "ok"
    except Exception as e:
        db_status = f"error: {e}"

    return {"status": "ok", "database": db_status} 