PRAGMA foreign_keys = ON;

ALTER TABLE farm ADD COLUMN description TEXT;
ALTER TABLE farm ADD COLUMN farm_size TEXT;
ALTER TABLE crop ADD COLUMN variety TEXT;
ALTER TABLE crop ADD COLUMN description TEXT;