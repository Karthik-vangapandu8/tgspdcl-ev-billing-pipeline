import csv
from pathlib import Path

raw_folder = Path("data/raw")
files = sorted(
    raw_folder.glob("TG-SPDCL_consumption_detail_ev_charging_stations_*.csv")
)

expected_columns = [
    "circle",
    "division",
    "subdivision",
    "section",
    "area",
    "catdesc",
    "catcode",
    "totservices",
    "billdservices",
    "units",
    "load",
]

required_columns = [
    column for column in expected_columns if column != "billdservices"
]
numeric_columns = ["totservices", "billdservices", "units", "load"]
identity_columns = [
    "circle",
    "division",
    "subdivision",
    "section",
    "area",
    "catcode",
]

if not files:
    raise SystemExit("No input CSV files found in data/raw.")

validation_errors = []

for file_path in files:
    with file_path.open(newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        columns = reader.fieldnames or []

        if columns != expected_columns:
            raise SystemExit(
                f"Schema mismatch in {file_path.name}: {columns}"
            )

        rows = list(reader)

    blank_counts = {
        column: sum(not (row.get(column) or "").strip() for row in rows)
        for column in columns
    }

    missing_required = {
        column: blank_counts[column]
        for column in required_columns
        if blank_counts[column] > 0
    }

    if missing_required:
        validation_errors.append(
            f"{file_path.name}: missing required values {missing_required}"
        )

    row_signatures = {
        tuple(row.get(column, "") for column in columns)
        for row in rows
    }
    duplicate_count = len(rows) - len(row_signatures)

    if duplicate_count:
        validation_errors.append(
            f"{file_path.name}: {duplicate_count} repeated exact rows"
        )

    print(f"\nFile: {file_path.name}")
    print(f"Rows: {len(rows)}")
    print(f"Blank values by column: {blank_counts}")
    print(f"Repeated exact rows: {duplicate_count}")

    for column in numeric_columns:
        values = []
        invalid_count = 0

        for row in rows:
            value = (row.get(column) or "").strip()
            if not value:
                continue

            try:
                number = float(value)
                if column == "totservices" and not number.is_integer():
                    invalid_count += 1
                    continue
                values.append(number)
            except ValueError:
                invalid_count += 1

        print(
            f"{column}: "
            f"valid={len(values)}, "
            f"invalid={invalid_count}, "
            f"min={min(values) if values else 'n/a'}, "
            f"max={max(values) if values else 'n/a'}"
        )

        if invalid_count:
            validation_errors.append(
                f"{file_path.name}: {column} has "
                f"{invalid_count} invalid numeric value(s)"
            )

    billed_over_total = 0

    for row in rows:
        billed = (row.get("billdservices") or "").strip()
        total = (row.get("totservices") or "").strip()

        if not billed or not total:
            continue

        try:
            if float(billed) > float(total):
                billed_over_total += 1
        except ValueError:
            # The numeric check above records this as a validation error.
            continue

    print(
        "Rows where billed services exceed total services: "
        f"{billed_over_total}"
    )

    candidate_keys = [
        tuple((row.get(column) or "").strip() for column in identity_columns)
        for row in rows
    ]
    duplicate_key_count = len(candidate_keys) - len(set(candidate_keys))

    print(f"Repeated area/category keys: {duplicate_key_count}")

    if duplicate_key_count:
        validation_errors.append(
            f"{file_path.name}: {duplicate_key_count} repeated area/category keys"
        )

if validation_errors:
    print("\nQuality gate failed; pipeline must stop:")
    for error in validation_errors:
        print(f"- {error}")
    raise SystemExit(1)

print("\nQuality gate passed.")
print("Blank billdservices values are allowed and will remain NULL.")