import os
import sys
from apscheduler.schedulers.background import BackgroundScheduler
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from backend.mlops_retrainer import run_all_retrainings
from backend.live_metar_fetcher import fetch_and_store_live_metar

def start_scheduler():
    """
    Initializes the APScheduler to run the MLOps retraining pipeline
    automatically on the 1st of every month at midnight, and fetch
    live METAR data every 30 minutes.
    """
    scheduler = BackgroundScheduler()
    
    # Run retraining on the 1st day of every month at midnight
    scheduler.add_job(
        run_all_retrainings,
        'cron',
        day='1',
        hour='0',
        minute='0',
        id='monthly_retrain_job',
        name='MLOps Monthly Retraining',
        replace_existing=True
    )

    # Fetch live METAR data every 15 minutes
    scheduler.add_job(
        fetch_and_store_live_metar,
        'cron',
        minute='*/15',
        id='live_metar_fetch_job',
        name='Live METAR Data Fetcher',
        replace_existing=True
    )
    
    scheduler.start()
    print("✅ MLOps Background Scheduler started. Next run: 1st of the month at 00:00.")
    print("✅ Live METAR Fetcher scheduled to run every 15 minutes.")
    
    # Keep the thread alive if running this script directly
    try:
        while True:
            time.sleep(2)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        print("Scheduler shut down.")

if __name__ == "__main__":
    start_scheduler()
