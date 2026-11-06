"""Fetch the latest ClinicalTrials.gov record for every trial on the watchlist.

Writes:
  watchlist.json             -> what the website shows
  snapshots/YYYY-MM-DD.json  -> one snapshot per day (raw material for the
                                     SQL change detection Emma writes later)

Only uses the Python standard library. Run: python update_watchlist.py
"""

import datetime
import json
import pathlib
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent
DATA = ROOT
API = "https://clinicaltrials.gov/api/v2/studies/{nct}"


def get(d, *keys):
    """Safely walk nested dictionaries: get(record, "a", "b") -> record["a"]["b"] or None."""
    for k in keys:
        if not isinstance(d, dict):
            return None
        d = d.get(k)
    return d


def fetch(nct):
    req = urllib.request.Request(
        API.format(nct=nct),
        headers={"Accept": "application/json", "User-Agent": "trial-watch-alpha/0.1"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def summarize(item, record):
    p = record.get("protocolSection", {})
    phases = get(p, "designModule", "phases") or []
    return {
        "nct": item["nct"],
        "company": item["company"],
        "label": item["label"],
        "title": get(p, "identificationModule", "briefTitle"),
        "acronym": get(p, "identificationModule", "acronym"),
        "sponsor": get(p, "sponsorCollaboratorsModule", "leadSponsor", "name"),
        "phase": "/".join(phases),
        "overall_status": get(p, "statusModule", "overallStatus"),
        "enrollment": get(p, "designModule", "enrollmentInfo", "count"),
        "enrollment_type": get(p, "designModule", "enrollmentInfo", "type"),
        "primary_completion": get(p, "statusModule", "primaryCompletionDateStruct", "date"),
        "primary_completion_type": get(p, "statusModule", "primaryCompletionDateStruct", "type"),
        "study_completion": get(p, "statusModule", "completionDateStruct", "date"),
        "last_update_posted": get(p, "statusModule", "lastUpdatePostDateStruct", "date"),
    }


def main():
    config = json.loads((DATA / "watchlist_config.json").read_text(encoding="utf-8"))
    now = datetime.datetime.now(datetime.timezone.utc)
    rows = []
    for item in config["trials"]:
        try:
            rows.append(summarize(item, fetch(item["nct"])))
            print("ok   ", item["nct"])
        except Exception as e:  # keep going if one trial fails
            rows.append({**item, "error": str(e)})
            print("error", item["nct"], e)

    out = {
        "fetched_at": now.isoformat(timespec="seconds"),
        "source_note": "Updated automatically every day from the ClinicalTrials.gov API v2 by GitHub Actions.",
        "trials": rows,
    }
    text = json.dumps(out, ensure_ascii=False, indent=2)
    (DATA / "watchlist.json").write_text(text, encoding="utf-8")
    snap_dir = DATA / "snapshots"
    snap_dir.mkdir(exist_ok=True)
    (snap_dir / f"{now.date().isoformat()}.json").write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
