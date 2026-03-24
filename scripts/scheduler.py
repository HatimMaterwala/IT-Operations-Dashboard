import schedule
import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from monitor import init_db, run_once
from report  import generate_report

def job():
    run_once()

def report_job():
    generate_report()
    print("📊 Report exported to /reports folder")

if __name__ == "__main__":
    init_db()
    print("🚀 IT Operations Monitor Started")
    print("   Collecting metrics every 5 minutes")
    print("   Generating report every hour")
    print("   Press Ctrl+C to stop\n")

    # Collect immediately on start
    run_once()
    generate_report()

    # Then schedule
    schedule.every(5).minutes.do(job)
    schedule.every(1).hours.do(report_job)

    while True:
        schedule.run_pending()
        time.sleep(1)