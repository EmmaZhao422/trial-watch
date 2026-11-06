# Trial Watch · Competitor Clinical Trial Intelligence Agent (Alpha)

Live site: https://emmazhao422.github.io/trial-watch/

A portfolio project by Emma Zhao (Duke University). Pharma competitive-intelligence teams track changes in competitors' clinical trials (status, enrollment, dates, endpoints). Spotting a change is easy; explaining *why* it happened and what it means still takes manual digging. Trial Watch pairs a daily-refreshed watchlist with an AI Agent that investigates each change in public sources and writes a four-part brief: **What happened / What sources say / What is still unclear / Analyst view**. Every fact is linked, inferences are labeled, and "Evidence insufficient" is an accepted answer.

## Status (alpha)

- Watchlist of 8 obesity / weight-loss trials (Lilly, Novo Nordisk, Amgen, AstraZeneca), refreshed daily from the ClinicalTrials.gov API by GitHub Actions, with a saved snapshot per day.
- 3 real registry changes used as development cases; the Agent (ChatGPT with web search + instruction v0) has produced 3 briefs.
- Agent output is **not yet human-verified**; claim-by-claim review, a human baseline brief, and an improved instruction (v1) are next. No accuracy figure is claimed.

## Files

| File | Purpose |
|---|---|
| `index.html` | The website (one page that reads the data files below) |
| `briefs.json` | Agent-generated briefs (text kept exactly as generated) |
| `watchlist_config.json` | Which trials to track. Add or remove trials here only |
| `watchlist.json` | Latest trial data shown on the site (written by the daily job) |
| `snapshots/` | One snapshot per day; input for SQL-based change detection later |
| `update_watchlist.py` | Pulls data from the ClinicalTrials.gov API (Python standard library only) |
| `.github/workflows/update-and-deploy.yml` | Daily data refresh + site deploy; also deploys on every push |

## How to update

- **Mark a brief as verified:** in `briefs.json`, change that change's `"verification"` from `"unverified"` to `"verified"` after checking every claim.
- **Change the watchlist:** edit `watchlist_config.json`; the next run picks it up.
- **Refresh now:** Actions → "Update watchlist and deploy" → Run workflow.

## Rules for editing

- Do not rewrite, polish or add to the Agent's text in `briefs.json`.
- Do not describe features or results that do not exist yet (e.g. an accuracy rate, or one-click Agent runs).
- No API keys, passwords or personal contact details in this repository.

## Credits

Research design, case selection and fact-checking: Emma Zhao. Instruction v0, watchlist candidates and site code were drafted with AI assistance (Claude / ChatGPT). Agent runs use ChatGPT with web search. ClinicalTrials.gov records are the source of truth for all trial information.
