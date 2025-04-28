CREATE TABLE IF NOT EXISTS project_snapshots (
    id SERIAL PRIMARY KEY,
    project_id TEXT REFERENCES bookings(project_id),
    image_url TEXT NOT NULL,
    storage_path TEXT NOT NULL DEFAULT 'project_snapshot',  -- Set default folder
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_project_snapshots_project_id ON project_snapshots(project_id);
