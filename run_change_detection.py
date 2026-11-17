"""Run the change-detection SQL and save its result for the website.

1. Loads history/versions.csv into a temporary SQLite table called "versions".
2. Runs the query in sql/detect_changes.sql (written by Emma).
3. Saves the rows the query returns to changes.json.

If the SQL file has no query yet, nothing is written.
Only uses the Python standard library. Run: python run_change_detection.py
"""

import csv
import json
import pathlib
import sqlite3

ROOT = pathlib.Path(__file__).resolve().parent
CSV = ROOT / "history" / "versions.csv"
SQL = ROOT / "sql" / "detect_changes.sql"
OUT = ROOT / "changes.json"
INTEGER_COLUMNS = {"version", "enrollment", "n_locations", "n_primary_outcomes", "n_secondary_outcomes"}


def load_versions(con):
    with CSV.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        cols = reader.fieldnames
        types = ", ".join(f'"{c}" {"INTEGER" if c in INTEGER_COLUMNS else "TEXT"}' for c in cols)
        con.execute(f"CREATE TABLE versions ({types})")
        marks = ", ".join("?" for _ in cols)
        for r in reader:
            con.execute(
                f"INSERT INTO versions VALUES ({marks})",
                [None if r[c] == "" else r[c] for c in cols],
            )
    return con.execute("SELECT COUNT(*) FROM versions").fetchone()[0]


def read_query():
    if not SQL.exists():
        return ""
    lines = [l for l in SQL.read_text(encoding="utf-8").splitlines() if not l.strip().startswith("--")]
    return "\n".join(lines).strip()


def main():
    query = read_query()
    if not query:
        print("No query in sql/detect_changes.sql yet; nothing to do.")
        return
    con = sqlite3.connect(":memory:")
    con.row_factory = sqlite3.Row
    n = load_versions(con)
    changes = [dict(r) for r in con.execute(query)]
    OUT.write_text(
        json.dumps({"versions_compared": n, "changes": changes}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"{n} version rows -> {len(changes)} changes written to {OUT.name}")


if __name__ == "__main__":
    main()
