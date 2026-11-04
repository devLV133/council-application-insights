-- SQL Server 2019+ demo. Run in a NEW, EMPTY database in SSMS or Azure Data Studio.
-- This script creates unqualified tables in your default schema, normally dbo.
-- Never run it against an operational database. It contains no DROP statements.
-- On rerun, existing-table checks stop execution rather than replacing data.
SET XACT_ABORT ON;
BEGIN TRANSACTION;

IF OBJECT_ID(N'dbo.owners', N'U') IS NOT NULL
    THROW 50001, 'Use a new empty demo database.', 1;

IF OBJECT_ID(N'dbo.applications', N'U') IS NOT NULL
    THROW 50001, 'Use a new empty demo database.', 1;

IF OBJECT_ID(N'dbo.services', N'U') IS NOT NULL
    THROW 50001, 'Use a new empty demo database.', 1;

IF OBJECT_ID(N'dbo.technologies', N'U') IS NOT NULL
    THROW 50001, 'Use a new empty demo database.', 1;

IF OBJECT_ID(N'dbo.application_services', N'U') IS NOT NULL
    THROW 50001, 'Use a new empty demo database.', 1;

IF OBJECT_ID(N'dbo.application_technologies', N'U') IS NOT NULL
    THROW 50001, 'Use a new empty demo database.', 1;

IF OBJECT_ID(N'dbo.dependencies', N'U') IS NOT NULL
    THROW 50001, 'Use a new empty demo database.', 1;

IF OBJECT_ID(N'dbo.report_context', N'U') IS NOT NULL
    THROW 50001, 'Use a new empty demo database.', 1;

-- Portable schema used by the tested SQLite runner and SQL Server setup script.
-- Required missing values are retained as NULL so quality issues remain visible.
CREATE TABLE owners (
    owner_id VARCHAR(20) PRIMARY KEY, owner_team VARCHAR(100) NOT NULL
);
CREATE TABLE applications (
    app_id VARCHAR(20) PRIMARY KEY, application VARCHAR(100) NOT NULL,
    owner_id VARCHAR(20) NULL REFERENCES owners(owner_id),
    annual_cost_gbp DECIMAL(14,2) NULL CHECK (annual_cost_gbp >= 0),
    last_reviewed DATE NULL
);
CREATE TABLE services (
    service_id VARCHAR(20) PRIMARY KEY, service VARCHAR(100) NOT NULL,
    criticality VARCHAR(10) NOT NULL CHECK (criticality IN ('High','Medium','Low'))
);
CREATE TABLE technologies (
    technology_id VARCHAR(20) PRIMARY KEY, technology VARCHAR(100) NOT NULL,
    support_end DATE NULL
);
CREATE TABLE application_services (
    app_id VARCHAR(20) REFERENCES applications(app_id),
    service_id VARCHAR(20) REFERENCES services(service_id),
    PRIMARY KEY (app_id, service_id)
);
CREATE TABLE application_technologies (
    app_id VARCHAR(20) REFERENCES applications(app_id),
    technology_id VARCHAR(20) REFERENCES technologies(technology_id),
    PRIMARY KEY (app_id, technology_id)
);
CREATE TABLE dependencies (
    app_id VARCHAR(20) REFERENCES applications(app_id),
    depends_on_app_id VARCHAR(20) REFERENCES applications(app_id),
    PRIMARY KEY (app_id, depends_on_app_id),
    CHECK (app_id <> depends_on_app_id)
);
CREATE TABLE report_context (
    context_id INTEGER PRIMARY KEY CHECK (context_id = 1),
    as_of_date DATE NOT NULL, review_cutoff DATE NOT NULL,
    stale_days INTEGER NOT NULL CHECK (stale_days > 0)
);

INSERT INTO owners (owner_id,owner_team) VALUES
(N'O01',N'Digital Platforms'),
(N'O02',N'Customer Operations'),
(N'O03',N'Revenue Systems'),
(N'O04',N'Housing Systems'),
(N'O05',N'Environmental Services');

