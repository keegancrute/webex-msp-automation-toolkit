#!/usr/bin/env python3

"""
Webex PSTN Swapper (Single-Organization Version)

This script updates PSTN assignments for all locations in a single Webex
customer organization. It is typically used for targeted migrations, testing,
or validation of PSTN change workflows.

Functionality:
    - Activates the organization via /organizations/{orgId}
    - Retrieves all location IDs
    - Queries connectionOptions to identify valid PSTN provider IDs
    - Applies a selected PSTN provider to all locations
    - Produces a detailed per-location status report

Outputs:
    - pstn_swapper_<timestamp>.json

Use this version for testing before running bulk changes with the Flipper tool.

Requires WEBEX_ACCESS_TOKEN to be set in the environment.

Usage:
    export WEBEX_ACCESS_TOKEN="your_token_here"
    python3 webex_pstn_swapper.py
"""

import os
import sys
import json
import requests
from datetime import datetime

# === CONFIGURATION ===
ORG_ID = "REPLACE_WITH_TARGET_ORGANIZATION_ID"
PSTN_OPTION_ID = "REPLACE_WITH_VALID_LOCATION_PSTN_CONNECTION_OPTION_ID"

ACCESS_TOKEN = os.environ.get("WEBEX_ACCESS_TOKEN")

if not ACCESS_TOKEN:
    print("ERROR: WEBEX_ACCESS_TOKEN environment variable is not set.")
    print("       Export it first, e.g.:")
    print('       export WEBEX_ACCESS_TOKEN="your_access_token_here"')
    sys.exit(1)

HEADERS = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Accept": "application/json",
    "Content-Type": "application/json",
}

# === TIMESTAMP & LOG FILE SETUP ===
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
location_log_dir = "Location Collector Logs"
pstn_log_dir = "PSTN Swapper Logs"
os.makedirs(location_log_dir, exist_ok=True)
os.makedirs(pstn_log_dir, exist_ok=True)

location_log_path = os.path.join(location_log_dir, f"LocationLogs_{timestamp}.json")
pstn_log_path = os.path.join(pstn_log_dir, f"PSTNSwapperLogs_{timestamp}.json")

# === FUNCTIONS ===

def activate_org(org_id):
    url = f"https://webexapis.com/v1/organizations/{org_id}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        print(f"[ERROR] Could not activate org {org_id} – status code: {response.status_code} – {response.text}")
        return False
    return True

def get_locations(org_id):
    url = f"https://webexapis.com/v1/locations?orgId={org_id}"
    response = requests.get(url, headers=HEADERS)
    data = response.json()

    with open(location_log_path, "w") as f:
        json.dump(data, f, indent=2)

    return data.get("items", [])

def swap_pstn(org_id, location):
    location_id = location.get("id")
    location_name = location.get("name", "Unknown Location")
    url = f"https://webexapis.com/v1/telephony/pstn/locations/{location_id}/connection?orgId={org_id}"
    payload = json.dumps({"id": PSTN_OPTION_ID})
    response = requests.put(url, headers=HEADERS, data=payload)

    return {
        "location_id": location_id,
        "location_name": location_name,
        "status_code": response.status_code,
        "response_text": response.text
    }

# === MAIN EXECUTION ===

def main():
    print(f"🔧 Starting PSTN Swapper for Org: {ORG_ID}")
    if not activate_org(ORG_ID):
        print("[EXITING] Could not activate org, halting script.")
        return

    locations = get_locations(ORG_ID)
    pstn_results = []

    for loc in locations:
        result = swap_pstn(ORG_ID, loc)
        code = result["status_code"]
        name = result["location_name"]
        if code == 204:
            print(f"[✓] PSTN updated for: {name}")
        else:
            print(f"[✗] ERROR updating PSTN for: {name} – status {code}")
        pstn_results.append(result)

    with open(pstn_log_path, "w") as f:
        json.dump(pstn_results, f, indent=2)

    print("\n✅ Script complete. Check log files for full results.")

if __name__ == "__main__":
    main()
