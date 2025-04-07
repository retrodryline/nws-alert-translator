CREATE TABLE IF NOT EXISTS alerts (
    id TEXT PRIMARY KEY,
    source TEXT,
    headline TEXT,
    area TEXT,
    severity TEXT,
    effective TEXT,
    expires TEXT,
    raw_json TEXT,
    translated_headline TEXT,
    translated_description TEXT,
    translated_json TEXT
);