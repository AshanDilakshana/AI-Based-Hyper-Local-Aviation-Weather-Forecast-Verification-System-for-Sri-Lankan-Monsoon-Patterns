import os
import sys
from apscheduler.schedulers.background import BackgroundScheduler
import time
from datetime import datetime, timedelta

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from backend.mlops_retrainer.mlops_Wind_retrainer import run_wind_models_retraining
from backend.mlops_retrainer.mlops_cloud_visibility_retrainer import run_cloud_visibility_retraining
from backend.mlops_retrainer.mlops_qnh_dewpoint_retrainer import run_qnh_dewpoint_retraining
from backend.live_metar_fetcher import fetch_and_store_live_metar

from datetime import datetime, timedelta

def smart_live_metar_fetch(sched):
    """
    Fetches METAR data. If no new data is found (records_added == 0),
    it schedules a one-off retry job to run in 5 minutes.
    """
    try:
        records_added = fetch_and_store_live_metar(hours=2)
        
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
            print(f"[{datetime.now()}] Successfully fetched {records_added} new records.")
    except Exception as e:
        print(f"[{datetime.now()}] Error fetching live METAR: {e}")

from backend.data.database import SessionLocal
from backend.data.models import SystemLogs

def log_scheduler_error(component: str, message: str, error: Exception):
    print(f"[{datetime.now()}] [ERROR] {component}: {message} - {error}")
    db = SessionLocal()
    try:
        log = SystemLogs(level="ERROR", component=component, message=message, details=str(error))
        db.add(log)
        db.commit()
    except Exception as db_e:
        print(f"[{datetime.now()}] [ERROR] Failed to log to database: {db_e}")
    finally:
        db.close()

def scheduled_retraining_job():
    print(f"[{datetime.now()}] Triggering scheduled MLOps retraining pipeline via Celery...")
    try:
        from backend.celery_worker import run_full_retraining_pipeline
        task = run_full_retraining_pipeline.delay()
        print(f"[{datetime.now()}] Retraining task successfully dispatched to Celery background worker (Task ID: {task.id}).")
    except Exception as e:
        log_scheduler_error("MLOps_Scheduler", "Failed to dispatch Celery retraining task", e)



def start_scheduler():
    """
    Initializes the APScheduler to run the MLOps retraining pipeline
    automatically on the 1st of every month at midnight, and fetch
    live METAR data smartly every 32 minutes.
    """
    scheduler = BackgroundScheduler()
    
    # Monthly retraining
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
    
    # Initial fetch 5 seconds after server startup
    scheduler.add_job(
        smart_live_metar_fetch,
        'date',
        run_date=datetime.now() + timedelta(seconds=5),
        args=[scheduler],
        id='initial_startup_fetch',
        name='Initial Startup METAR Fetch',
        replace_existing=True
    )
    
    scheduler.start()
    print("✅ MLOps Background Scheduler started. Next run: 1st of the month at 00:00.")
    print("✅ Smart Live METAR Fetcher scheduled to run every 32 minutes (retries every 5m if delayed).")
    print("✅ Daily METAR Backup Fetcher scheduled to run every day at 01:00 AM.")
    
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
