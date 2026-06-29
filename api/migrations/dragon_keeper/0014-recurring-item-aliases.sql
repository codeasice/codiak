-- Link alternate payee names to a canonical recurring subscription
CREATE TABLE IF NOT EXISTS recurring_item_aliases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recurring_id INTEGER NOT NULL REFERENCES recurring_items(id) ON DELETE CASCADE,
    payee_name TEXT NOT NULL COLLATE NOCASE,
    created_at TEXT NOT NULL,
    UNIQUE(payee_name COLLATE NOCASE)
);

CREATE INDEX IF NOT EXISTS idx_recurring_aliases_recurring_id
    ON recurring_item_aliases(recurring_id);
