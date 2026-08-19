import os
import sys
# pyrefly: ignore [missing-import]
from apscheduler.schedulers.background import BackgroundScheduler
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from backend.mlops_retrainer import run_all_retrainings

def start_scheduler():
    """
    Initializes the APScheduler to run the MLOps retraining pipeline
    automatically on the 1st of every month at midnight.
    """
    scheduler = BackgroundScheduler()
    
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
    
    scheduler.start()
    print("[SUCCESS] MLOps Background Scheduler started. Next run: 1st of the month at 00:00.")
    
    try:
        while True:
            time.sleep(2)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        print("Scheduler shut down.")

if __name__ == "__main__":
    start_scheduler()
