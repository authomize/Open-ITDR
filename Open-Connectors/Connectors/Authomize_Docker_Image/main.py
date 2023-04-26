import time
import subprocess
from datetime import datetime
from croniter import croniter
import threading
import logging

# Import scripts_to_schedule from schedule_config.py
from schedule_config import scripts_to_schedule

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='/app/main.log',  # Set the log file path
    filemode='w'  # Set the file mode to write or append new log entries
)

def run_scheduled_task(cron_expression, script_path):
    cron_iter = croniter(cron_expression, datetime.now())

    # Run the script at start
    logging.info(f"First Run: {script_path}")
    subprocess.run(["python3", script_path])
    logging.info(f"Sleeping - Finished First Run: {script_path}")

    while True:
        next_run_time = cron_iter.get_next(datetime)
        logging.info(f"Next run time for {script_path}: {next_run_time}")
        time.sleep((next_run_time - datetime.now()).total_seconds())
        logging.info(f"Running {script_path}")
        subprocess.run(["python3", script_path])

def schedule_scripts(scripts):
    threads = []

    for script in scripts:
        t = threading.Thread(target=run_scheduled_task, args=(script['cron'], script['path']))
        t.start()
        threads.append(t)

    for thread in threads:
        thread.join()

if __name__ == "__main__":
    schedule_scripts(scripts_to_schedule)
