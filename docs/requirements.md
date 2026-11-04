# Business brief and acceptance criteria

This is a fictional brief for a council digital technology team. No stakeholder interviews or council engagement are claimed.

## Decisions

| Reader | Question | Evidence | Action enabled |
|---|---|---|---|
| Senior technical architect | Which services use technology with expired support? | Application-to-service and application-to-technology joins | Prioritise lifecycle assessment |
| Service lead | Who owns the systems my service uses? | Owner teams and unassigned records | Assign accountable owners |
| Data owner | Which records need correction? | Named quality rules, records and suggested actions | Maintain an issue queue |
| Finance partner | What annual cost is documented, and what is missing? | One row per application, cost coverage | Confirm missing costs before budgeting |
| Business analyst | Which applications would need review if a shared component changes? | Direct dependency table and dependent counts | Scope a change-impact discussion |

## Acceptance criteria

1. Every portfolio metric traces to a raw record and an explicit SQL rule.
2. Unknown costs and support dates remain visible. No value is imputed.
3. Multiple service or technology relationships do not duplicate application costs.
4. Duplicate keys, invalid relationships, malformed dates and invalid costs fail before export.
5. Reporting date and stale-review interval are explicit and reproducible.
6. Excel supplies a readable summary and editable calculations.
7. Power BI source includes the three required pages, field bindings, measures and refresh instructions. Native Desktop verification is recorded separately.
8. Findings distinguish observed sample data from proposed actions and unproven benefits.

## Follow-up evaluation

For a real pilot, agree metric definitions with data owners, ask an architect and service lead to use the report, record completion errors and feedback, then revise the report. Compare reviewed-record coverage and time to resolve issues at agreed future dates. This project has one synthetic snapshot and does not claim an adoption trend.
