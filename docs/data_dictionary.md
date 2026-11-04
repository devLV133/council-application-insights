# Data dictionary and metric definitions

All raw files use UTF-8 CSV. IDs are case-sensitive stable keys. Whitespace is trimmed. Blank optional fields become SQL NULL. There are no resident records or personal contact details.

| Source | One row represents | Key | Other fields |
|---|---|---|---|
| owners | An accountable team | owner_id | owner_team |
| applications | An application | app_id | application, owner_id (nullable), annual_cost_gbp (nullable), last_reviewed (nullable) |
| services | A service | service_id | service, criticality (High/Medium/Low) |
| technologies | A technology | technology_id | technology, support_end (nullable) |
| application_services | A direct service mapping | app_id + service_id | Both IDs must exist |
| application_technologies | A technology used by an application | app_id + technology_id | Both IDs must exist |
| dependencies | A directed dependency | app_id + depends_on_app_id | Application depends on the named target. Self-links are rejected |

Dates must be YYYY-MM-DD. Costs are annual GBP amounts, non-negative, with at most two decimal places. Zero is a known value. Blank means unknown. Future review dates are retained and flagged, not silently corrected. Duplicate source keys and orphan relationships stop the load.

## Eight quality rules

| Rule | Trigger |
|---|---|
| Missing owner | owner_id is NULL |
| Missing annual cost | annual_cost_gbp is NULL |
| Missing review | last_reviewed is NULL |
| Stale review | last_reviewed is strictly before as_of_date minus stale_days |
| Future review | last_reviewed is strictly after as_of_date |
| Missing service mapping | No application_services row exists |
| Missing technology mapping | No application_technologies row exists |
| Unknown support end date | At least one mapped technology has a NULL support_end |

Each rule creates at most one issue per application. An application may have several issues. Quality pass rate = applications with none of these issues / all applications. It measures conformity to these eight rules, not proof that all source data is accurate.

## Support and dependency metrics

- **Expired support:** at least one mapped technology has support_end strictly before the reporting date. Support is treated as valid through its end date.
- **Unknown support:** at least one mapped technology has no end date. This flag may coexist with expiry when an application has several technologies.
- **Service exposure:** distinct directly mapped applications with each flag. It does not propagate risk through transitive dependency paths.
- **Dependent applications:** number of distinct applications directly depending on the target. No outage probability or resilience score is inferred.
- **Known annual cost:** sum of available costs at application grain. It is not allocated across services and is not a savings estimate.

## Output grains

`portfolio`: application. `quality_issues`: application plus rule. `dependency_detail`: directed application pair. `service_exposure`: service. `technology_exposure`: technology. `report_context`: one row containing the date and threshold.

The Power BI model relates Applications to Issues and Dependencies by app_id using one-way filtering. Services and Technologies are separate aggregated tables; selecting them does not filter the application detail. This avoids an ambiguous many-to-many model. Extend the model deliberately if cross-filtering between every entity is needed.
