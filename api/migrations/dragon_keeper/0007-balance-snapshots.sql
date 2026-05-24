-- Balance snapshots: store account balances on each sync for trend charts
CREATE TABLE IF NOT EXISTS balance_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_date TEXT NOT NULL,
    account_id TEXT,
    account_name TEXT,
    account_type TEXT,
    balance REAL NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_balance_snap_date ON balance_snapshots(snapshot_date);
CREATE INDEX IF NOT EXISTS idx_balance_snap_acct ON balance_snapshots(account_id, snapshot_date);

-- Aggregate snapshot: totals per day
CREATE TABLE IF NOT EXISTS balance_daily_totals (
    snapshot_date TEXT PRIMARY KEY,
    checking_total REAL NOT NULL DEFAULT 0,
    credit_total REAL NOT NULL DEFAULT 0,
    savings_total REAL NOT NULL DEFAULT 0,
    net_worth REAL NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);
