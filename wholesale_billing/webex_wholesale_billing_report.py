#!/usr/bin/env python3
"""
Webex Wholesale Billing Report Automation (Previous Month)
----------------------------------------------------------

This script automates the retrieval and processing of Webex Wholesale
Billing reports for the previous month's billing cycle.

It supports MSP/Partner workflows by:

1. Automatically determining the previous billing month
2. Ensuring a billing report exists (create → poll → download)
3. Downloading the CSV using Webex's temporary download URL
4. Applying a post-processing transformation similar to an internal
   operations workflow ("Ben's script"):
     - Drop first 4 columns
     - Extract usage from Column K
     - Compute BILLABLE_UNITS = ceil(ColumnK / days_in_last_month)
     - Append BILLABLE_UNITS as a final CSV column

5. Producing:
     <Month>-<Year>-Wholesale-Usage_<ts>_ORIGINAL.csv
     <Month>-<Year>-Wholesale-Usage_<ts>.csv

The script uses OAuth Refresh Tokens; CLIENT_ID, CLIENT_SECRET,
ACCESS_TOKEN, and REFRESH_TOKEN are supplied via environment variables
to keep credentials out of the source code.

---------------------------------------------------------------------------
Environment Variables Required:
    export WEBEX_CLIENT_ID="xxxx"
    export WEBEX_CLIENT_SECRET="xxxx"
    export WEBEX_ACCESS_TOKEN="xxxx"
    export WEBEX_REFRESH_TOKEN="xxxx"

Dependencies:
    pip install pandas numpy requests
"""

import os
import sys
import time
import json
import calendar
import requests
import datetime as dt

try:
    import pandas as pd
    import numpy as np
except ImportError:
    print("[ERROR] This script requires pandas and numpy. Install with:")
    print("       pip install pandas numpy requests")
    sys.exit(1)

# ---------------------------------------------------------------------------
#                        OAuth (Environment-Based)
# ---------------------------------------------------------------------------
API_BASE = "https://webexapis.com/v1"
REPORTS_URL = f"{API_BASE}/wholesale/billing/reports"

# Load from environment instead of hardcoding
CLIENT_ID = os.environ.get("WEBEX_CLIENT_ID")
CLIENT_SECRET = os.environ.get("WEBEX_CLIENT_SECRET")
ACCESS_TOKEN = os.environ.get("WEBEX_ACCESS_TOKEN")
REFRESH_TOKEN = os.environ.get("WEBEX_REFRESH_TOKEN")


def require_env(var_name: str):
    if not os.environ.get(var_name):
        raise RuntimeError(
            f"Environment variable {var_name} is not set. "
            f"Please export it before running this script."
        )


for var in ("WEBEX_CLIENT_ID", "WEBEX_CLIENT_SECRET",
            "WEBEX_ACCESS_TOKEN", "WEBEX_REFRESH_TOKEN"):
    require_env(var)


def refresh_access_token(verbose: bool = True) -> str:
    """
    Refresh the Webex ACCESS_TOKEN using the REFRESH_TOKEN.
    Returns the new ACCESS_TOKEN string.
    """
    token_url = f"{API_BASE}/access_token"
    data = {
        "grant_type": "refresh_token",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "refresh_token": REFRESH_TOKEN,
    }

    if verbose:
        print("[INFO] Refreshing Webex access token...")

    try:
        r = requests.post(token_url, data=data, timeout=45)
        if verbose:
            print(f"[DEBUG] Token refresh status {r.status_code}")

        if r.status_code == 200:
            resp = r.json()
            new_token = resp.get("access_token")
            if not new_token:
                raise RuntimeError("No access_token in refresh response.")
            return new_token

        raise RuntimeError(f"Refresh failed: {r.status_code} {r.text}")

    except Exception as e:
        raise RuntimeError(f"Token refresh exception: {e}")


def auth_header(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }


# Perform token refresh at startup
try:
    ACCESS_TOKEN = refresh_access_token(verbose=True)
except Exception as e:
    print(f"[FATAL] Could not refresh access token: {e}")
    sys.exit(1)

# ---------------------------------------------------------------------------
#                      Date Helpers (Previous Billing Month)
# ---------------------------------------------------------------------------


def previous_month_first_last():
    today = dt.date.today().replace(day=1)
    last_day_prev = today - dt.timedelta(days=1)
    first_day_prev = last_day_prev.replace(day=1)
    return (
        first_day_prev.strftime("%Y-%m-%d"),
        last_day_prev.strftime("%Y-%m-%d"),
        first_day_prev.strftime("%B"),
        first_day_prev.strftime("%Y"),
    )


def days_in_last_month() -> int:
    today = dt.date.today().replace(day=1)
    last = today - dt.timedelta(days=1)
    return calendar.monthrange(last.year, last.month)[1]

# ---------------------------------------------------------------------------
#                      HTTP Wrapper with Retry Logic
# ---------------------------------------------------------------------------


def req(session, method, url, **kwargs):
    delay = 1.5
    for _ in range(8):
        r = session.request(method, url, timeout=60, **kwargs)
        if r.status_code in (429, 500, 502, 503, 504):
            ra = r.headers.get("Retry-After")
            wait = float(ra) if ra else delay
            print(f"[WARN] Retry {method} {url}: {r.status_code}, sleeping {wait}s...")
            time.sleep(wait)
            delay = min(delay * 2, 60)
            continue
        r.raise_for_status()
        return r
    r.raise_for_status()
    return r

