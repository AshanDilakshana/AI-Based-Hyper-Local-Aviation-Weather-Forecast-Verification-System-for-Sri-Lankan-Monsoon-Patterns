import os
import sys
from apscheduler.schedulers.background import BackgroundScheduler
import time
from datetime import datetime, timedelta

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

def smart_live_metar_fetch(sched):
    try:
        from backend.live_metar_fetcher import fetch_and_store_live_metar
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

        # Run verification of past predictions against actual METAR
        try:
            from backend.verification_service import verify_past_temp_pressure_predictions, run_auto_prediction_and_save
            verify_past_temp_pressure_predictions()
            run_auto_prediction_and_save()
        except Exception as e:
            print(f"Verification/Auto-prediction error: {e}")

    except ImportError:
        print("Warning: fetch_and_store_live_metar not found locally. Skipping live fetch.")

def daily_metar_backup():
    try:
        from backend.live_metar_fetcher import fetch_and_store_live_metar
        fetch_and_store_live_metar(hours=48)
    except ImportError:
        pass

def scheduled_retraining_job():
    print(f"[{datetime.now()}] Starting scheduled MLOps retraining pipeline...")
    
    # Imash's Temperature & Pressure Retraining (ACTIVE)
    try:
        from backend.mlops_retrainer import retrain_temperature_pressure_pipeline
        retrain_temperature_pressure_pipeline()
    except ImportError:
        pass
        
    try:
        from backend.api.routers.temperature_pressure_router import load_Temp_Press_models
        load_Temp_Press_models()
    except ImportError:
        pass
    
    # Placeholders for other members (if needed in future)
    
    print(f"[{datetime.now()}] Scheduled retraining complete and models hot-reloaded.")

def start_scheduler():
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
    
    # Initial fetch & verification 5 seconds after server startup
    scheduler.add_job(
        smart_live_metar_fetch,
        'date',
        run_date=datetime.now() + timedelta(seconds=5),
        args=[scheduler],
        id='initial_startup_fetch',
        name='Initial Startup METAR Fetch & Auto Verification',
        replace_existing=True
    )
    
    scheduler.start()
    print("[INFO] MLOps Background Scheduler started.")
    return scheduler

if __name__ == "__main__":
    scheduler = start_scheduler()
    try:
        while True:
            time.sleep(2)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        print("Scheduler shut down.")