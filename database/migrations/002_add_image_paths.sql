PRAGMA foreign_keys = ON;

ALTER TABLE farm ADD COLUMN image_path TEXT;
ALTER TABLE crop ADD COLUMN image_path TEXT;
ALTER TABLE listing ADD COLUMN image_path TEXT;
