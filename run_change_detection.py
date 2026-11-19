"""Run the change-detection SQL and save its result for the website.

1. Loads history/versions.csv into a temporary SQLite table called "versions".
2. Runs the query in sql/detect_changes.sql.
3. Saves the rows the query returns to changes.json.
4. Writes the same changes as a feed (feed.xml) that a feed reader can follow.

If the SQL file has no query yet, nothing is written.
Only uses the Python standard library. Run: python run_change_detection.py
"""

import csv
import json
import pathlib
import sqlite3
from xml.sax.saxutils import escape

ROOT = pathlib.Path(__file__).resolve().parent
CSV = ROOT / "history" / "versions.csv"
SQL = ROOT / "sql" / "detect_changes.sql"
OUT = ROOT / "changes.json"
FEED = ROOT / "feed.xml"
SITE = "https://emmazhao422.github.io/trial-watch/"
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


def write_feed(changes):
    """Atom feed: one entry per change, newest first (the query already sorts them)."""
    entries = []
    for c in changes[:50]:
        title = f"{c['company']} · {c['label']}: {c['field']} {c['old_value']} -> {c['new_value']}"
        entries.append(
            "  <entry>\n"
            f"    <id>{SITE}#{c['nct']}-v{c['version']}-{c['field']}</id>\n"
            f"    <title>{escape(title)}</title>\n"
            f"    <updated>{c['version_date']}T00:00:00Z</updated>\n"
            f"    <link href=\"{escape(c['compare_url'] or SITE)}\"/>\n"
            f"    <summary>{escape(c['nct'])}, record version {c['version']}, submitted {c['version_date']}.</summary>\n"
            "  </entry>"
        )
    updated = changes[0]["version_date"] if changes else "1970-01-01"
    FEED.write_text(
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<feed xmlns="http://www.w3.org/2005/Atom">\n'
        "  <title>Trial Watch: detected registry changes</title>\n"
        f"  <id>{SITE}feed.xml</id>\n"
        f"  <link href=\"{SITE}\"/>\n"
        f"  <link rel=\"self\" href=\"{SITE}feed.xml\"/>\n"
        f"  <updated>{updated}T00:00:00Z</updated>\n"
        "  <author><name>Trial Watch</name></author>\n"
        + "\n".join(entries) + "\n</feed>\n",
        encoding="utf-8",
    )


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
    write_feed(changes)
    print(f"{n} version rows -> {len(changes)} changes written to {OUT.name} and {FEED.name}")


if __name__ == "__main__":
    main()
