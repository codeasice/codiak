-- Add cancelled_date to recurring_items for soft-cancel support
ALTER TABLE recurring_items ADD COLUMN cancelled_date TEXT;