# ---------------------------------------------------------------------------
#                          Billing Report Orchestration
# ---------------------------------------------------------------------------


def list_reports_for_period(session, start_date, end_date):
    r = req(session, "GET", REPORTS_URL, headers=auth_header(ACCESS_TOKEN))
    items = r.json().get("items") or []
    for it in items:
        if (
            it.get("billingStartDate") == start_date and
            it.get("billingEndDate") == end_date
        ):
            return it.get("id"), it.get("status")
    return None, None


def poll_completed_report_id(session, start_date, end_date):
    while True:
        r = req(session, "GET", REPORTS_URL, headers=auth_header(ACCESS_TOKEN))
        items = r.json().get("items") or []
        for it in items:
            if (
                it.get("billingStartDate") == start_date and
                it.get("billingEndDate") == end_date and
                it.get("status") == "COMPLETED"
            ):
                return it.get("id")
        print("[INFO] Waiting for report to complete (10s)...")
        time.sleep(10)


def ensure_report(session, start_date, end_date):
    rid, status = list_reports_for_period(session, start_date, end_date)

    if rid:
        if status == "COMPLETED":
            return rid
        if status in ("REQUESTED", "IN_PROGRESS"):
            print(f"[INFO] Using in-progress report {rid}. Polling...")
            return poll_completed_report_id(session, start_date, end_date)
        if status == "FAILED":
            print(f"[WARN] Found FAILED report {rid}; creating new one...")
        else:
            print(f"[INFO] Report {rid} status={status}. Polling...")
            return poll_completed_report_id(session, start_date, end_date)

    payload = {
        "billingStartDate": start_date,
        "billingEndDate": end_date,
        "type": "CUSTOMER",
    }

    resp = session.post(
        REPORTS_URL,
        headers={**auth_header(ACCESS_TOKEN), "Content-Type": "application/json"},
        json=payload,
        timeout=60,
    )

    if resp.status_code == 409:
        print("[INFO] Report already exists. Polling...")
    elif resp.status_code >= 400:
        raise RuntimeError(f"Create report failed: {resp.status_code} {resp.text}")
    else:
        print("[INFO] Report creation accepted.")

    return poll_completed_report_id(session, start_date, end_date)


def get_temp_download_url(session, report_id):
    r = req(session, "GET", f"{REPORTS_URL}/{report_id}", headers=auth_header(ACCESS_TOKEN))
    data = r.json()
    url = data.get("tempDownloadURL")
    if not url:
        raise RuntimeError(f"No tempDownloadURL in response: {data}")
    return url


def download_file(session, url, dest_path):
    with session.get(url, stream=True, timeout=120) as r:
        r.raise_for_status()
        with open(dest_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 512):
                if chunk:
                    f.write(chunk)

# ---------------------------------------------------------------------------
#                        CSV Transformation Logic
# ---------------------------------------------------------------------------


def transform_billing_report(original_csv, final_csv, days):
    """
    Transformation rules:

    - Remove the first 4 columns
    - Take the 7th column (index 6) after trimming → Column K
    - BILLABLE_UNITS = ceil(ColumnK / days_in_last_month)
    - Append BILLABLE_UNITS as the final column
    """
    df = pd.read_csv(original_csv, dtype=str, keep_default_na=False, na_values=[])

    if df.shape[1] <= 4:
        trimmed = pd.DataFrame()
    else:
        trimmed = df.iloc[:, 4:].copy()

    col_k_index = 6
    billable = pd.Series([""] * len(trimmed), dtype=object)

    if not trimmed.empty and trimmed.shape[1] > col_k_index:
        raw_vals = pd.to_numeric(trimmed.iloc[:, col_k_index], errors="coerce")
        with np.errstate(invalid="ignore", divide="ignore"):
            billable_units = np.ceil(raw_vals / float(days))
        mask = np.isfinite(billable_units)
        billable.loc[mask] = billable_units[mask].astype(int).astype(str)

    trimmed["BILLABLE_UNITS"] = billable
    trimmed.to_csv(final_csv, index=False)

# ---------------------------------------------------------------------------
#                                   Main
# ---------------------------------------------------------------------------


def main():
    start_date, end_date, month_name, year_str = previous_month_first_last()
    ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")

    original_csv = f"{month_name}-{year_str}-Wholesale-Usage_{ts}_ORIGINAL.csv"
    final_csv = f"{month_name}-{year_str}-Wholesale-Usage_{ts}.csv"

    print(f"[INFO] Fetching billing report for {start_date} → {end_date}")

    with requests.Session() as session:
        report_id = ensure_report(session, start_date, end_date)
        print(f"[OK] Report ready: {report_id}")

        url = get_temp_download_url(session, report_id)
        print("[OK] Temporary download URL retrieved.")

        print(f"[INFO] Downloading raw CSV → {original_csv}")
        download_file(session, url, original_csv)
        print("[OK] Download complete.")

    days = days_in_last_month()
    print(f"[INFO] Transforming CSV (days_in_last_month={days})...")
    transform_billing_report(original_csv, final_csv, days)

    print("[OK] Final transformed CSV:", final_csv)
    print("[OK] Original CSV saved:", original_csv)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(1)
