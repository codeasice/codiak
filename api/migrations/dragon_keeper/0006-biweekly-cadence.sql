-- Add biweekly cadence support: recreate table with updated CHECK constraint
CREATE TABLE IF NOT EXISTS recurring_items_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    payee_name TEXT NOT NULL,
    payee_pattern TEXT,
    type TEXT NOT NULL CHECK(type IN ('income', 'expense')),
    cadence TEXT NOT NULL CHECK(cadence IN ('biweekly', 'monthly', 'annual')),
    expected_amount REAL NOT NULL,
    expected_day INTEGER NOT NULL,
    next_expected_date TEXT NOT NULL,
    confirmed INTEGER NOT NULL DEFAULT 0,
    include_in_sts INTEGER NOT NULL DEFAULT 1,
    last_seen_date TEXT,
    avg_amount REAL,
    occurrence_count INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

INSERT INTO recurring_items_new SELECT * FROM recurring_items;
DROP TABLE recurring_items;
ALTER TABLE recurring_items_new RENAME TO recurring_items;

CREATE INDEX IF NOT EXISTS idx_recurring_next_date ON recurring_items(next_expected_date);
CREATE INDEX IF NOT EXISTS idx_recurring_payee ON recurring_items(payee_name);
