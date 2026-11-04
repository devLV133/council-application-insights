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
