import os

import pandas as pd
import psycopg
import streamlit as st
from psycopg.rows import dict_row


st.set_page_config(
    page_title="TGSPDCL EV Billing",
    page_icon="⚡",
    layout="wide",
)

DATABASE_URL = os.getenv("DATABASE_URL", "dbname=ev_charging_dw")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = "postgresql://" + DATABASE_URL.removeprefix("postgres://")


@st.cache_data(ttl=60)
def query_df(query, params=()):
    with psycopg.connect(DATABASE_URL, row_factory=dict_row) as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, params)
            return pd.DataFrame(cursor.fetchall())


st.title("TGSPDCL EV charging billing")
st.caption(
    "Monthly area-level billing records from the Telangana Southern Power "
    "Distribution Company (TGSPDCL)."
)
st.info(
    "These records describe utility areas and connection counts. "
    "They do not include individual charger IDs, charging sessions, or coordinates."
)
st.caption("Trend charts show all loaded months for the selected circle.")

try:
    months_df = query_df(
        "SELECT DISTINCT report_month "
        "FROM ev_consumption_monthly ORDER BY report_month"
    )
except Exception as error:
    st.error(
        "Could not connect to PostgreSQL or find the project table. "
        "For local use, start PostgreSQL and run python pipeline.py first."
    )
    st.exception(error)
    st.stop()

if months_df.empty:
    st.warning("No monthly records found. Run python pipeline.py first.")
    st.stop()

months = months_df["report_month"].tolist()

st.sidebar.header("Filters")
selected_month = st.sidebar.selectbox(
    "Month for summary and top areas",
    months,
    format_func=lambda value: value.strftime("%B %Y"),
)

circle_df = query_df(
    """
    SELECT DISTINCT circle
    FROM ev_consumption_monthly
    WHERE report_month = %s
    ORDER BY circle
    """,
    (selected_month,),
)
circles = ["All circles", *circle_df["circle"].tolist()]
selected_circle = st.sidebar.selectbox("TGSPDCL circle", circles)

conditions = ["report_month = %s"]
parameters = [selected_month]
if selected_circle != "All circles":
    conditions.append("circle = %s")
    parameters.append(selected_circle)
where_clause = " AND ".join(conditions)
query_parameters = tuple(parameters)

summary_df = query_df(
    f"""
    SELECT
        COUNT(*) AS area_records,
        COALESCE(SUM(totservices), 0) AS total_services,
        COALESCE(SUM(billdservices), 0) AS billed_services,
        COUNT(*) FILTER (WHERE billdservices IS NULL) AS missing_billed_services,
        COALESCE(SUM(units), 0) AS units_billed,
        COALESCE(SUM("load"), 0) AS load_billed_kw
    FROM ev_consumption_monthly
    WHERE {where_clause}
    """,
    query_parameters,
)
summary = summary_df.iloc[0]

metric_columns = st.columns(4)
metric_columns[0].metric(
    "Connections reported",
    f"{int(summary['total_services']):,}",
    help="Sum of source service counts across the selected area's records.",
)
metric_columns[1].metric(
    "Connections billed",
    f"{float(summary['billed_services']):,.0f}",
    help="SQL sums recorded billed-service values and excludes missing values.",
)
metric_columns[2].metric(
    "Units billed",
    f"{float(summary['units_billed']):,.0f}",
    help="The source calls this field units billed; it does not specify a physical unit.",
)
metric_columns[3].metric(
    "Load billed",
    f"{float(summary['load_billed_kw']):,.2f} kW",
    help="The source identifies catcode 9 load as kW.",
)
st.caption(f"{int(summary['area_records']):,} area records in this selection.")

missing_count = int(summary["missing_billed_services"])
if missing_count:
    st.warning(
        f"{missing_count} selected area record(s) have no billed-service count. "
        "Those values are kept as NULL; SQL sums exclude them."
    )

trend_conditions = []
trend_parameters = []
if selected_circle != "All circles":
    trend_conditions.append("circle = %s")
    trend_parameters.append(selected_circle)
trend_where_clause = (
    f"WHERE {' AND '.join(trend_conditions)}" if trend_conditions else ""
)

trend_df = query_df(
    f"""
    SELECT
        report_month,
        SUM(units)::double precision AS units_billed,
        SUM("load")::double precision AS load_billed_kw
    FROM ev_consumption_monthly
    {trend_where_clause}
    GROUP BY report_month
    ORDER BY report_month
    """,
    tuple(trend_parameters),
)

left_chart, right_chart = st.columns(2)
with left_chart:
    st.subheader("Units billed by month")
    st.line_chart(
        trend_df,
        x="report_month",
        y="units_billed",
        y_label="Units billed",
        alt="Reported units billed by month",
    )
with right_chart:
    st.subheader("Load billed by month")
    st.line_chart(
        trend_df,
        x="report_month",
        y="load_billed_kw",
        y_label="Load billed (kW)",
        alt="Load billed in kilowatts by month",
    )

area_df = query_df(
    f"""
    SELECT
        circle,
        division,
        subdivision,
        section,
        area,
        totservices,
        billdservices,
        units::double precision AS units_billed,
        "load"::double precision AS load_billed_kw
    FROM ev_consumption_monthly
    WHERE {where_clause}
    ORDER BY units DESC, circle, section, area
    LIMIT 10
    """,
    query_parameters,
)

st.subheader("Top areas by reported units billed")
if area_df.empty:
    st.info("No area records match these filters.")
else:
    area_df["location"] = area_df.apply(
        lambda row: f"{row['circle']} / {row['section']} / {row['area']}",
        axis=1,
    )
    chart_df = area_df.set_index("location")[["units_billed"]]
    st.bar_chart(
        chart_df,
        y="units_billed",
        x_label="Utility area",
        y_label="Units billed",
        horizontal=True,
    )

    display_columns = [
        "circle",
        "division",
        "subdivision",
        "section",
        "area",
        "totservices",
        "billdservices",
        "units_billed",
        "load_billed_kw",
    ]
    st.dataframe(
        area_df[display_columns],
        hide_index=True,
        use_container_width=True,
    )

    csv_data = area_df[display_columns].to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download these area records",
        data=csv_data,
        file_name=f"tgspdcl_ev_area_records_{selected_month:%Y_%m}.csv",
        mime="text/csv",
    )

st.divider()
st.caption(
    "Source: Telangana Open Data Portal. "
    "The selected files cover August–October 2026. "
    "Units billed are shown as reported; the source does not specify a physical unit."
)
