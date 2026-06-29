-- Per-category budget targets and per-period income configuration
CREATE TABLE IF NOT EXISTS budget_targets (
    category_id TEXT PRIMARY KEY,
    amount REAL NOT NULL,
    updated_at TEXT NOT NULL
);
