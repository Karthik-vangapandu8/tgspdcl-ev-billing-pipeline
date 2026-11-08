import csv
import re
from collections import Counter
from pathlib import Path

raw_folder = Path("data/raw")
processed_folder = Path("data/processed")
processed_folder.mkdir(parents=True, exist_ok=True)

files = sorted(
    raw_folder.glob("TG-SPDCL_consumption_detail_ev_charging_stations_*.csv")
)

output_file = processed_folder / "ev_consumption_aug_oct_2026.csv"
month_counts = Counter()
output_columns = None
total_rows = 0

with output_file.open("w", newline="", encoding="utf-8") as output:
    writer = None

    for file_path in files:
        match = re.search(r"_(\d{2})_(\d{4})$", file_path.stem)
        if not match:
            raise ValueError(f"Cannot read month and year from {file_path.name}")

        month, year = match.groups()
        report_month = f"{year}-{month}"

        with file_path.open(newline="", encoding="utf-8-sig") as source:
            reader = csv.DictReader(source)
            source_columns = reader.fieldnames or []

            if output_columns is None:
                output_columns = ["report_month", *source_columns]
                writer = csv.DictWriter(output, fieldnames=output_columns)
                writer.writeheader()
            elif source_columns != output_columns[1:]:
                raise ValueError(f"Unexpected columns in {file_path.name}")

            for row in reader:
                row["report_month"] = report_month
                writer.writerow(row)
                month_counts[report_month] += 1
                total_rows += 1

print(f"Created: {output_file}")
print(f"Total rows: {total_rows}")
print(f"Rows by month: {dict(sorted(month_counts.items()))}")