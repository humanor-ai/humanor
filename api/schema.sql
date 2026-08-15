-- humanor — D1 schema. Small on purpose: two tables carry the whole game.

CREATE TABLE IF NOT EXISTS rounds (
  no          INTEGER PRIMARY KEY,
  date        TEXT    NOT NULL,          -- YYYY-MM-DD, the day it goes live
  text        TEXT    NOT NULL,
  sha256      TEXT    NOT NULL,          -- the commitment, published with the line
  label       TEXT,                      -- NULL until reveal
  salt        TEXT,                      -- NULL until reveal
  source      TEXT,                      -- work, year, chapter
  published   INTEGER NOT NULL DEFAULT 0,
  revealed    INTEGER NOT NULL DEFAULT 0,
  votes_human INTEGER NOT NULL DEFAULT 0,
  votes_ai    INTEGER NOT NULL DEFAULT 0
);

-- One row per vote. voter is a random client id, never an identity.
-- The UNIQUE constraint is the whole anti-stuffing mechanism.
CREATE TABLE IF NOT EXISTS votes (
  round_no INTEGER NOT NULL,
  voter    TEXT    NOT NULL,
  choice   TEXT    NOT NULL CHECK (choice IN ('HUMAN','AI')),
  ts       INTEGER NOT NULL,
  PRIMARY KEY (round_no, voter)
);

CREATE INDEX IF NOT EXISTS idx_rounds_pub ON rounds(published, no DESC);
