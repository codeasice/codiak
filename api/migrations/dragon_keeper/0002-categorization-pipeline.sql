-- Categorization rules (tier 1 of pipeline)
CREATE TABLE IF NOT EXISTS categorization_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    payee_pattern TEXT NOT NULL,
    match_type TEXT NOT NULL,  -- 'exact', 'contains', 'starts_with'
    category_id TEXT NOT NULL REFERENCES categories(id),
    min_amount REAL,
    max_amount REAL,
    confidence REAL NOT NULL DEFAULT 1.0,
    source TEXT NOT NULL,  -- 'manual', 'learned', 'imported'
    times_applied INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_rules_payee_pattern ON categorization_rules(payee_pattern);

-- Write-back queue (approved categorizations → YNAB)
CREATE TABLE IF NOT EXISTS write_back_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_id TEXT NOT NULL REFERENCES transactions(id),
    category_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',  -- 'pending', 'in_progress', 'completed', 'failed'
    retry_count INTEGER NOT NULL DEFAULT 0,
    error_message TEXT,
    created_at TEXT NOT NULL,
    completed_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_write_back_status ON write_back_queue(status);

-- Categorization tracking columns on transactions
ALTER TABLE transactions ADD COLUMN categorization_status TEXT;
ALTER TABLE transactions ADD COLUMN suggested_category_id TEXT;
ALTER TABLE transactions ADD COLUMN suggestion_confidence REAL;
ALTER TABLE transactions ADD COLUMN suggestion_source TEXT;
