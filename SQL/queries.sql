-- FitTrack queries. Each one starts with a "-- name:" line.
-- Words like :email are parameters: DBeaver asks for their values when you
-- run the query, and the Python runner fills them from name=value arguments.

-- name: list_clients
SELECT id, name, email, join_date
FROM clients
ORDER BY id;

-- name: add_client
INSERT INTO clients (name, email, join_date)
VALUES (:name, :email, :join_date);

-- name: log_session
INSERT INTO sessions (client_id, session_date, duration_minutes, notes)
VALUES (:client_id, :session_date, :duration_minutes, :notes);

-- name: update_client_email
UPDATE clients
SET email = :email
WHERE id = :client_id;

-- name: delete_client
-- Children first: exercises of the client's sessions, then the sessions,
-- then the client. In the opposite order the foreign keys would block it.
DELETE FROM session_exercises
WHERE session_id IN (SELECT id FROM sessions WHERE client_id = :client_id);
DELETE FROM sessions
WHERE client_id = :client_id;
DELETE FROM clients
WHERE id = :client_id;

-- name: sessions_with_client_names
SELECT s.id AS session_id, c.name AS client, s.session_date,
       s.duration_minutes, s.notes
FROM sessions s
INNER JOIN clients c ON c.id = s.client_id
ORDER BY s.session_date, s.id;

-- name: sessions_per_client
SELECT c.name AS client, COUNT(s.id) AS total_sessions
FROM clients c
INNER JOIN sessions s ON s.client_id = c.id
GROUP BY c.id, c.name
ORDER BY c.name;

-- name: calories_per_client
SELECT c.name AS client,
       SUM(se.minutes * e.calories_per_minute) AS total_calories
FROM clients c
INNER JOIN sessions s ON s.client_id = c.id
INNER JOIN session_exercises se ON se.session_id = s.id
INNER JOIN exercises e ON e.id = se.exercise_id
GROUP BY c.id, c.name
ORDER BY total_calories DESC;

-- name: summary_report
-- LEFT JOINs keep clients with no sessions (and sessions with no exercises).
-- COUNT(DISTINCT s.id) because a session appears once per exercise row.
SELECT c.name AS client,
       COUNT(DISTINCT s.id) AS total_sessions,
       COALESCE(SUM(se.minutes * e.calories_per_minute), 0.0) AS total_calories
FROM clients c
LEFT JOIN sessions s ON s.client_id = c.id
LEFT JOIN session_exercises se ON se.session_id = s.id
LEFT JOIN exercises e ON e.id = se.exercise_id
GROUP BY c.id, c.name
ORDER BY total_calories DESC, c.name;