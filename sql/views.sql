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

CREATE VIEW dependency_detail AS
SELECT d.app_id, a.application, d.depends_on_app_id, b.application AS dependency,
       COALESCE(o.owner_team,'Unassigned') AS dependency_owner,
       p.unsupported_technology AS dependency_unsupported,
       p.unknown_support AS dependency_unknown_support
FROM dependencies d JOIN applications a ON a.app_id=d.app_id
JOIN applications b ON b.app_id=d.depends_on_app_id
LEFT JOIN owners o ON o.owner_id=b.owner_id JOIN portfolio p ON p.app_id=b.app_id;

CREATE VIEW service_exposure AS
SELECT s.service_id, s.service, s.criticality, COUNT(p.app_id) AS applications,
       COALESCE(SUM(p.unsupported_technology),0) AS unsupported_apps,
       COALESCE(SUM(p.missing_owner),0) AS unowned_apps,
       COALESCE(SUM(p.unknown_support),0) AS unknown_support_apps
FROM services s LEFT JOIN application_services a ON a.service_id=s.service_id
LEFT JOIN portfolio p ON p.app_id=a.app_id
GROUP BY s.service_id,s.service,s.criticality;

CREATE VIEW technology_exposure AS
SELECT t.technology_id,t.technology,t.support_end,COUNT(a.app_id) AS applications,
       CASE WHEN t.support_end IS NULL THEN 'Unknown'
            WHEN t.support_end<c.as_of_date THEN 'Expired' ELSE 'Supported' END AS support_status
FROM technologies t CROSS JOIN report_context c
LEFT JOIN application_technologies a ON a.technology_id=t.technology_id
GROUP BY t.technology_id,t.technology,t.support_end,c.as_of_date;
