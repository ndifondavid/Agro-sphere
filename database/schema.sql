PRAGMA foreign_keys = ON;

CREATE TABLE user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL
);

CREATE TABLE farm (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id INTEGER NOT NULL REFERENCES user(id),
    name TEXT NOT NULL,
    location TEXT NOT NULL,
    image_path TEXT
);

CREATE TABLE crop (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    farm_id INTEGER NOT NULL REFERENCES farm(id),
    crop_type TEXT NOT NULL,
    planting_date DATE,
    image_path TEXT
);

CREATE TABLE scan (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    crop_id INTEGER NOT NULL REFERENCES crop(id),
    image_path TEXT NOT NULL,
    predicted_disease TEXT NOT NULL,
    confidence_score FLOAT NOT NULL,
    recommendation TEXT,
    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE listing (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    farmer_id INTEGER NOT NULL REFERENCES user(id),
    crop_type TEXT NOT NULL,
    harvest_date DATE NOT NULL,
    quantity FLOAT NOT NULL,
    price FLOAT NOT NULL,
    availability_status TEXT NOT NULL DEFAULT 'available',
    image_path TEXT
);

CREATE TABLE reservation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    listing_id INTEGER NOT NULL REFERENCES listing(id),
    buyer_id INTEGER NOT NULL REFERENCES user(id),
    status TEXT NOT NULL DEFAULT 'requested',
    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE message (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender_id INTEGER NOT NULL REFERENCES user(id),
    receiver_id INTEGER NOT NULL REFERENCES user(id),
    listing_id INTEGER NOT NULL REFERENCES listing(id),
    content TEXT NOT NULL,
    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX ix_farm_owner_id ON farm(owner_id);
CREATE INDEX ix_crop_farm_id ON crop(farm_id);
CREATE INDEX ix_scan_crop_id ON scan(crop_id);
CREATE INDEX ix_listing_availability_status ON listing(availability_status);
CREATE INDEX ix_message_listing_id ON message(listing_id);
