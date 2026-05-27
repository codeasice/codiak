CREATE TABLE IF NOT EXISTS paycheck_config (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  gross_amount REAL NOT NULL,
  take_home_amount REAL NOT NULL,
  effective_date TEXT NOT NULL,
  notes TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS paycheck_deduction_items (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  paycheck_config_id INTEGER NOT NULL REFERENCES paycheck_config(id) ON DELETE CASCADE,
  category TEXT NOT NULL,
  name TEXT NOT NULL,
  amount REAL NOT NULL,
  sort_order INTEGER DEFAULT 0
);

INSERT OR IGNORE INTO paycheck_config (id, gross_amount, take_home_amount, effective_date, notes, created_at, updated_at)
VALUES (1, 6687.50, 3743.57, '2026-05-24', 'Seeded from pay stub', datetime('now'), datetime('now'));

INSERT OR IGNORE INTO paycheck_deduction_items (paycheck_config_id, category, name, amount, sort_order) VALUES
  (1, 'taxes',      'Federal Income Tax',  -908.77,  1),
  (1, 'taxes',      'Social Security Tax', -379.87,  2),
  (1, 'taxes',      'Medicare Tax',         -88.84,  3),
  (1, 'benefits',   'Prtx Dental',          -16.99,  4),
  (1, 'benefits',   'Prtx Med',            -537.90,  5),
  (1, 'benefits',   'Prtx Vision',           -5.63,  6),
  (1, 'retirement', '401(K)',              -535.00,  7),
  (1, 'other',      'Child Vol Life',        -0.92,  8),
  (1, 'other',      'Spouse Vol Life',       -0.92,  9),
  (1, 'other',      'Voluntary Life',        -1.85, 10),
  (1, 'other',      '401K Loan',           -467.24, 11);
