"""Build one table of every registered version of every trial on the watchlist.

ClinicalTrials.gov keeps each past version of a trial record ("Record History").
This script saves the key fields of every version to history/versions.csv:
one row = one trial at one version. Comparing a row with the row before it
shows what changed; that comparison is done in SQL (sql/detect_changes.sql),
not here.

Versions never change once posted, so rows already in the CSV are kept and
only new versions are downloaded.

Only uses the Python standard library. Run: python fetch_history.py
"""

import csv
import json
import pathlib
import time
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent
OUT = ROOT / "history" / "versions.csv"
LIST_API = "https://clinicaltrials.gov/api/int/studies/{nct}/history"
VERSION_API = "https://clinicaltrials.gov/api/int/studies/{nct}/history/{version}"
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


def to_row(item, change, record):
    p = get(record, "study", "protocolSection") or {}
    s = p.get("statusModule") or {}
    api_version = change["version"]          # the API counts from 0
    web_version = api_version + 1            # the website counts from 1
    return {
        "nct": item["nct"],
        "company": item["company"],
        "label": item["label"],
        "version": web_version,
        "version_date": change.get("date"),
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
        "modules_changed": "; ".join(change.get("moduleLabels") or []),
        "compare_url": COMPARE_URL.format(nct=item["nct"], a=web_version - 1, b=web_version)
        if web_version > 1 else "",
    }


def load_existing():
    if not OUT.exists():
        return {}
    with OUT.open(encoding="utf-8", newline="") as f:
        return {(r["nct"], int(r["version"])): r for r in csv.DictReader(f)}


def main(fetch=fetch_json, pause=0.3):
    config = json.loads((ROOT / "watchlist_config.json").read_text(encoding="utf-8"))
    rows = load_existing()
    new = 0
    for item in config["trials"]:
        nct = item["nct"]
        try:
            changes = fetch(LIST_API.format(nct=nct))["changes"]
        except Exception as e:  # keep going if one trial fails
            print("error", nct, e)
            continue
        for change in changes:
            key = (nct, change["version"] + 1)
            if key in rows:
                continue
            try:
                record = fetch(VERSION_API.format(nct=nct, version=change["version"]))
                rows[key] = to_row(item, change, record)
                new += 1
            except Exception as e:
                print("error", nct, "version", key[1], e)
            time.sleep(pause)
        print("ok   ", nct, len(changes), "versions")

    watched = {t["nct"] for t in config["trials"]}
    ordered = [rows[k] for k in sorted(rows) if k[0] in watched]
    OUT.parent.mkdir(exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(ordered)
    print(f"{len(ordered)} rows in {OUT.name} ({new} new)")


if __name__ == "__main__":
    main()
