import os
import sqlite3
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SQL_DIR = os.path.join(BASE_DIR, "sql")
DB_PATH = os.path.join(BASE_DIR, "fittrack.db")
NAME_MARKER = "-- name:"
PROG = "python " + os.path.basename(__file__)
USAGE = (
    "Usage:\n"
    "    " + PROG + " build\n"
    "    " + PROG + " list\n"
    "    " + PROG + " run QUERY_NAME [key=value ...]"
)


def read_sql(filename):
    # utf-8-sig also accepts a file saved with a byte order mark.
    with open(os.path.join(SQL_DIR, filename), encoding="utf-8-sig") as f:
        return f.read()


def connect(path):
    conn = sqlite3.connect(path)
    # SQLite only enforces REFERENCES when this is switched on, per connection.
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def build_database(conn):
    conn.executescript(read_sql("schema.sql"))
    conn.executescript(read_sql("seed.sql"))
    conn.commit()


def split_statements(text):
    statements = []
    current = ""
    for line in text.splitlines(keepends=True):
        current += line
        if sqlite3.complete_statement(current):
            statements.append(current.strip())
            current = ""
    leftover = [
        line for line in current.splitlines()
        if line.strip() and not line.strip().startswith("--")
    ]
    if leftover:
        raise ValueError("Statement without a closing semicolon: " + current.strip())
    return statements


def load_queries(text=None):
    if text is None:
        text = read_sql("queries.sql")
    queries = {}
    name = None
    body = []
    for line in text.splitlines():
        if line.strip().startswith(NAME_MARKER):
            if name:
                queries[name] = split_statements("\n".join(body))
            name = line.strip()[len(NAME_MARKER):].strip()
            if name in queries:
                raise ValueError("Duplicate query name: " + name)
            body = []
        elif name:
            body.append(line)
    if name:
        queries[name] = split_statements("\n".join(body))
    return queries


def run_query(conn, name, params=None, queries=None):
    """Run every statement of one named query.

    Returns (columns, rows) for a SELECT, or (None, changed_row_count) otherwise.
    """
    if queries is None:
        queries = load_queries()
    if name not in queries:
        raise KeyError("Unknown query: " + name)
    params = params or {}
    before = conn.total_changes
    cursor = None
    try:
        for statement in queries[name]:
            cursor = conn.execute(statement, params)
        if cursor is not None and cursor.description:
            columns = [d[0] for d in cursor.description]
            return columns, cursor.fetchall()
        conn.commit()
    except Exception:
        # A half-finished delete must not leave orphaned or missing rows.
        conn.rollback()
        raise
    return None, conn.total_changes - before


def format_table(columns, rows):
    text = [["" if v is None else str(v) for v in row] for row in rows]
    widths = [len(c) for c in columns]
    for row in text:
        widths = [max(w, len(v)) for w, v in zip(widths, row)]
    lines = ["  ".join(c.ljust(w) for c, w in zip(columns, widths)).rstrip()]
    lines.append("  ".join("-" * w for w in widths))
    for row in text:
        lines.append("  ".join(v.ljust(w) for v, w in zip(row, widths)).rstrip())
    return "\n".join(lines)


def parse_params(args):
    params = {}
    for arg in args:
        if "=" not in arg:
            raise ValueError("Expected key=value, got: " + arg)
        key, value = arg.split("=", 1)
        params[key] = value
    return params


def count_rows(conn, table):
    return conn.execute("SELECT COUNT(*) FROM " + table).fetchone()[0]


def main(argv):
    if not argv or argv[0] not in ("build", "list", "run"):
        print(USAGE)
        return 1
    command = argv[0]
    try:
        if command == "build":
            if os.path.exists(DB_PATH):
                os.remove(DB_PATH)
            conn = connect(DB_PATH)
            build_database(conn)
            counts = [
                str(count_rows(conn, t)) + " " + t
                for t in ("clients", "sessions", "exercises", "session_exercises")
            ]
            conn.close()
            print("Created fittrack.db with " + ", ".join(counts))
        elif command == "list":
            for name in load_queries():
                print(name)
        else:
            if len(argv) < 2:
                print("Error: give a query name, e.g. " + PROG + " run list_clients")
                return 1
            if not os.path.exists(DB_PATH):
                print("Error: fittrack.db not found. Run: " + PROG + " build")
                return 1
            conn = connect(DB_PATH)
            try:
                columns, result = run_query(conn, argv[1], parse_params(argv[2:]))
            finally:
                conn.close()
            if columns is None:
                print(str(result) + " row(s) changed")
            else:
                print(format_table(columns, result))
                print("(" + str(len(result)) + " rows)")
    except PermissionError:
        print("Error: fittrack.db is in use. Disconnect it in DBeaver and try again.")
        return 1
    except (sqlite3.Error, KeyError, ValueError) as e:
        message = e.args[0] if e.args else str(e)
        print("Error: " + str(message))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))