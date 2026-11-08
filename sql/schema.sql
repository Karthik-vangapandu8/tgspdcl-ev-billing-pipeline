CREATE TABLE IF NOT EXISTS ev_consumption_monthly (
    report_month DATE NOT NULL,
    circle TEXT NOT NULL,
    division TEXT NOT NULL,
    subdivision TEXT NOT NULL,
    section TEXT NOT NULL,
    area TEXT NOT NULL,
    catdesc TEXT NOT NULL,
    catcode TEXT NOT NULL,
    totservices INTEGER NOT NULL,
    billdservices NUMERIC(12, 2),
    units NUMERIC(14, 2) NOT NULL,
    load NUMERIC(12, 2) NOT NULL,
    source_file TEXT NOT NULL,
    PRIMARY KEY (
        report_month,
        circle,
        division,
        subdivision,
        section,
        area,
        catcode
    )
);

COMMENT ON COLUMN ev_consumption_monthly.report_month IS
    'Reporting month stored as the first day of that month.';
COMMENT ON COLUMN ev_consumption_monthly.circle IS
    'TGSPDCL administrative circle; source notes circles correspond to districts.';
COMMENT ON COLUMN ev_consumption_monthly.totservices IS
    'Total connections/services during the month, as defined by the source.';
COMMENT ON COLUMN ev_consumption_monthly.billdservices IS
    'Connections/services billed during the month; blank source values remain NULL.';
COMMENT ON COLUMN ev_consumption_monthly.units IS
    'Units billed during the month; source does not specify the physical unit.';
COMMENT ON COLUMN ev_consumption_monthly.load IS
    'Load billed; for category code 9 the source defines the unit as kW.';
COMMENT ON COLUMN ev_consumption_monthly.source_file IS
    'Original monthly CSV filename used to produce this record.';
