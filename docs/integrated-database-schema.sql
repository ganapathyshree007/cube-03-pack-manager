-- Integrated additions from Alembic 002. Documentation export, not a migration runner.

-- Existing Pack tables are unchanged. Timestamps/defaults are supplied by application code.


CREATE TABLE cw_requests (
	organization_id VARCHAR NOT NULL,
	id VARCHAR NOT NULL,
	body_hash VARCHAR NOT NULL,
	response JSONB NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE NOT NULL,
	PRIMARY KEY (organization_id, id)
)

;

ALTER TABLE cw_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE cw_requests FORCE ROW LEVEL SECURITY;

CREATE POLICY tenant_scope ON cw_requests USING (organization_id = current_setting('app.organization_id', true)) WITH CHECK (organization_id = current_setting('app.organization_id', true));

GRANT SELECT, INSERT, UPDATE, DELETE ON cw_requests TO pack_app;


CREATE TABLE cw_units (
	organization_id VARCHAR NOT NULL,
	id VARCHAR NOT NULL,
	data JSONB NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE NOT NULL,
	PRIMARY KEY (organization_id, id)
)

;

ALTER TABLE cw_units ENABLE ROW LEVEL SECURITY;
ALTER TABLE cw_units FORCE ROW LEVEL SECURITY;

CREATE POLICY tenant_scope ON cw_units USING (organization_id = current_setting('app.organization_id', true)) WITH CHECK (organization_id = current_setting('app.organization_id', true));

GRANT SELECT, INSERT, UPDATE, DELETE ON cw_units TO pack_app;


CREATE TABLE cw_workflows (
	organization_id VARCHAR NOT NULL,
	id VARCHAR NOT NULL,
	unit_id VARCHAR NOT NULL,
	data JSONB NOT NULL,
	version INTEGER NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE NOT NULL,
	PRIMARY KEY (organization_id, id),
	UNIQUE (organization_id, unit_id),
	FOREIGN KEY(organization_id, unit_id) REFERENCES cw_units (organization_id, id)
)

;

ALTER TABLE cw_workflows ENABLE ROW LEVEL SECURITY;
ALTER TABLE cw_workflows FORCE ROW LEVEL SECURITY;

CREATE POLICY tenant_scope ON cw_workflows USING (organization_id = current_setting('app.organization_id', true)) WITH CHECK (organization_id = current_setting('app.organization_id', true));

GRANT SELECT, INSERT, UPDATE, DELETE ON cw_workflows TO pack_app;


CREATE TABLE cw_events (
	organization_id VARCHAR NOT NULL,
	id VARCHAR NOT NULL,
	workflow_id VARCHAR NOT NULL,
	run_id VARCHAR,
	data JSONB NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE NOT NULL,
	PRIMARY KEY (organization_id, id),
	FOREIGN KEY(organization_id, workflow_id) REFERENCES cw_workflows (organization_id, id)
)

;

ALTER TABLE cw_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE cw_events FORCE ROW LEVEL SECURITY;

CREATE POLICY tenant_scope ON cw_events USING (organization_id = current_setting('app.organization_id', true)) WITH CHECK (organization_id = current_setting('app.organization_id', true));

GRANT SELECT, INSERT ON cw_events TO pack_app;


CREATE TABLE cw_runs (
	organization_id VARCHAR NOT NULL,
	id VARCHAR NOT NULL,
	workflow_id VARCHAR NOT NULL,
	manager VARCHAR NOT NULL,
	trigger_id VARCHAR NOT NULL,
	state VARCHAR NOT NULL,
	data JSONB NOT NULL,
	version INTEGER NOT NULL,
	lease_owner VARCHAR,
	lease_until TIMESTAMP WITH TIME ZONE,
	retry_at TIMESTAMP WITH TIME ZONE,
	retries INTEGER NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE NOT NULL,
	PRIMARY KEY (organization_id, id),
	UNIQUE (organization_id, workflow_id, manager, trigger_id),
	FOREIGN KEY(organization_id, workflow_id) REFERENCES cw_workflows (organization_id, id)
)

;

ALTER TABLE cw_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE cw_runs FORCE ROW LEVEL SECURITY;

CREATE POLICY tenant_scope ON cw_runs USING (organization_id = current_setting('app.organization_id', true)) WITH CHECK (organization_id = current_setting('app.organization_id', true));

GRANT SELECT, INSERT, UPDATE, DELETE ON cw_runs TO pack_app;


CREATE TABLE cw_calls (
	organization_id VARCHAR NOT NULL,
	id VARCHAR NOT NULL,
	unit_id VARCHAR NOT NULL,
	run_id VARCHAR NOT NULL,
	policy VARCHAR NOT NULL,
	state VARCHAR NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE NOT NULL,
	PRIMARY KEY (organization_id, id),
	UNIQUE (organization_id, unit_id),
	FOREIGN KEY(organization_id, unit_id) REFERENCES cw_units (organization_id, id),
	FOREIGN KEY(organization_id, run_id) REFERENCES cw_runs (organization_id, id)
)

;

ALTER TABLE cw_calls ENABLE ROW LEVEL SECURITY;
ALTER TABLE cw_calls FORCE ROW LEVEL SECURITY;

CREATE POLICY tenant_scope ON cw_calls USING (organization_id = current_setting('app.organization_id', true)) WITH CHECK (organization_id = current_setting('app.organization_id', true));

GRANT SELECT, INSERT, UPDATE, DELETE ON cw_calls TO pack_app;

CREATE INDEX cw_run_queue ON cw_runs (organization_id, state, retry_at);

CREATE INDEX cw_event_workflow ON cw_events (organization_id, workflow_id, created_at);
