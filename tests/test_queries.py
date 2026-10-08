import sqlite3
import unittest

import fittrack


class FitTrackTestCase(unittest.TestCase):
    """Every test gets a fresh in-memory database built from the real SQL files."""

    def setUp(self):
        self.conn = fittrack.connect(":memory:")
        fittrack.build_database(self.conn)
        self.queries = fittrack.load_queries()

    def tearDown(self):
        self.conn.close()

    def run_q(self, query_name, **params):
        return fittrack.run_query(self.conn, query_name, params, self.queries)

    def scalar(self, sql, params=()):
        return self.conn.execute(sql, params).fetchone()[0]


class TestSchemaAndSeed(FitTrackTestCase):
    def test_sample_data_is_loaded(self):
        self.assertEqual(self.scalar("SELECT COUNT(*) FROM clients"), 4)
        self.assertEqual(self.scalar("SELECT COUNT(*) FROM sessions"), 8)
        self.assertEqual(self.scalar("SELECT COUNT(*) FROM exercises"), 5)
        self.assertEqual(self.scalar("SELECT COUNT(*) FROM session_exercises"), 13)

    def test_duplicate_email_is_rejected(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.run_q("add_client", name="Copy", email="alice@example.com",
                       join_date="2026-04-01")

    def test_session_for_missing_client_is_rejected(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.run_q("log_session", client_id=99, session_date="2026-04-01",
                       duration_minutes=30, notes="Nobody")

    def test_zero_minute_session_is_rejected(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.run_q("log_session", client_id=1, session_date="2026-04-01",
                       duration_minutes=0, notes="Too short")


class TestQueryFile(FitTrackTestCase):
    def test_all_required_queries_exist(self):
        for name in ("list_clients", "add_client", "log_session",
                     "update_client_email", "delete_client",
                     "sessions_with_client_names", "sessions_per_client",
                     "calories_per_client", "summary_report"):
            self.assertIn(name, self.queries)

    def test_delete_client_has_three_statements(self):
        self.assertEqual(len(self.queries["delete_client"]), 3)

    def test_windows_line_endings_are_handled(self):
        text = "-- name: a\r\nSELECT 1;\r\n-- name: b\r\nSELECT 2;\r\nSELECT 3;\r\n"
        queries = fittrack.load_queries(text)
        self.assertEqual(list(queries), ["a", "b"])
        self.assertEqual(len(queries["b"]), 2)

    def test_missing_semicolon_is_reported(self):
        with self.assertRaises(ValueError):
            fittrack.load_queries("-- name: a\nSELECT 1\n")

    def test_unknown_query_name(self):
        with self.assertRaises(KeyError):
            self.run_q("no_such_query")


class TestMaintenance(FitTrackTestCase):
    def test_add_client_then_list(self):
        _, changed = self.run_q("add_client", name="Eva Lopez",
                                email="eva@example.com", join_date="2026-04-01")
        self.assertEqual(changed, 1)
        columns, rows = self.run_q("list_clients")
        self.assertEqual(columns, ["id", "name", "email", "join_date"])
        self.assertEqual(len(rows), 5)
        self.assertEqual(rows[-1], (5, "Eva Lopez", "eva@example.com", "2026-04-01"))

    def test_log_session_stores_number_from_text(self):
        # The command line passes every value as text, like "40".
        self.run_q("log_session", client_id="4", session_date="2026-04-02",
                   duration_minutes="40", notes="First session")
        row = self.conn.execute(
            "SELECT client_id, duration_minutes, notes FROM sessions "
            "WHERE session_date = '2026-04-02'").fetchone()
        self.assertEqual(row, (4, 40, "First session"))

    def test_update_client_email_changes_only_that_client(self):
        _, changed = self.run_q("update_client_email", client_id=2,
                                email="ben.carter@example.com")
        self.assertEqual(changed, 1)
        emails = dict(self.conn.execute("SELECT id, email FROM clients").fetchall())
        self.assertEqual(emails[2], "ben.carter@example.com")
        self.assertEqual(emails[1], "alice@example.com")

    def test_update_unknown_client_changes_nothing(self):
        _, changed = self.run_q("update_client_email", client_id=99, email="x@example.com")
        self.assertEqual(changed, 0)

    def test_delete_client_removes_sessions_and_their_exercises(self):
        _, changed = self.run_q("delete_client", client_id=1)
        # 5 session_exercises rows + 3 sessions + 1 client
        self.assertEqual(changed, 9)
        self.assertEqual(self.scalar("SELECT COUNT(*) FROM clients WHERE id = 1"), 0)
        self.assertEqual(self.scalar("SELECT COUNT(*) FROM sessions WHERE client_id = 1"), 0)
        self.assertEqual(self.scalar(
            "SELECT COUNT(*) FROM session_exercises WHERE session_id IN (1, 2, 3)"), 0)
        # Other clients are untouched.
        self.assertEqual(self.scalar("SELECT COUNT(*) FROM clients"), 3)
        self.assertEqual(self.scalar("SELECT COUNT(*) FROM sessions"), 5)
        self.assertEqual(self.scalar("SELECT COUNT(*) FROM session_exercises"), 8)

    def test_failed_statement_rolls_back_whole_query(self):
        # Two statements; the second breaks a CHECK, so the first must be undone.
        queries = fittrack.load_queries(
            "-- name: bad\n"
            "UPDATE clients SET email = 'changed@example.com' WHERE id = 1;\n"
            "UPDATE sessions SET duration_minutes = 0 WHERE id = 1;\n")
        with self.assertRaises(sqlite3.IntegrityError):
            fittrack.run_query(self.conn, "bad", {}, queries)
        self.assertEqual(self.scalar("SELECT email FROM clients WHERE id = 1"),
                         "alice@example.com")


class TestReports(FitTrackTestCase):
    def test_sessions_with_client_names(self):
        columns, rows = self.run_q("sessions_with_client_names")
        self.assertEqual(columns[:3], ["session_id", "client", "session_date"])
        self.assertEqual(len(rows), 8)
        self.assertEqual(rows[0][:3], (1, "Alice Johnson", "2026-02-02"))
        self.assertEqual(rows[1][:3], (4, "Ben Carter", "2026-02-03"))
        dates = [r[2] for r in rows]
        self.assertEqual(dates, sorted(dates))

    def test_sessions_per_client(self):
        _, rows = self.run_q("sessions_per_client")
        self.assertEqual(rows, [("Alice Johnson", 3), ("Ben Carter", 2), ("Chloe Diaz", 3)])

    def test_calories_per_client(self):
        _, rows = self.run_q("calories_per_client")
        self.assertEqual(rows, [("Chloe Diaz", 780.0), ("Alice Johnson", 690.0),
                                ("Ben Carter", 295.0)])

    def test_summary_report_counts_each_session_once(self):
        _, rows = self.run_q("summary_report")
        self.assertEqual(rows, [
            ("Chloe Diaz", 3, 780.0),
            ("Alice Johnson", 3, 690.0),
            ("Ben Carter", 2, 295.0),
            ("Dev Patel", 0, 0.0),
        ])

    def test_summary_report_follows_new_data(self):
        self.run_q("log_session", client_id=4, session_date="2026-04-02",
                   duration_minutes=20, notes="Bike test")
        session_id = self.scalar("SELECT MAX(id) FROM sessions")
        self.conn.execute(
            "INSERT INTO session_exercises VALUES (?, 5, 20)", (session_id,))
        _, rows = self.run_q("summary_report")
        self.assertIn(("Dev Patel", 1, 180.0), rows)


if __name__ == "__main__":
    unittest.main()