CREATE TABLE clients (
    id        INTEGER PRIMARY KEY,
    name      TEXT NOT NULL,
    email     TEXT NOT NULL UNIQUE,
    join_date TEXT NOT NULL
);

CREATE TABLE sessions (
    id               INTEGER PRIMARY KEY,
    client_id        INTEGER NOT NULL REFERENCES clients (id),
    session_date     TEXT NOT NULL,
    duration_minutes INTEGER NOT NULL CHECK (duration_minutes > 0),
    notes            TEXT
);

CREATE TABLE exercises (
    id                  INTEGER PRIMARY KEY,
    name                TEXT NOT NULL UNIQUE,
    muscle_group        TEXT NOT NULL,
    calories_per_minute REAL NOT NULL CHECK (calories_per_minute >= 0)
);

CREATE TABLE session_exercises (
    session_id  INTEGER NOT NULL REFERENCES sessions (id),
    exercise_id INTEGER NOT NULL REFERENCES exercises (id),
    minutes     INTEGER NOT NULL CHECK (minutes > 0),
    PRIMARY KEY (session_id, exercise_id)
);