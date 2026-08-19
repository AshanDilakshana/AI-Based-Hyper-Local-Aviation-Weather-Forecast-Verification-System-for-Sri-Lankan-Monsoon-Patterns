import os
import sys
from apscheduler.schedulers.background import BackgroundScheduler
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from backend.mlops_retrainer import run_wind_models_retraining
from backend.live_metar_fetcher import fetch_and_store_live_metar

from datetime import datetime, timedelta

def smart_live_metar_fetch(sched):
    """
    Fetches METAR data. If no new data is found (records_added == 0),
    it schedules a one-off retry job to run in 5 minutes.
    """
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

def scheduled_retraining_job():
    print(f"[{datetime.now()}] Starting scheduled MLOps retraining pipeline...")
    
    # 1. Ashan's Wind Models Retraining
    run_wind_models_retraining()
    
    # ---------------------------------------------------------
    # (imash,sachiii,vijjj): Add your model retraining functions here!
    # (Use try...except so missing files don't crash the scheduler)
    # ---------------------------------------------------------
    # try:
    #     from backend.mlops_retrainer_plugin import retrain_temperature_pressure_pipeline
    #     retrain_temperature_pressure_pipeline()
    # except ImportError:
    #     pass
    # ---------------------------------------------------------
    
    
    # Hot-reload the models into memory so the API uses the newly trained versions
    from backend.api.routers.wind_router import load_Wind_models
    load_Wind_models()
    
    # ---------------------------------------------------------
    # (imash,sachiii,vijjj): Call your model loading functions here 
    # so they update in RAM automatically after monthly retraining!
    # ---------------------------------------------------------
    # try:
    #     from backend.api.routers.temperature_pressure_router import load_Temp_Press_models
    #     load_Temp_Press_models()
    # except ImportError:
    #     pass
    #
    # try:
    #     from backend.api.routers.visibility_router import load_Visibility_models
    #     load_Visibility_models()
    # except ImportError:
    #     pass
    #
    # try:
    #     from backend.api.routers.clouds_router import load_Clouds_models
    #     load_Clouds_models()
    # except ImportError:
    #     pass
    # ---------------------------------------------------------
    
    print(f"[{datetime.now()}] Scheduled retraining complete and models hot-reloaded.")


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
