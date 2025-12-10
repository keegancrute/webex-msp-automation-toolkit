#!/usr/bin/env python3
"""
Fetch Webex Licenses (Hardcoded Org IDs)

This script activates organizations in the Webex Partner API and retrieves all
licenses for each org via the /v1/licenses endpoint. It handles paging, error
responses, and rate limiting, and produces:

    - successful_orgs_<timestamp>.json
    - failed_orgs_<timestamp>.json
    - webex_licenses_<timestamp>.csv

Organizations must be added manually to the ORGS list.
A Webex OAuth token must be provided via the WEBEX_ACCESS_TOKEN environment
variable.

Usage:
    export WEBEX_ACCESS_TOKEN="your_access_token_here"
    python3 webex_license_counter.py
"""


import json
import sys
import os
from datetime import datetime
from typing import Dict, List, Tuple, Any

import pandas as pd
import requests
from ratelimit import limits, sleep_and_retry

# -----------------------------
# 🔧 CONFIG - EDIT THESE
# -----------------------------
BASE_URL = "https://webexapis.com/v1"

# 1) Expect a raw access token in the environment
ACCESS_TOKEN = os.environ.get("WEBEX_ACCESS_TOKEN")

if not ACCESS_TOKEN:
    print("ERROR: WEBEX_ACCESS_TOKEN environment variable is not set.")
    print("       Export it first, e.g.:")
    print('       export WEBEX_ACCESS_TOKEN="your_access_token_here"')
    sys.exit(1)

# 2) Hardcoded list of org IDs you want to process (examples only)
ORGS: List[str] = [
    # "00000000-0000-0000-0000-000000000000",
    # "11111111-1111-1111-1111-111111111111",
]

# Request tuning
REQUEST_TIMEOUT = 30  # seconds per request
MAX_RETRIES = 4       # retries on 429/5xx (currently informational)
PAGE_SIZE = 100       # licenses page size (Webex defaults to 100)

# Rate limiting: Cisco suggested 10 calls / minute
CALLS = 10
PERIOD = 60  # seconds


# -----------------------------
# 🧰 HTTP helpers
# -----------------------------

def auth_headers() -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


@sleep_and_retry
@limits(calls=CALLS, period=PERIOD)
def _rate_limited_request(method: str, url: str, params: Dict[str, Any] = None) -> requests.Response:
    """Requests wrapper that is rate-limited."""
    return requests.request(
        method=method,
        url=url,
        headers=auth_headers(),
        params=params or {},
        timeout=REQUEST_TIMEOUT,
    )


# -----------------------------
# 🔄 Org activation
# -----------------------------

def activate_org(org_id: str) -> Tuple[bool, str, Dict[str, Any]]:
    """Activate org by calling Organizations detail endpoint.

    Returns (ok, display_name, payload_or_error_info)
    """
    url = f"{BASE_URL}/organizations/{org_id}"
    resp = _rate_limited_request("GET", url)

    try:
        data = resp.json()
    except ValueError:
        data = {"raw_text": resp.text}

    ok = resp.status_code == 200 and isinstance(data, dict) and data.get("id")
    display_name = data.get("displayName") if ok else None

    return ok, display_name, {
        "status_code": resp.status_code,
        "response": data,
        "headers": {k: v for k, v in resp.headers.items()},
    }


# -----------------------------
# 📜 Licenses fetch (paged)
# -----------------------------

def fetch_licenses(org_id: str) -> Tuple[bool, List[Dict[str, Any]], Dict[str, Any]]:
    url = f"{BASE_URL}/licenses"
    all_items: List[Dict[str, Any]] = []
    params = {"orgId": org_id, "max": PAGE_SIZE}

    page = 1
    while True:
        resp = _rate_limited_request("GET", url, params=params)
        meta: Dict[str, Any] = {
            "status_code": resp.status_code,
            "page": page,
            "params": dict(params),
            "headers": {k: v for k, v in resp.headers.items()},
        }

        if resp.status_code != 200:
            try:
                meta["error_body"] = resp.json()
            except ValueError:
                meta["error_body"] = resp.text
            return False, [], meta

        try:
            payload = resp.json()
        except ValueError:
            meta["error_body"] = resp.text
            return False, [], meta

        items = payload.get("items", []) if isinstance(payload, dict) else []
        all_items.extend(items)

        link = resp.headers.get("Link", "")
        if "rel=\"next\"" in link:
            next_url = None
            parts = [p.strip() for p in link.split(",")]
            for p in parts:
                if 'rel="next"' in p:
                    try:
                        start = p.index("<") + 1
                        end = p.index(">")
                        next_url = p[start:end]
                    except Exception:
                        next_url = None
                    break
            if next_url:
                url = next_url
                params = {}
                page += 1
                continue
        break

    return True, all_items, {"status_code": 200, "pages": page}


