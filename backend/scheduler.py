import os
import sys
from apscheduler.schedulers.background import BackgroundScheduler
import time
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from backend.mlops_retrainer import run_all_retrainings

def scheduled_retraining_job():
    print(f"[{datetime.now()}] Starting scheduled MLOps retraining pipeline...")
    run_all_retrainings()
    
    # ---------------------------------------------------------
    # Imash's Temperature & Pressure Hot-reload
    from backend.api.routers.temperature_pressure_router import load_Temp_Press_models
    load_Temp_Press_models()
    # ---------------------------------------------------------
    
    print(f"[{datetime.now()}] Scheduled retraining complete and models hot-reloaded.")

def start_scheduler():
    """
    Initializes the APScheduler to run the MLOps retraining pipeline
    automatically on the 1st of every month at midnight.
    """
    scheduler = BackgroundScheduler()
    
    # Run retraining on the 1st day of every month at midnight
    scheduler.add_job(
        scheduled_retraining_job,
        'cron',
        day='1',
        hour='0',
        minute='0',
        id='monthly_retrain_job',
        name='MLOps Monthly Retraining',
        replace_existing=True
    )

    scheduler.start()
    print("✅ MLOps Background Scheduler started. Next run: 1st of the month at 00:00.")
    
    return scheduler

if __name__ == "__main__":
    scheduler = start_scheduler()
    try:
        while True:
            time.sleep(2)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        print("Scheduler shut down.")