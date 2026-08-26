CREATE TABLE geo_handoffs (
  token_hash TEXT PRIMARY KEY CHECK (length(token_hash) = 64),
  receipt_json TEXT NOT NULL CHECK (length(receipt_json) <= 16384),
  created_at INTEGER NOT NULL,
  expires_at INTEGER NOT NULL CHECK (expires_at > created_at),
  consumed_at INTEGER CHECK (consumed_at IS NULL OR consumed_at >= created_at)
);

CREATE INDEX geo_handoffs_expires_at_idx ON geo_handoffs (expires_at);
