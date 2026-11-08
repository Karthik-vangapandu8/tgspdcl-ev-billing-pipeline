# TGSPDCL EV Charging Billing Pipeline

A Python batch pipeline and Streamlit dashboard for monthly TGSPDCL billing records for the EV charging category.

## What it does

1. Profiles monthly CSV files and checks the expected schema, required values, numeric fields, and duplicate area/category keys.
2. Adds a reporting month from each filename and combines the source files into one processed CSV.
3. Loads the records into PostgreSQL with an upsert keyed by reporting month and the area/category hierarchy.
4. Provides SQL analysis and a dashboard with month and circle filters, billing metrics, trends, ranked areas, and CSV export.

## Data source and interpretation

Source: [TGSPDCL EV charging stations consumption data](https://data.telangana.gov.in/dataset/tgspdcl-ev-charging-stations-consumption-data)

The source description says the data is available from June 2021 through October 2026. This project currently processes the August, September, and October 2026 CSVs (1,576 records total).

The source defines totservices as total connections/services during the month and billdservices as connections/services billed during the month. Units is the number of units billed in the month; the source description does not specify the physical unit. For category code 9, load is billed load in kW.

The files contain utility location fields and service counts, but no individual charger identifier, charging session, or coordinates. The dashboard therefore describes area-level billing records, not individual charger usage. Blank billdservices values are kept as SQL NULL; they are not converted to zero.

## Pipeline layout

    data/raw/*.csv
        -> inspectdata.py (schema and data-quality gate)
        -> builddataset.py (combine files and add report_month)
        -> data/processed/ev_consumption_aug_oct_2026.csv
        -> load_data.py (PostgreSQL upsert)
        -> ev_consumption_monthly
        -> dashboard.py / sql/area_trends.sql

Raw and processed CSV files are excluded from Git. Download the monthly source files and place them in data/raw/ before running the pipeline.

## Run locally

Prerequisites: Python 3.11+ and a local PostgreSQL server.

    python3 -m venv .venv
    source .venv/bin/activate
    python -m pip install -r requirements.txt

    createdb ev_charging_dw
    psql -d ev_charging_dw -f sql/schema.sql
    python pipeline.py
    streamlit run dashboard.py

Place source CSVs in data/raw/ using filenames that end in _MM_YYYY.csv, for example:

- TG-SPDCL_consumption_detail_ev_charging_stations_08_2026.csv
- TG-SPDCL_consumption_detail_ev_charging_stations_09_2026.csv
- TG-SPDCL_consumption_detail_ev_charging_stations_10_2026.csv

The dashboard uses dbname=ev_charging_dw locally. Set DATABASE_URL to a PostgreSQL connection URL when using a remote database. Do not commit database credentials.

## SQL analysis

Run the area trend query with:

    psql -d ev_charging_dw -f sql/area_trends.sql
