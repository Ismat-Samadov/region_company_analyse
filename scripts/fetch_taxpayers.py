import json
import logging
import os
import random
import signal
import sys
import time
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
LOG_DIR = os.path.join(BASE_DIR, "logs")

REGIONS_CSV = os.path.join(DATA_DIR, "regions.csv")
OUTPUT_CSV = os.path.join(DATA_DIR, "taxpayers_all_regions.csv")
OUTPUT_SUMMARY_CSV = os.path.join(DATA_DIR, "taxpayers_all_regions_summary.csv")
OUTPUT_JSONL = os.path.join(DATA_DIR, "taxpayers_all_regions.jsonl")
PROGRESS_PATH = os.path.join(DATA_DIR, "taxpayers_progress.json")

ENDPOINT = "https://new.e-taxes.gov.az/api/po/authless/public/v1/authless/findTaxpayer"

REQUEST_TIMEOUT = (10, 60)
SLEEP_MIN = 0.4
SLEEP_MAX = 0.9


class StopRequested(Exception):
    pass


def setup_logging() -> logging.Logger:
    os.makedirs(LOG_DIR, exist_ok=True)
    logger = logging.getLogger("taxpayer_fetch")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_path = os.path.join(
        LOG_DIR, f"taxpayer_fetch_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    )
    file_handler = RotatingFileHandler(file_path, maxBytes=2_000_000, backupCount=5)
    file_handler.setFormatter(fmt)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(fmt)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger


def build_session() -> requests.Session:
    session = requests.Session()
    retries = Retry(
        total=5,
        backoff_factor=1.0,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["POST"],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def safe_write_json(path: str, payload: dict) -> None:
    tmp_path = f"{path}.tmp"
    with open(tmp_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
    os.replace(tmp_path, path)


def load_progress() -> dict:
    if not os.path.exists(PROGRESS_PATH):
        return {
            "started_at": datetime.now(timezone.utc).isoformat(),
            "processed_regions": [],
            "last_region": None,
        }
    with open(PROGRESS_PATH, "r", encoding="utf-8") as handle:
        return json.load(handle)


def load_existing_rows() -> list:
    if not os.path.exists(OUTPUT_JSONL):
        return []
    rows = []
    with open(OUTPUT_JSONL, "r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def append_rows(rows: list) -> None:
    if not rows:
        return
    with open(OUTPUT_JSONL, "a", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def extract_field(dct: dict, path: list, default=None):
    current = dct
    for key in path:
        if not isinstance(current, dict):
            return default
        current = current.get(key)
    return default if current is None else current


def flatten_taxpayer(region: str, item: dict) -> dict:
    legal_status = item.get("legalTaxpayerStatus") or {}
    tax_authority = item.get("taxAuthority") or {}
    legal_form = legal_status.get("legalForm") or {}
    taxpayer_status = legal_status.get("taxpayerStatus") or {}

    return {
        "region": region,
        "name": item.get("name"),
        "tin": item.get("tin"),
        "type": item.get("type"),
        "active": item.get("active"),
        "vatPayer": item.get("vatPayer"),
        "riskyPayer": item.get("riskyPayer"),
        "debt": item.get("debt"),
        "sanctions_json": json.dumps(item.get("sanctions") or [], ensure_ascii=False),
        "taxOrganizationName": item.get("taxOrganizationName"),
        "organizationType": item.get("organizationType"),
        "taxAuthority_code": tax_authority.get("code"),
        "taxAuthority_name_az": extract_field(tax_authority, ["name", "az"]),
        "taxAuthority_name_ru": extract_field(tax_authority, ["name", "ru"]),
        "taxAuthority_name_en": extract_field(tax_authority, ["name", "en"]),
        "legalStatus_name": legal_status.get("name"),
        "legalAddress": legal_status.get("legalAddress"),
        "legitimate": legal_status.get("legitimate"),
        "legalForm_code": legal_form.get("code"),
        "legalForm_name_az": extract_field(legal_form, ["name", "az"]),
        "legalForm_name_ru": extract_field(legal_form, ["name", "ru"]),
        "legalForm_name_en": extract_field(legal_form, ["name", "en"]),
        "charterCapital": legal_status.get("charterCapital"),
        "financialYearStart": legal_status.get("financialYearStart"),
        "financialYearEnd": legal_status.get("financialYearEnd"),
        "voenRegisteredAt": legal_status.get("voenRegisteredAt"),
        "stateRegisteredAt": legal_status.get("stateRegisteredAt"),
        "extractDate": legal_status.get("extractDate"),
        "taxpayerStatus_code": taxpayer_status.get("code"),
        "taxpayerStatus_name_az": extract_field(taxpayer_status, ["name", "az"]),
        "taxpayerStatus_name_ru": extract_field(taxpayer_status, ["name", "ru"]),
        "taxpayerStatus_name_en": extract_field(taxpayer_status, ["name", "en"]),
        "legalStatus_riskyTaxpayer": legal_status.get("riskyTaxpayer"),
        "legalStatus_debt": legal_status.get("debt"),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }



def load_regions() -> list:
    if not os.path.exists(REGIONS_CSV):
        raise FileNotFoundError(f"Regions file not found: {REGIONS_CSV}")
    df = pd.read_csv(REGIONS_CSV)
    if "region" not in df.columns:
        raise ValueError(f"Expected 'region' column in {REGIONS_CSV}")
    regions = []
    seen = set()
    for value in df["region"].tolist():
        region = str(value).strip().upper()
        if not region or region in seen:
            continue
        seen.add(region)
        regions.append(region)
    return regions


def build_payload(region: str) -> dict:
    return {
        "middleName": None,
        "type": "legalEntity",
        "name": f"%{region}%",
    }


def fetch_region(session: requests.Session, region: str, logger: logging.Logger) -> list:
    payload = build_payload(region)
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0",
    }
    response = session.post(
        ENDPOINT,
        json=payload,
        headers=headers,
        timeout=REQUEST_TIMEOUT,
    )
    if response.status_code != 200:
        logger.warning(
            "Non-200 response for region=%s status=%s body=%s",
            region,
            response.status_code,
            response.text[:500],
        )
        return []
    try:
        data = response.json()
    except json.JSONDecodeError:
        logger.error("Invalid JSON response for region=%s", region)
        return []
    taxpayers = data.get("taxpayers") or []
    rows = [flatten_taxpayer(region, item) for item in taxpayers]
    return rows


def write_csv(all_rows: list, summary_rows: list, logger: logging.Logger) -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    tmp_taxpayers = f"{OUTPUT_CSV}.tmp"
    tmp_summary = f"{OUTPUT_SUMMARY_CSV}.tmp"
    pd.DataFrame(all_rows).to_csv(tmp_taxpayers, index=False)
    pd.DataFrame(summary_rows).to_csv(tmp_summary, index=False)
    os.replace(tmp_taxpayers, OUTPUT_CSV)
    os.replace(tmp_summary, OUTPUT_SUMMARY_CSV)
    logger.info("Wrote output to %s and %s", OUTPUT_CSV, OUTPUT_SUMMARY_CSV)


def main() -> int:
    logger = setup_logging()
    logger.info("Starting taxpayer fetch")

    stop_flag = {"stop": False}

    def handle_stop(signum, frame):
        stop_flag["stop"] = True

    signal.signal(signal.SIGINT, handle_stop)
    try:
        signal.signal(signal.SIGTERM, handle_stop)
    except AttributeError:
        pass

    regions = load_regions()
    progress = load_progress()
    processed = set(progress.get("processed_regions", []))

    existing_rows = load_existing_rows()
    logger.info("Loaded %s existing rows", len(existing_rows))

    session = build_session()
    for idx, region in enumerate(regions, start=1):
        if stop_flag["stop"]:
            raise StopRequested()
        if region in processed:
            logger.info("Skipping already processed region=%s", region)
            continue
        logger.info("Processing region %s/%s: %s", idx, len(regions), region)
        try:
            rows = fetch_region(session, region, logger)
        except requests.RequestException as exc:
            logger.error("Request failed for region=%s error=%s", region, exc)
            rows = []
        append_rows(rows)

        processed.add(region)
        progress["processed_regions"] = sorted(processed)
        progress["last_region"] = region
        safe_write_json(PROGRESS_PATH, progress)

        time.sleep(random.uniform(SLEEP_MIN, SLEEP_MAX))

    all_rows = load_existing_rows()
    if all_rows:
        counts = (
            pd.DataFrame(all_rows)
            .groupby("region", dropna=False)
            .size()
            .to_dict()
        )
    else:
        counts = {}
    summary_rows = [{"region": region, "count": counts.get(region, 0)} for region in regions]
    write_csv(all_rows, summary_rows, logger)
    logger.info("Completed successfully")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except StopRequested:
        print("Stop requested. Progress saved.")
        raise SystemExit(1)
    except KeyboardInterrupt:
        print("Interrupted. Progress saved.")
        raise SystemExit(1)
