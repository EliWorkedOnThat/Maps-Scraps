CREATE TABLE IF NOT EXISTS coldcalls (
    id            SERIAL PRIMARY KEY,
    name          TEXT,
    url           TEXT UNIQUE,
    rating        NUMERIC(3,1),
    review_count  INTEGER,
    category      TEXT,
    address       TEXT,
    phone         TEXT
);