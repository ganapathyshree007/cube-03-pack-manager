-- Pack Manager: repository schema export (not a live Supabase dump).
-- Generated from backend/db.py and migration 001.
-- Reference only: use Alembic for deployment; tables and pack_app may already exist.
-- IDs/timestamps/version/retry/status defaults are supplied by application code.
-- No database foreign keys are declared in this version.


CREATE TABLE checkpoints (
	id VARCHAR NOT NULL, 
	organization_id VARCHAR NOT NULL, 
	thread_id VARCHAR NOT NULL, 
	data JSONB NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
);

ALTER TABLE checkpoints ENABLE ROW LEVEL SECURITY;
ALTER TABLE checkpoints FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_scope ON checkpoints
  USING (organization_id = current_setting('app.organization_id', true))
  WITH CHECK (organization_id = current_setting('app.organization_id', true));
GRANT SELECT, INSERT, UPDATE, DELETE ON checkpoints TO pack_app;

CREATE TABLE events (
	id VARCHAR NOT NULL, 
	organization_id VARCHAR NOT NULL, 
	attempt_id VARCHAR NOT NULL, 
	data JSONB NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
);

ALTER TABLE events ENABLE ROW LEVEL SECURITY;
ALTER TABLE events FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_scope ON events
  USING (organization_id = current_setting('app.organization_id', true))
  WITH CHECK (organization_id = current_setting('app.organization_id', true));
GRANT SELECT, INSERT, UPDATE, DELETE ON events TO pack_app;

CREATE TABLE jobs (
	id VARCHAR NOT NULL, 
	organization_id VARCHAR NOT NULL, 
	attempt_id VARCHAR NOT NULL, 
	key VARCHAR NOT NULL, 
	body_hash VARCHAR NOT NULL, 
	status VARCHAR NOT NULL, 
	lease_owner VARCHAR, 
	lease_until TIMESTAMP WITH TIME ZONE, 
	retries INTEGER NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (organization_id, key), 
	UNIQUE (attempt_id)
);

ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE jobs FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_scope ON jobs
  USING (organization_id = current_setting('app.organization_id', true))
  WITH CHECK (organization_id = current_setting('app.organization_id', true));
GRANT SELECT, INSERT, UPDATE, DELETE ON jobs TO pack_app;

CREATE TABLE records (
	id VARCHAR NOT NULL, 
	organization_id VARCHAR NOT NULL, 
	kind VARCHAR NOT NULL, 
	data JSONB NOT NULL, 
	version INTEGER NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
);

ALTER TABLE records ENABLE ROW LEVEL SECURITY;
ALTER TABLE records FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_scope ON records
  USING (organization_id = current_setting('app.organization_id', true))
  WITH CHECK (organization_id = current_setting('app.organization_id', true));
GRANT SELECT, INSERT, UPDATE, DELETE ON records TO pack_app;

CREATE INDEX records_tenant_kind ON records (organization_id, kind);
CREATE INDEX events_attempt ON events (organization_id, attempt_id);
CREATE INDEX checkpoints_thread ON checkpoints (organization_id, thread_id, created_at);

-- Alembic also manages its own alembic_version administrative table.
-- Authentication and Supabase storage system schemas are not defined by this app.
