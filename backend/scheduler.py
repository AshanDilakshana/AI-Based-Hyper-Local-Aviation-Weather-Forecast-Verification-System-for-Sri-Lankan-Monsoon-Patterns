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
    print(f"[{datetime.now()}] Starting scheduled MLOps retraining pipeline...")
    

    # 1. Ashan's Wind Models Retraining
    try:
        run_wind_models_retraining()
    except Exception as e:
        log_scheduler_error("MLOps_Wind", "Wind Models Retraining failed", e)
        
    # 2. Cloud & Visibility Models Retraining
    try:
        success, msg = run_cloud_visibility_retraining()
        print(f"[{datetime.now()}] MLOps Retraining: {msg}")
    except Exception as e:
        log_scheduler_error("MLOps_Cloud_Vis", "Cloud/Visibility Models Retraining failed", e)
    
    # ---------------------------------------------------------
    # (imash,sachiii,vijjj): Add your model retraining functions here!
    # (Use try...except so missing files don't crash the scheduler)
    # ---------------------------------------------------------
    try:
        from backend.mlops_retrainer import retrain_temperature_pressure_pipeline
        retrain_temperature_pressure_pipeline()
    except Exception as e:
        log_scheduler_error("MLOps_Temp_Press", "Failed to run Temp/Pressure retraining pipeline", e)
    # ---------------------------------------------------------
    
    
    # Hot-reload the models into memory so the API uses the newly trained versions
    try:
        from backend.api.routers.wind_router import load_Wind_models
        load_Wind_models()
    except Exception as e:
        log_scheduler_error("MLOps_Wind_Router", "Failed to hot-reload Wind models", e)
        
    try:
        # Note: Correcting the load function name to match the implementation if it's different.
        # But we'll just keep it as is, and catch the error.
        from backend.api.routers.cloud_visibility_router import load_models
        load_models()
        print(f"[{datetime.now()}] Cloud & Visibility models hot-reloaded successfully.")
    except Exception as e:
        log_scheduler_error("MLOps_Cloud_Vis_Router", "Failed to hot-reload Cloud & Visibility models", e)
    
    # ---------------------------------------------------------
    # (imash,sachiii,vijjj): Call your model loading functions here 
    # so they update in RAM automatically after monthly retraining!
    # ---------------------------------------------------------
    try:
        from backend.api.routers.temperature_pressure_router import load_Temp_Press_models
        load_Temp_Press_models()
    except Exception as e:
        log_scheduler_error("MLOps_Temp_Press_Router", "Failed to hot-reload Temperature & Pressure models", e)
    
    # ---------------------------------------------------------
    # (viji): Add your model retraining functions here!
    # ---------------------------------------------------------
    try:
        run_qnh_dewpoint_retraining()
    except Exception as e:
        log_scheduler_error("MLOps_QNH_Dewpoint", "Failed to retrain QNH & Dewpoint models", e)
    # ---------------------------------------------------------
    
    # ---------------------------------------------------------
    # (viji): Call your model loading functions here 
    # so they update in RAM automatically after monthly retraining!
    # ---------------------------------------------------------
    try:
        from backend.api.routers.qnh_dewpoint_router import load_QNH_Dewpoint_models
        load_QNH_Dewpoint_models()
    except Exception as e:
        log_scheduler_error("MLOps_QNH_Dewpoint_Router", "Failed to hot-reload QNH & Dewpoint models", e)
    # ---------------------------------------------------------
    
    print(f"[{datetime.now()}] Scheduled retraining complete and models hot-reloaded.")



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
