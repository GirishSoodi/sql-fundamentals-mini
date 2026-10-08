INSERT INTO clients (id, name, email, join_date) VALUES
    (1, 'Alice Johnson', 'alice@example.com', '2026-01-05'),
    (2, 'Ben Carter',    'ben@example.com',   '2026-01-12'),
    (3, 'Chloe Diaz',    'chloe@example.com', '2026-02-01'),
    (4, 'Dev Patel',     'dev@example.com',   '2026-03-15');

INSERT INTO exercises (id, name, muscle_group, calories_per_minute) VALUES
    (1, 'Squat',       'Legs',   8.0),
    (2, 'Bench Press', 'Chest',  6.0),
    (3, 'Rowing',      'Back',  10.0),
    (4, 'Plank',       'Core',   4.0),
    (5, 'Cycling',     'Cardio', 9.0);

INSERT INTO sessions (id, client_id, session_date, duration_minutes, notes) VALUES
    (1, 1, '2026-02-02', 60, 'Baseline strength test'),
    (2, 1, '2026-02-09', 45, 'Focus on squat depth'),
    (3, 1, '2026-02-16', 50, 'Added rowing intervals'),
    (4, 2, '2026-02-03', 30, 'Intro session'),
    (5, 2, '2026-02-10', 40, 'Upper body'),
    (6, 3, '2026-02-05', 55, 'Cardio endurance'),
    (7, 3, '2026-02-12', 60, 'Mixed circuit'),
    (8, 3, '2026-02-19', 35, 'Stretching only');

INSERT INTO session_exercises (session_id, exercise_id, minutes) VALUES
    (1, 1, 20),
    (1, 2, 15),
    (2, 1, 25),
    (2, 4, 10),
    (3, 3, 20),
    (4, 5, 15),
    (4, 4, 10),
    (5, 2, 20),
    (6, 5, 30),
    (6, 3, 15),
    (7, 1, 15),
    (7, 2, 15),
    (7, 3, 15);