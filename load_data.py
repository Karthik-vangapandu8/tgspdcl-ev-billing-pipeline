import csv
from datetime import date
from decimal import Decimal
from pathlib import Path

import psycopg

input_file = Path("data/processed/ev_consumption_aug_oct_2026.csv")

insert_sql = """
    INSERT INTO ev_consumption_monthly (
        report_month,
        circle,
        division,
        subdivision,
        section,
        area,
        catdesc,
        catcode,
        totservices,
        billdservices,
        units,
        load,
        source_file
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (
        report_month,
        circle,
        division,
        subdivision,
        section,
        area,
        catcode
    )
    DO UPDATE SET
        totservices = EXCLUDED.totservices,
        billdservices = EXCLUDED.billdservices,
        units = EXCLUDED.units,
        load = EXCLUDED.load,
        source_file = EXCLUDED.source_file
"""

records = []

with input_file.open(newline="", encoding="utf-8-sig") as file:
    reader = csv.DictReader(file)

    for row in reader:
        report_month = date.fromisoformat(row["report_month"] + "-01")
        source_file = (
            "TG-SPDCL_consumption_detail_ev_charging_stations_"
            f"{report_month:%m_%Y}.csv"
        )

        billed_value = row["billdservices"].strip()

        records.append(
            (
                report_month,
                row["circle"],
                row["division"],
                row["subdivision"],
                row["section"],
                row["area"],
                row["catdesc"],
                row["catcode"],
                int(row["totservices"]),
                Decimal(billed_value) if billed_value else None,
                Decimal(row["units"]),
                Decimal(row["load"]),
                source_file,
            )
        )

with psycopg.connect("dbname=ev_charging_dw") as connection:
    with connection.cursor() as cursor:
        cursor.executemany(insert_sql, records)

print(f"Processed {len(records)} rows into ev_consumption_monthly.")