-- Epic 3: Engagement tracking for daily financial habit
CREATE TABLE IF NOT EXISTS engagement_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL UNIQUE,
    visit_count INTEGER NOT NULL DEFAULT 1,
    actions_count INTEGER NOT NULL DEFAULT 0,
    first_visit_at TEXT NOT NULL,
    last_visit_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_engagement_date ON engagement_log(date);
