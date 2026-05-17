CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE stories (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  topic         TEXT,
  input_url     TEXT,
  root_outlet   TEXT,
  root_url      TEXT,
  root_headline TEXT,
  root_text     TEXT,
  root_dna      JSONB,
  status        TEXT DEFAULT 'processing',
  created_at    TIMESTAMP DEFAULT NOW()
);

CREATE TABLE outlet_versions (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  story_id      UUID REFERENCES stories(id) ON DELETE CASCADE,
  outlet        TEXT NOT NULL,
  country       TEXT NOT NULL,
  url           TEXT,
  headline      TEXT,
  article_text  TEXT,
  dna           JSONB,
  drift_score   INTEGER CHECK (drift_score BETWEEN 0 AND 100),
  parent_outlet TEXT,
  language      TEXT DEFAULT 'en',
  crawled_at    TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_outlet_story   ON outlet_versions(story_id);
CREATE INDEX idx_outlet_country ON outlet_versions(country);
CREATE INDEX idx_outlet_drift   ON outlet_versions(drift_score);
