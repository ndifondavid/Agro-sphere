PRAGMA foreign_keys = ON;

ALTER TABLE user ADD COLUMN phone TEXT;
ALTER TABLE user ADD COLUMN farm_location TEXT;
ALTER TABLE user ADD COLUMN language TEXT DEFAULT 'English';
ALTER TABLE user ADD COLUMN profile_image_path TEXT;