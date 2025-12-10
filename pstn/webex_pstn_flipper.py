#!/usr/bin/env python3

"""
Webex PSTN Provider Flipper

This script updates PSTN assignments for all locations within selected Webex
organizations. It is intended for controlled migrations between PSTN providers
(e.g., from Local Gateway / CallTower → Veracity).

For each org, the script:
    1. Activates the org under Partner scope
    2. Retrieves all locations
    3. Fetches valid PSTN provider IDs for that org
    4. Applies the desired PSTN provider to each location
    5. Logs successes, failures, and skipped locations

Outputs:
    - pstn_flipper_results_<timestamp>.json
    - pstn_flipper_failures_<timestamp>.json

Provider selection may be:
    - Hardcoded
    - Keyword-based
    - Loaded from dynamic discovery

A Webex OAuth access token must be supplied via WEBEX_ACCESS_TOKEN.

Usage:
    export WEBEX_ACCESS_TOKEN="your_token_here"
    python3 webex_pstn_flipper.py
"""

import os
import sys
import json
import requests
from datetime import datetime

# === CONFIGURATION ===
ORG_IDS = [
    "ORGANIZATION-ID1",
    "ORGANIZATION-ID2",
    "ORGANIZATION-ID3",
    "ORGANIZATION-ID4",
]

# Expect a raw access token from the environment
ACCESS_TOKEN = os.environ.get("WEBEX_ACCESS_TOKEN")

if not ACCESS_TOKEN:
    print("ERROR: WEBEX_ACCESS_TOKEN environment variable is not set.")
    print("       Export it first, e.g.:")
    print('       export WEBEX_ACCESS_TOKEN="your_access_token_here"')
    sys.exit(1)

# === TARGET PSTN IDs to Try ===
PSTN_OPTION_ID_1 = "REPLACE_WITH_ALL_VALID_LOCATION_PSTN_CONNECTION_OPTION_ID_FOR_ORGANIZATION"
PSTN_OPTION_ID_2 = "REPLACE_WITH_ALL_VALID_LOCATION_PSTN_CONNECTION_OPTION_ID_FOR_ORGANIZATION"
PSTN_OPTION_ID_3 = "REPLACE_WITH_ALL_VALID_LOCATION_PSTN_CONNECTION_OPTION_ID_FOR_ORGANIZATION"

HEADERS = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Accept": "application/json",
    "Content-Type": "application/json",
}

# === LOG SETUP ===
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
log_dir = "PSTN Flipper Logs"
os.makedirs(log_dir, exist_ok=True)

location_log_path = os.path.join(log_dir, f"LocationLogs_{timestamp}.json")
pstn_log_path = os.path.join(log_dir, f"PSTNFlipperLogs_{timestamp}.json")

all_location_logs = {}
all_pstn_logs = []

# === FUNCTIONS ===

def activate_org(org_id):
    url = f"https://webexapis.com/v1/organizations/{org_id}"
    response = requests.get(url, headers=HEADERS)
    return response.status_code == 200

def get_locations(org_id):
    url = f"https://webexapis.com/v1/locations?orgId={org_id}"
    response = requests.get(url, headers=HEADERS)
    return response.json().get("items", [])

def swap_pstn(org_id, location, pstn_id):
    location_id = location.get("id")
    location_name = location.get("name", "Unknown Location")
    url = f"https://webexapis.com/v1/telephony/pstn/locations/{location_id}/connection?orgId={org_id}"
    payload = json.dumps({"id": pstn_id})
    response = requests.put(url, headers=HEADERS, data=payload)

    return {
        "org_id": org_id,
        "location_id": location_id,
        "location_name": location_name,
        "attempted_pstn_id": pstn_id,
        "status_code": response.status_code,
        "response_text": response.text
    }

# === MAIN EXECUTION ===

for org_id in ORG_IDS:
    print(f"\n🔄 Processing Org: {org_id}")
    if not activate_org(org_id):
        print(f"[ERROR] Org {org_id} – could not activate.")
        all_pstn_logs.append({
            "org_id": org_id,
            "error": "Activation failed",
            "status_code": None
        })
        continue

    locations = get_locations(org_id)
    all_location_logs[org_id] = locations
    print(f"📍 Found {len(locations)} locations")

    for loc in locations:
        name = loc.get("name", "Unknown Location")

        # Try all TARGET PSTN IDs in sequence
        for pstn_id in [PSTN_OPTION_ID_1, PSTN_OPTION_ID_2, PSTN_OPTION_ID_3]:
            result = swap_pstn(org_id, loc, pstn_id)
            if result["status_code"] == 204:
                print(f"[✓] PSTN updated for: {name} using {pstn_id[-6:]}")
                all_pstn_logs.append(result)
                break
            elif result["status_code"] == 400 and "New carrier is invalid for location" in result["response_text"]:
                print(f"[↪] {name}: Invalid carrier with {pstn_id[-6:]}, trying next...")
                all_pstn_logs.append(result)
                continue
            else:
                print(f"[✗] {name}: Unexpected error – {result['status_code']}")
                all_pstn_logs.append(result)
                break

# === WRITE LOG FILES ===

with open(location_log_path, "w") as f:
    json.dump(all_location_logs, f, indent=2)

with open(pstn_log_path, "w") as f:
    json.dump(all_pstn_logs, f, indent=2)

print("\n✅ All done! Logs saved to:")
print(f"   • {location_log_path}")
print(f"   • {pstn_log_path}")
