CREATE TABLE IF NOT EXISTS blacklist (
    userid BIGINT PRIMARY KEY,
    reason TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS prefixes (
    guild_id BIGINT,
    prefixes VARCHAR(1999)[]
);