-- Continuum — CockroachDB schema
-- Run once against the Serverless cluster (see scripts/apply_schema.py)

-- Vector indexes are a newer feature and require this flag.
SET CLUSTER SETTING feature.vector_index.enabled = true;

-- Long-term memory: past incidents + resolutions, searchable by semantic similarity.
CREATE TABLE IF NOT EXISTS incidents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title STRING NOT NULL,
  description STRING NOT NULL,
  root_cause STRING,
  resolution STRING,
  severity STRING NOT NULL CHECK (severity IN ('critical', 'warning', 'info')),
  tags STRING[],
  embedding VECTOR(768), -- Gemini embedding, requested at 768 dims to match this column
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  resolved_at TIMESTAMPTZ
);

-- Cosine distance is the right metric for text embeddings (direction, not magnitude).
CREATE VECTOR INDEX IF NOT EXISTS incidents_embedding_idx
  ON incidents (embedding vector_cosine_ops);

-- Short-term memory: state of the incident currently being handled.
CREATE TABLE IF NOT EXISTS active_incidents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title STRING NOT NULL,
  status STRING NOT NULL CHECK (status IN ('investigating', 'mitigating', 'resolved')),
  severity STRING NOT NULL CHECK (severity IN ('critical', 'warning', 'info')),
  opened_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  closed_at TIMESTAMPTZ
);

-- Timeline of everything said/done during an active incident (transactional log).
CREATE TABLE IF NOT EXISTS incident_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  incident_id UUID NOT NULL REFERENCES active_incidents(id),
  actor STRING NOT NULL CHECK (actor IN ('agent', 'user')),
  event_type STRING NOT NULL CHECK (event_type IN ('message', 'hypothesis', 'action', 'citation')),
  content STRING NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS incident_events_by_incident ON incident_events (incident_id, created_at);
