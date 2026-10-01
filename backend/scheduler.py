import os
import sys
from apscheduler.schedulers.background import BackgroundScheduler
import time
from datetime import datetime, timedelta

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))
from backend.live_metar_fetcher import fetch_and_store_live_metar

from backend.data.database import SessionLocal
from backend.data.models import SystemLogs


def smart_live_metar_fetch(sched):
    """
    Fetches METAR data. If no new data is found (records_added == 0),
    it schedules a one-off retry job to run in 5 minutes.
    """
    try:
        records_added = fetch_and_store_live_metar(hours=2)

        if records_added == 0:
            print(
                f"[{datetime.now()}] No new data found. Rescheduling fetch in 5 minutes..."
            )
            run_date = datetime.now() + timedelta(minutes=5)
            sched.add_job(
                smart_live_metar_fetch,
                "date",
                run_date=run_date,
                args=[sched],
                id="live_metar_retry_job",
                name="Live METAR Retry Fetcher (5m)",
                replace_existing=True,
            )
        else:
            print(
                f"[{datetime.now()}] Successfully fetched {records_added} new records."
            )
    except Exception as e:
        print(f"[{datetime.now()}] Error fetching live METAR: {e}")


def log_scheduler_error(component: str, message: str, error: Exception):
    print(f"[{datetime.now()}] [ERROR] {component}: {message} - {error}")
    db = SessionLocal()
    try:
        log = SystemLogs(
            level="ERROR", component=component, message=message, details=str(error)
        )
        db.add(log)
        db.commit()
    except Exception as db_e:
        print(f"[{datetime.now()}] [ERROR] Failed to log to database: {db_e}")
    finally:
        db.close()


def clean_old_system_logs():
    """
    Deletes SystemLogs older than 30 days.
    """
    db = SessionLocal()
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        deleted_count = (
            db.query(SystemLogs).filter(SystemLogs.timestamp_utc < cutoff_date).delete()
        )
        db.commit()
        print(
            f"[{datetime.now()}] [OK] Successfully deleted {deleted_count} system logs older than 30 days (before {cutoff_date})."
        )
    except Exception as e:
        print(f"[{datetime.now()}] [ERROR] Failed to clean old system logs: {e}")
        db.rollback()
    finally:
        db.close()


def clean_old_temp_maps():
    """
    Deletes temporary map images older than 5 days to save disk space.
    """
    try:
        from backend.api.routers.pilot_router import TEMP_MAP_DIR
        if not os.path.exists(TEMP_MAP_DIR):
            return
            
        cutoff_time = time.time() - (5 * 24 * 60 * 60) # 5 days ago in seconds
        deleted_count = 0
        
        for filename in os.listdir(TEMP_MAP_DIR):
            file_path = os.path.join(TEMP_MAP_DIR, filename)
            if os.path.isfile(file_path):
                if os.path.getmtime(file_path) < cutoff_time:
                    os.remove(file_path)
                    deleted_count += 1
                    
        print(
            f"[{datetime.now()}] [OK] Successfully deleted {deleted_count} temp maps older than 5 days."
        )
    except Exception as e:
        print(f"[{datetime.now()}] [ERROR] Failed to clean old temp maps: {e}")


def scheduled_retraining_job():
    print(
        f"[{datetime.now()}] Triggering scheduled MLOps retraining pipeline via Celery..."
    )
    try:
        from backend.celery_worker import run_full_retraining_pipeline

        task = run_full_retraining_pipeline.delay()
        print(
            f"[{datetime.now()}] Retraining task successfully dispatched to Celery background worker (Task ID: {task.id})."
        )
    except Exception as e:
        log_scheduler_error(
            "MLOps_Scheduler", "Failed to dispatch Celery retraining task", e
        )


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
        "cron",
        day="1",
        hour="0",
        minute="0",
        id="monthly_retrain_job",
        name="MLOps Monthly Retraining",
        replace_existing=True,
    )

    # Fetch live METAR data every 32 minutes
    scheduler.add_job(
        smart_live_metar_fetch,
        "interval",
        minutes=32,
        args=[scheduler],
        id="live_metar_fetch_job",
        name="Live METAR Data Fetcher (32m)",
        replace_existing=True,
    )

    # Run a daily job to fetch the last 48 hours and fill any missing gaps
    # It runs at 01:00 AM every day
    scheduler.add_job(
        lambda: fetch_and_store_live_metar(hours=48),
        "cron",
        hour=1,
        minute=0,
        id="live_metar_daily_backup",
        name="Live METAR Data Backup Fetcher (48h)",
        replace_existing=True,
    )

    # Initial fetch 5 seconds after server startup
    scheduler.add_job(
        smart_live_metar_fetch,
        "date",
        run_date=datetime.now() + timedelta(seconds=5),
        args=[scheduler],
        id="initial_startup_fetch",
        name="Initial Startup METAR Fetch",
        replace_existing=True,
    )

    # Daily cleanup for system logs older than 30 days
    scheduler.add_job(
        clean_old_system_logs,
        "cron",
        hour=2,
        minute=0,
        id="daily_log_cleanup",
        name="Daily System Log Cleanup (30 Days)",
        replace_existing=True,
    )

    # Daily cleanup for temp maps older than 5 days
    scheduler.add_job(
        clean_old_temp_maps,
        "cron",
        hour=3,
        minute=0,
        id="daily_temp_maps_cleanup",
        name="Daily Temp Maps Cleanup (5 Days)",
        replace_existing=True,
    )

    scheduler.start()
    print("[OK] MLOps Background Scheduler started. Next run: 1st of the month at 00:00.")
    print(
        "[OK] Smart Live METAR Fetcher scheduled to run every 32 minutes (retries every 5m if delayed)."
    )
    print("[OK] Daily METAR Backup Fetcher scheduled to run every day at 01:00 AM.")
    print(
        "[OK] Daily System Log Cleanup scheduled to run every day at 02:00 AM (30-day retention)."
    )
    print(
        "[OK] Daily Temp Maps Cleanup scheduled to run every day at 03:00 AM (5-day retention)."
    )

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
