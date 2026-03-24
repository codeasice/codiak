-- Core data tables (populated by YNAB sync)
CREATE TABLE IF NOT EXISTS accounts (
    id TEXT PRIMARY KEY,
    budget_id TEXT NOT NULL,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    on_budget INTEGER NOT NULL,
    closed INTEGER NOT NULL DEFAULT 0,
    balance REAL NOT NULL DEFAULT 0,
    cleared_balance REAL NOT NULL DEFAULT 0,
    uncleared_balance REAL NOT NULL DEFAULT 0,
    note TEXT,
    deleted INTEGER NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS category_groups (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    hidden INTEGER NOT NULL DEFAULT 0,
    deleted INTEGER NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS categories (
    id TEXT PRIMARY KEY,
    category_group_id TEXT NOT NULL REFERENCES category_groups(id),
    name TEXT NOT NULL,
    hidden INTEGER NOT NULL DEFAULT 0,
    budgeted REAL NOT NULL DEFAULT 0,
    activity REAL NOT NULL DEFAULT 0,
    balance REAL NOT NULL DEFAULT 0,
    goal_type TEXT,
    goal_target REAL,
    goal_target_month TEXT,
    goal_percentage_complete INTEGER,
    note TEXT,
    deleted INTEGER NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS payees (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    deleted INTEGER NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS transactions (
    id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL REFERENCES accounts(id),
    date TEXT NOT NULL,
    amount REAL NOT NULL,
    payee_id TEXT REFERENCES payees(id),
    payee_name TEXT,
    category_id TEXT REFERENCES categories(id),
    category_name TEXT,
    memo TEXT,
    cleared TEXT NOT NULL,
    approved INTEGER NOT NULL DEFAULT 0,
    transfer_account_id TEXT,
    deleted INTEGER NOT NULL DEFAULT 0,
    imported_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_transactions_account_id ON transactions(account_id);
CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(date);
CREATE INDEX IF NOT EXISTS idx_transactions_category_id ON transactions(category_id);
CREATE INDEX IF NOT EXISTS idx_transactions_payee_id ON transactions(payee_id);

-- Sync tracking
CREATE TABLE IF NOT EXISTS sync_state (
    account_id TEXT PRIMARY KEY REFERENCES accounts(id),
    server_knowledge INTEGER NOT NULL DEFAULT 0,
    last_sync_at TEXT,
    last_sync_status TEXT NOT NULL DEFAULT 'never',
    last_error TEXT,
    transactions_synced INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS sync_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id TEXT REFERENCES accounts(id),
    event_type TEXT NOT NULL,
    details TEXT,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_sync_log_created_at ON sync_log(created_at);

-- Settings
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
