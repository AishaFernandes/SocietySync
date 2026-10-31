BEGIN;

CREATE TABLE IF NOT EXISTS users (
    id            SERIAL PRIMARY KEY,
    name          TEXT NOT NULL,
    email         TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role          TEXT NOT NULL DEFAULT 'resident'
                  CHECK (role IN ('resident', 'admin')),
    flat_no       TEXT,
    phone         TEXT,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS notices (
    id         SERIAL PRIMARY KEY,
    title      TEXT NOT NULL,
    body       TEXT NOT NULL,
    created_by INTEGER NOT NULL REFERENCES users (id) ON DELETE RESTRICT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS complaints (
    id             SERIAL PRIMARY KEY,
    user_id        INTEGER NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    subject        TEXT NOT NULL,
    description    TEXT,
    status         TEXT NOT NULL DEFAULT 'open'
                   CHECK (status IN ('open', 'in_progress', 'resolved')),
    attachment_key TEXT,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS notification_log (
    id           SERIAL PRIMARY KEY,
    event_type   TEXT NOT NULL,
    payload      JSONB NOT NULL,
    processed_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_notices_created_at ON notices (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_complaints_user_id ON complaints (user_id);
CREATE INDEX IF NOT EXISTS idx_complaints_status ON complaints (status);

COMMIT;