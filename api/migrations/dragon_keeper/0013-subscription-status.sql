-- Add subscription flag and explicit status to recurring items
ALTER TABLE recurring_items ADD COLUMN is_subscription INTEGER NOT NULL DEFAULT 1;
ALTER TABLE recurring_items ADD COLUMN status TEXT NOT NULL DEFAULT 'active';

-- Migrate existing cancelled items
UPDATE recurring_items SET status = 'cancelled' WHERE cancelled_date IS NOT NULL;

-- Income items (paychecks) are not subscriptions
UPDATE recurring_items SET is_subscription = 0 WHERE type = 'income';
