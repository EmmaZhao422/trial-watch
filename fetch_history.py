"""Keep one table of every registered version of every trial on the watchlist.

history/versions.csv: one row = one trial at one version. Comparing a row with
the row before it shows what changed; that comparison is done in SQL
(sql/detect_changes.sql), not here.

Where the rows come from:
- Past versions were loaded once, on 2026-11-16, from the Record History pages
  of ClinicalTrials.gov (that data is not offered by the public API).
- From then on this script asks the public API (v2) for each trial's current
  record every day. If its "last update submitted" date is newer than the
  newest row in the table, the current record is added as the next version.

Known limits: two versions submitted between two daily runs are saved as one;
a trial added to the watchlist later starts with no past versions.

Only uses the Python standard library. Run: python fetch_history.py
"""

import csv
import json
import pathlib
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent
OUT = ROOT / "history" / "versions.csv"
API = "https://clinicaltrials.gov/api/v2/studies/{nct}"
COMPARE_URL = "https://clinicaltrials.gov/study/{nct}?tab=history&a={a}&b={b}#version-content-panel"

COLUMNS = [
    "nct", "company", "label",
    "version",              # version number as shown on the website (starts at 1)
    "version_date",         # date this version was submitted
    "overall_status",
    "enrollment", "enrollment_type",
    "primary_completion_date", "primary_completion_type",
    "study_completion_date", "study_completion_type",
    "start_date",
    "n_locations", "n_primary_outcomes", "n_secondary_outcomes",
    "modules_changed",      # sections the registry itself flags as edited
    "compare_url",          # website page comparing this version with the one before
]


def get(d, *keys):
    for k in keys:
        if not isinstance(d, dict):
            return None
        d = d.get(k)
    return d


def fetch_json(url):
    req = urllib.request.Request(
        url, headers={"Accept": "application/json", "User-Agent": "trial-watch-alpha/0.2"}
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def to_row(item, version, record):
    p = record.get("protocolSection") or {}
    s = p.get("statusModule") or {}
    return {
        "nct": item["nct"],
        "company": item["company"],
        "label": item["label"],
        "version": version,
        "version_date": s.get("lastUpdateSubmitDate"),
        "overall_status": s.get("overallStatus"),
        "enrollment": get(p, "designModule", "enrollmentInfo", "count"),
        "enrollment_type": get(p, "designModule", "enrollmentInfo", "type"),
        "primary_completion_date": get(s, "primaryCompletionDateStruct", "date"),
        "primary_completion_type": get(s, "primaryCompletionDateStruct", "type"),
        "study_completion_date": get(s, "completionDateStruct", "date"),
        "study_completion_type": get(s, "completionDateStruct", "type"),
        "start_date": get(s, "startDateStruct", "date"),
        "n_locations": len(get(p, "contactsLocationsModule", "locations") or []),
        "n_primary_outcomes": len(get(p, "outcomesModule", "primaryOutcomes") or []),
        "n_secondary_outcomes": len(get(p, "outcomesModule", "secondaryOutcomes") or []),
        "modules_changed": "",
        "compare_url": COMPARE_URL.format(nct=item["nct"], a=version - 1, b=version)
        if version > 1 else "",
    }


def load_existing():
    if not OUT.exists():
        return {}
    with OUT.open(encoding="utf-8", newline="") as f:
        return {(r["nct"], int(r["version"])): r for r in csv.DictReader(f)}


def main(fetch=fetch_json):
    config = json.loads((ROOT / "watchlist_config.json").read_text(encoding="utf-8"))
    rows = load_existing()
    new = 0
    for item in config["trials"]:
        nct = item["nct"]
        known = [r for (n, _), r in rows.items() if n == nct]
        latest = max(known, key=lambda r: int(r["version"])) if known else None
        try:
            record = fetch(API.format(nct=nct))
        except Exception as e:  # keep going if one trial fails
            print("error", nct, e)
            continue
        submitted = get(record, "protocolSection", "statusModule", "lastUpdateSubmitDate")
        if latest and (not submitted or submitted <= latest["version_date"]):
            print("same ", nct, "still version", latest["version"])
            continue
        version = int(latest["version"]) + 1 if latest else 1
        rows[(nct, version)] = to_row(item, version, record)
        new += 1
        print("new  ", nct, "version", version, submitted)

    watched = {t["nct"] for t in config["trials"]}
    ordered = [rows[k] for k in sorted(rows) if k[0] in watched]
    OUT.parent.mkdir(exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS, lineterminator="\n")
        w.writeheader()
        w.writerows(ordered)
    print(f"{len(ordered)} rows in {OUT.name} ({new} new)")


if __name__ == "__main__":
    main()