INSERT INTO applications (app_id,application,owner_id,annual_cost_gbp,last_reviewed) VALUES
(N'A01',N'Resident Hub',N'O01',N'84000',N'2026-09-10'),
(N'A02',N'Contact Manager',N'O02',N'120000',N'2026-10-20'),
(N'A03',N'Revenue Desk',N'O03',N'160000',N'2026-04-01'),
(N'A04',N'Permit Portal',NULL,N'72000',N'2026-10-15'),
(N'A05',N'Legacy Register',N'O04',N'48000',N'2025-12-01'),
(N'A06',N'Collection Scheduler',N'O05',N'36000',N'2026-08-01'),
(N'A07',N'Document Store',N'O01',N'65000',N'2026-07-01'),
(N'A08',N'Payment Gateway',N'O03',N'54000',N'2026-10-01'),
(N'A09',N'Reporting Suite',N'O02',N'42000',N'2026-10-18'),
(N'A10',N'Grants Manager',NULL,NULL,NULL),
(N'A11',N'Case Archive',N'O04',N'30000',N'2026-04-15'),
(N'A12',N'Web Forms',N'O01',N'24000',N'2026-10-25');

INSERT INTO services (service_id,service,criticality) VALUES
(N'S01',N'Council Tax',N'High'),
(N'S02',N'Waste Collections',N'High'),
(N'S03',N'Housing',N'High'),
(N'S04',N'Licensing',N'Medium'),
(N'S05',N'Customer Contact',N'High'),
(N'S06',N'Community Grants',N'Medium');

INSERT INTO technologies (technology_id,technology,support_end) VALUES
(N'T01',N'Web Runtime Current',N'2028-12-31'),
(N'T02',N'Database Current',N'2029-06-30'),
(N'T03',N'Legacy Database',N'2026-06-30'),
(N'T04',N'Legacy Operating System',N'2025-12-31'),
(N'T05',N'Managed Integration Service',N'2028-11-30'),
(N'T06',N'Archive Engine',NULL);

INSERT INTO application_services (app_id,service_id) VALUES
(N'A01',N'S01'),
(N'A01',N'S02'),
(N'A01',N'S03'),
(N'A01',N'S04'),
(N'A01',N'S05'),
(N'A01',N'S06'),
(N'A02',N'S05'),
(N'A03',N'S01'),
(N'A04',N'S04'),
(N'A05',N'S03'),
(N'A06',N'S02'),
(N'A07',N'S01'),
(N'A07',N'S03'),
(N'A07',N'S04'),
(N'A07',N'S06'),
(N'A08',N'S01'),
(N'A08',N'S04'),
(N'A09',N'S05'),
(N'A10',N'S06'),
(N'A11',N'S03');

INSERT INTO application_technologies (app_id,technology_id) VALUES
(N'A01',N'T01'),
(N'A01',N'T02'),
(N'A02',N'T01'),
(N'A02',N'T02'),
(N'A03',N'T03'),
(N'A04',N'T01'),
(N'A04',N'T05'),
(N'A05',N'T03'),
(N'A05',N'T04'),
(N'A06',N'T01'),
(N'A07',N'T02'),
(N'A08',N'T05'),
(N'A09',N'T02'),
(N'A10',N'T01'),
(N'A11',N'T06'),
(N'A12',N'T01');

INSERT INTO dependencies (app_id,depends_on_app_id) VALUES
(N'A01',N'A02'),
(N'A01',N'A07'),
(N'A01',N'A08'),
(N'A03',N'A08'),
(N'A04',N'A07'),
(N'A04',N'A08'),
(N'A05',N'A07'),
(N'A06',N'A01'),
(N'A09',N'A02'),
(N'A10',N'A07'),
(N'A11',N'A07'),
(N'A12',N'A08');

INSERT INTO report_context VALUES (1,'2026-11-04','2026-05-08',180);
COMMIT;
GO

