import os
import sys
from apscheduler.schedulers.background import BackgroundScheduler
import time
from datetime import datetime, timedelta

base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.abspath(os.path.join(base_dir, '../')))

from backend.mlops_retrainer.mlops_cloud_visibility_retrainer import run_cloud_visibility_retraining
from backend.live_metar_fetcher import fetch_and_store_live_metar


def smart_live_metar_fetch(sched):
    """
    Fetches METAR data. If no new data is found (records_added == 0),
    it schedules a one-off retry job to run in 5 minutes.
    """
    # Note: fetch_and_store_live_metar must return the number of records added for this logic.
    # If it doesn't return anything currently, we will still run it and catch exceptions.
    try:
        records_added = fetch_and_store_live_metar(hours=2)
        
        # If the function returns None because it was not modified to return int yet, default to a success print.
        if records_added == 0:
            print(f"[{datetime.now()}] No new data found. Rescheduling fetch in 5 minutes...")
            run_date = datetime.now() + timedelta(minutes=5)
            sched.add_job(
                smart_live_metar_fetch,
                'date',
                run_date=run_date,
                args=[sched],
                id='live_metar_retry_job',
                name='Live METAR Retry Fetcher (5m)',
                replace_existing=True
            )
        else:
            print(f"[{datetime.now()}] Successfully fetched new records.")
    except Exception as e:
        print(f"[{datetime.now()}] Error fetching live METAR: {e}")

def scheduled_retraining_job():
    print(f"[{datetime.now()}] Starting scheduled MLOps retraining pipeline...")
    
    # 1. Cloud & Visibility Models Retraining
    success, msg = run_cloud_visibility_retraining()
    print(f"[{datetime.now()}] MLOps Retraining: {msg}")
    
    # ---------------------------------------------------------
    # (imash,vijjj): Add other team model retraining functions here!
    # (Use try...except so missing files don't crash the scheduler)
    # ---------------------------------------------------------
    # try:
    #     from backend.mlops_retrainer.mlops_Wind_retrainer import run_wind_models_retraining
    #     run_wind_models_retraining()
    # except ImportError:
    #     pass
    # ---------------------------------------------------------
    
    
    # Hot-reload the models into memory so the API uses the newly trained versions
    try:
        from backend.api.routers.cloud_visibility_router import load_models
        load_models()
        print(f"[{datetime.now()}] Cloud & Visibility models hot-reloaded successfully.")
    except ImportError:
        pass
    
    print(f"[{datetime.now()}] Scheduled retraining complete.")


def start_scheduler():
    """
    Initializes the APScheduler to run the MLOps retraining pipeline
    automatically on the 1st of every month at midnight, and fetch
    live METAR data smartly every 32 minutes.
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

    # Fetch live METAR data every 32 minutes
    scheduler.add_job(
        smart_live_metar_fetch,
        'interval',
        minutes=32,
        args=[scheduler],
        id='live_metar_fetch_job',
        name='Live METAR Data Fetcher (32m)',
        replace_existing=True
    )
    
    # Run a daily job to fetch the last 48 hours and fill any missing gaps
    # It runs at 01:00 AM every day
    scheduler.add_job(
        lambda: fetch_and_store_live_metar(hours=48),
        'cron',
        hour=1,
        minute=0,
        id='live_metar_daily_backup',
        name='Live METAR Data Backup Fetcher (48h)',
        replace_existing=True
    )
    
    scheduler.start()
    print("▶ MLOps Background Scheduler started. Next run: 1st of the month at 00:00.")
    print("▶ Smart Live METAR Fetcher scheduled to run every 32 minutes (retries every 5m if delayed).")
    print("▶ Daily METAR Backup Fetcher scheduled to run every day at 01:00 AM.")
    
    # Return the scheduler instance so it can be managed if needed
    return scheduler


if __name__ == "__main__":
    scheduler = start_scheduler()
    # Keep the thread alive if running this script directly
    try:
        while True:
            time.sleep(2)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        print("Scheduler shut down.")
