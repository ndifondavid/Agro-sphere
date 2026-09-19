PRAGMA foreign_keys = ON;

ALTER TABLE listing ADD COLUMN package_size TEXT NOT NULL DEFAULT 'medium basket';
ALTER TABLE listing ADD COLUMN package_unit TEXT NOT NULL DEFAULT 'basket';