# -----------------------------
# 🧾 Flatten license rows for DataFrame
# -----------------------------

def normalize_license_rows(customer_name: str, org_id: str, licenses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows = []
    for lic in licenses:
        rows.append({
            "customer_name": customer_name,
            "org_id": org_id,
            "license_id": lic.get("id") or lic.get("licenseId"),
            "license_name": lic.get("name"),
            "total_units": lic.get("totalUnits"),
            "consumed_units": lic.get("consumedUnits"),
            "subscription_id": lic.get("subscriptionId"),
            "status": lic.get("status"),
            "sku": lic.get("skuId") or lic.get("sku"),
            "offer_id": lic.get("offerId"),
            "created": lic.get("created"),
            "modified": lic.get("modified"),
        })
    return rows


# -----------------------------
# 🚀 Main
# -----------------------------

def main() -> None:
    # ORGS must be populated by the user
    if not ORGS:
        print("[!] Please populate the ORGS list with org_id strings.")
        sys.exit(1)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    successes: List[Dict[str, Any]] = []
    failures: List[Dict[str, Any]] = []
    flat_rows: List[Dict[str, Any]] = []

    for org_id in ORGS:
        print(f"\n=== Processing Org: {org_id} ===")

        ok_activate, display_name, activation_meta = activate_org(org_id)
        if not ok_activate:
            print(f"  [x] Activation failed (status {activation_meta.get('status_code')}).")
            failures.append({
                "org_id": org_id,
                "stage": "activate_org",
                **activation_meta,
            })
            continue
        else:
            print(f"  [+] Activated org: {display_name}")

        ok_lic, licenses, lic_meta = fetch_licenses(org_id)
        if not ok_lic:
            print(f"  [x] License fetch failed (status {lic_meta.get('status_code')}).")
            failures.append({
                "org_id": org_id,
                "org_name": display_name,
                "stage": "fetch_licenses",
                **lic_meta,
            })
            continue

        if not licenses:
            print("  [!] No licenses returned.")
            failures.append({
                "org_id": org_id,
                "org_name": display_name,
                "stage": "fetch_licenses",
                "status_code": lic_meta.get("status_code"),
                "error": "No licenses returned",
            })
        else:
            print(f"  [+] Licenses: {len(licenses)}")

        flat_rows.extend(normalize_license_rows(display_name, org_id, licenses))

        successes.append({
            "org_id": org_id,
            "org_name": display_name,
            "activation": activation_meta,
            "licenses_count": len(licenses),
            "licenses_sample": licenses[:3],
        })

    success_path = f"successful_orgs_{ts}.json"
    failed_path = f"failed_orgs_{ts}.json"
    csv_path = f"webex_licenses_{ts}.csv"

    with open(success_path, "w", encoding="utf-8") as f:
        json.dump(successes, f, indent=2)
    with open(failed_path, "w", encoding="utf-8") as f:
        json.dump(failures, f, indent=2)

    df = pd.DataFrame(flat_rows, columns=[
        "customer_name",
        "org_id",
        "license_id",
        "license_name",
        "total_units",
        "consumed_units",
        "subscription_id",
        "status",
        "sku",
        "offer_id",
        "created",
        "modified",
    ])

    if not df.empty:
        df = df.sort_values(by=["license_name", "customer_name", "org_id"], na_position="last")
        df.to_csv(csv_path, index=False)
        print(f"\n✅ Wrote CSV: {csv_path} (rows: {len(df)})")
    else:
        df.to_csv(csv_path, index=False)
        print(f"\n⚠️ No license rows; wrote empty CSV with headers: {csv_path}")

    print(f"📄 Success log: {success_path}")
    print(f"📄 Failure log: {failed_path}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
        sys.exit(130)
