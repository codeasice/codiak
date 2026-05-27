-- Add user-editable metadata to payees
ALTER TABLE payees ADD COLUMN display_name TEXT;
ALTER TABLE payees ADD COLUMN note TEXT;
