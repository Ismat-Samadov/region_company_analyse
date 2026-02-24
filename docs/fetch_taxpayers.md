# fetch_taxpayers.py

## Purpose
Fetches taxpayer data per region from the public endpoint and stores results locally. The script is resumable and tracks progress between runs.

## Requirements
Install dependencies from `scripts/requirements.txt`:

```bash
pip install -r scripts/requirements.txt
```

## Inputs
- `data/regions.csv`
  - CSV with a single header: `region`
  - Values must be uppercase region names (one per line).

## Outputs
- `data/taxpayers_all_regions.jsonl`
  - Append-only JSONL file with raw fetched rows.
- `data/taxpayers_all_regions.csv`
  - Final merged CSV of all rows (generated at the end).
- `data/taxpayers_all_regions_summary.csv`
  - Summary counts by region (generated at the end).
- `data/taxpayers_progress.json`
  - Progress file for resuming (ignored by git).
- `logs/`
  - Run logs (ignored by git).

## How It Works
1. Reads regions from `data/regions.csv`.
2. Skips regions already recorded in `data/taxpayers_progress.json`.
3. Fetches data for each region from the endpoint.
4. Appends rows to `data/taxpayers_all_regions.jsonl` as it goes.
5. At the end, writes CSV outputs for the full dataset and summary.

## Run
```bash
python scripts/fetch_taxpayers.py
```

## Notes
- If interrupted, the script saves progress and can resume on the next run.
- The final CSVs are rebuilt at the end from the JSONL file.
