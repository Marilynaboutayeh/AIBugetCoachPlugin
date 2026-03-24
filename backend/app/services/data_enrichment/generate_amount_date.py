import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

CSV_FILE = Path("backend/data/without_category_name.csv")


def generate_amount() -> float:
    return round(random.uniform(5, 200), 2)


def generate_date(start_days_ago: int = 180) -> str:
    start_date = datetime.today() - timedelta(days=start_days_ago)
    random_days = random.randint(0, start_days_ago)
    generated_date = start_date + timedelta(days=random_days)
    return generated_date.strftime("%Y-%m-%d")


def enrich_file():
    rows = []

    with CSV_FILE.open("r", encoding="utf-8", newline="") as infile:
        reader = csv.DictReader(infile, delimiter=";")
        fieldnames = reader.fieldnames.copy()

        if "amount" not in fieldnames:
            fieldnames.append("amount")
        if "date" not in fieldnames:
            fieldnames.append("date")

        for row in reader:
            row["amount"] = generate_amount()
            row["date"] = generate_date()
            rows.append(row)

    with CSV_FILE.open("w", encoding="utf-8", newline="") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames, delimiter=";")
        writer.writeheader()
        writer.writerows(rows)

    print(f"Updated file in place: {CSV_FILE}")


if __name__ == "__main__":
    enrich_file()