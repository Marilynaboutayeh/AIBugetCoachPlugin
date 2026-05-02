import time
import requests
from datetime import datetime


URL = "http://127.0.0.1:8000/health"
DURATION_SECONDS = 10 * 60  # 10 minutes
INTERVAL_SECONDS = 5

total_checks = 0
successful_checks = 0
failed_checks = 0

start_time = time.time()

while time.time() - start_time < DURATION_SECONDS:
    total_checks += 1
    try:
        response = requests.get(URL, timeout=2)
        if response.status_code == 200:
            successful_checks += 1
            print(f"{datetime.now()} - OK")
        else:
            failed_checks += 1
            print(f"{datetime.now()} - FAIL status={response.status_code}")
    except Exception as e:
        failed_checks += 1
        print(f"{datetime.now()} - FAIL error={e}")

    time.sleep(INTERVAL_SECONDS)

uptime = (successful_checks / total_checks) * 100 if total_checks else 0

print("\n--- Uptime Test Result ---")
print(f"Total checks: {total_checks}")
print(f"Successful checks: {successful_checks}")
print(f"Failed checks: {failed_checks}")
print(f"Observed uptime: {uptime:.2f}%")