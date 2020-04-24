CREATE TABLE IF NOT EXISTS prefixes (
    guild_id INTEGER PRIMARY KEY,
    prefixes PYSET
);
CREATE TABLE IF NOT EXISTS command_uses (
    name TEXT PRIMARY KEY,
    uses INTEGER
);
CREATE TABLE IF NOT EXISTS socket_stats (
    name TEXT PRIMARY KEY,
    amount INTEGER
);
CREATE TABLE IF NOT EXISTS channel_links (
    send_from INTEGER PRIMARY KEY,
    send_to PYSET
);
CREATE TABLE IF NOT EXISTS ratings (
    bot_id INTEGER,
    user_id INTEGER,
    rating INTEGER,
    review TEXT,
    PRIMARY KEY(bot_id, user_id)
);
CREATE TABLE IF NOT EXISTS blacklist (
    user_id INTEGER PRIMARY KEY,
    reason TEXT
);