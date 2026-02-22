import schedule
import time
from dump_db import dump_database

# set any time
schedule.every().day.at("12:00").do(dump_database)

print("Scheduler started. Waiting to 12:00...")

while True:
    schedule.run_pending()
    time.sleep(30)