-- Each application appears once. Costs are never summed over a relationship join.
CREATE VIEW portfolio AS
SELECT a.app_id, a.application, COALESCE(o.owner_team, 'Unassigned') AS owner_team,
       a.annual_cost_gbp, a.last_reviewed,
       (SELECT COUNT(*) FROM application_services s WHERE s.app_id=a.app_id) AS service_count,
       (SELECT COUNT(*) FROM dependencies d WHERE d.depends_on_app_id=a.app_id) AS dependent_apps,
       CASE WHEN a.owner_id IS NULL THEN 1 ELSE 0 END AS missing_owner,
       CASE WHEN a.annual_cost_gbp IS NULL THEN 1 ELSE 0 END AS missing_cost,
       CASE WHEN a.last_reviewed IS NULL THEN 1 ELSE 0 END AS missing_review,
       CASE WHEN a.last_reviewed < c.review_cutoff THEN 1 ELSE 0 END AS stale_review,
       CASE WHEN a.last_reviewed > c.as_of_date THEN 1 ELSE 0 END AS future_review,
       CASE WHEN NOT EXISTS (SELECT 1 FROM application_services s WHERE s.app_id=a.app_id)
            THEN 1 ELSE 0 END AS missing_service,
       CASE WHEN NOT EXISTS (SELECT 1 FROM application_technologies t WHERE t.app_id=a.app_id)
            THEN 1 ELSE 0 END AS missing_technology,
       CASE WHEN EXISTS (
            SELECT 1 FROM application_technologies at JOIN technologies t
            ON t.technology_id=at.technology_id WHERE at.app_id=a.app_id AND t.support_end IS NULL
       ) THEN 1 ELSE 0 END AS unknown_support,
       CASE WHEN EXISTS (
            SELECT 1 FROM application_technologies at JOIN technologies t
            ON t.technology_id=at.technology_id WHERE at.app_id=a.app_id AND t.support_end<c.as_of_date
       ) THEN 1 ELSE 0 END AS unsupported_technology
FROM applications a LEFT JOIN owners o ON o.owner_id=a.owner_id CROSS JOIN report_context c;
GO

CREATE VIEW quality_issues AS
SELECT app_id, application, owner_team, 'Missing owner' AS issue, 'Assign an accountable team' AS action
FROM portfolio WHERE missing_owner=1
UNION ALL SELECT app_id, application, owner_team, 'Missing annual cost', 'Confirm annual cost with Finance'
FROM portfolio WHERE missing_cost=1
UNION ALL SELECT app_id, application, owner_team, 'Missing review date', 'Review the application record'
FROM portfolio WHERE missing_review=1
UNION ALL SELECT app_id, application, owner_team, 'Stale review', 'Review with the recorded owner'
FROM portfolio WHERE stale_review=1
UNION ALL SELECT app_id, application, owner_team, 'Future review date', 'Correct or explain the future date'
FROM portfolio WHERE future_review=1
UNION ALL SELECT app_id, application, owner_team, 'Missing service mapping', 'Confirm which service uses this application'
FROM portfolio WHERE missing_service=1
UNION ALL SELECT app_id, application, owner_team, 'Missing technology mapping', 'Record the supporting technology'
FROM portfolio WHERE missing_technology=1
UNION ALL SELECT app_id, application, owner_team, 'Unknown support end date', 'Verify support dates with the supplier'
FROM portfolio WHERE unknown_support=1;
GO

CREATE VIEW dependency_detail AS
SELECT d.app_id, a.application, d.depends_on_app_id, b.application AS dependency,
       COALESCE(o.owner_team,'Unassigned') AS dependency_owner,
       p.unsupported_technology AS dependency_unsupported,
       p.unknown_support AS dependency_unknown_support
FROM dependencies d JOIN applications a ON a.app_id=d.app_id
JOIN applications b ON b.app_id=d.depends_on_app_id
LEFT JOIN owners o ON o.owner_id=b.owner_id JOIN portfolio p ON p.app_id=b.app_id;
GO

CREATE VIEW service_exposure AS
SELECT s.service_id, s.service, s.criticality, COUNT(p.app_id) AS applications,
       COALESCE(SUM(p.unsupported_technology),0) AS unsupported_apps,
       COALESCE(SUM(p.missing_owner),0) AS unowned_apps,
       COALESCE(SUM(p.unknown_support),0) AS unknown_support_apps
FROM services s LEFT JOIN application_services a ON a.service_id=s.service_id
LEFT JOIN portfolio p ON p.app_id=a.app_id
GROUP BY s.service_id,s.service,s.criticality;
GO

CREATE VIEW technology_exposure AS
SELECT t.technology_id,t.technology,t.support_end,COUNT(a.app_id) AS applications,
       CASE WHEN t.support_end IS NULL THEN 'Unknown'
            WHEN t.support_end<c.as_of_date THEN 'Expired' ELSE 'Supported' END AS support_status
FROM technologies t CROSS JOIN report_context c
LEFT JOIN application_technologies a ON a.technology_id=t.technology_id
GROUP BY t.technology_id,t.technology,t.support_end,c.as_of_date;
GO

SELECT COUNT(*) AS applications, SUM(annual_cost_gbp) AS known_annual_cost_gbp FROM portfolio;
SELECT * FROM quality_issues ORDER BY app_id, issue;
SELECT * FROM service_exposure ORDER BY service_id;
