WITH area_trends AS (
    SELECT
        report_month,
        circle,
        division,
        subdivision,
        section,
        area,
        units,
        LAG(units) OVER (
            PARTITION BY circle, division, subdivision, section, area, catcode
            ORDER BY report_month
        ) AS previous_units
    FROM ev_consumption_monthly
    WHERE area IN ('NALLAGADLA HV', 'HV GOWLI DODDI')
)
SELECT
    report_month,
    circle,
    section,
    area,
    units,
    previous_units,
    units - previous_units AS change_from_previous_month
FROM area_trends
ORDER BY area, report_month;
