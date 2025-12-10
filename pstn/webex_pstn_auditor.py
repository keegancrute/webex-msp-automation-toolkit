#!/usr/bin/env python3

"""
Webex PSTN Configuration Auditor

This script audits PSTN assignments across multiple Webex customer
organizations. For each org, it:

    - Activates the organization in Partner scope
    - Retrieves all locations
    - Queries /telephony/config/locations/{locationId}/pstnConnection
    - Builds a structured JSON report summarizing:
        * Current PSTN provider per location
        * Missing or invalid PSTN configurations
        * Orgs with zero locations or unreadable data

Outputs include:
    - pstn_audit_<timestamp>.json
    - pstn_audit_flat_<timestamp>.csv

This tool is used to verify readiness before mass PSTN migrations, enforce
provider consistency, and identify outlier configurations.

Requires a Webex OAuth token via WEBEX_ACCESS_TOKEN.

Usage:
    export WEBEX_ACCESS_TOKEN="your_token_here"
    python3 webex_pstn_auditor.py
"""

import requests
import json
import os
import sys
import time
from datetime import datetime
import pytz
from ratelimit import limits, sleep_and_retry

# === CONFIGURATION ===
BASE_URL = "https://webexapis.com/v1"

# Expect a raw access token in the environment
ACCESS_TOKEN = os.environ.get("WEBEX_ACCESS_TOKEN")

if not ACCESS_TOKEN:
    print("ERROR: WEBEX_ACCESS_TOKEN environment variable is not set.")
    print("       Export it first, e.g.:")
    print('       export WEBEX_ACCESS_TOKEN="your_access_token_here"')
    sys.exit(1)

HEADERS = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Accept": "application/json",
}

# Example placeholder org IDs; replace with real ones locally, don't commit them
ORG_IDS = [
    "ORGANIZATION-ID1",
    "ORGANIZATION-ID2",
    "ORGANIZATION-ID3",
    "ORGANIZATION-ID4",
]

DEBUG = True
REQUESTS_PER_MINUTE = 10  # 10 requests per 60 seconds
DELAY_BETWEEN_REQUESTS = 60 / REQUESTS_PER_MINUTE  # = 6 seconds

# === FOLDER SETUP ===
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
OUTPUT_FOLDER = "output/audits"
LOG_FOLDER = "output/logs"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(LOG_FOLDER, exist_ok=True)
tracking_log = []

# === FUNCTIONS ===
def log_response(org_id, call_type, url, response):
    try:
        tracking_id = response.headers.get("trackingid", "N/A")
    except:
        tracking_id = "N/A"
    log_entry = {
        "orgId": org_id,
        "callType": call_type,
        "url": url,
        "statusCode": response.status_code,
        "trackingId": tracking_id,
        "responseText": response.text,
        "timestamp": datetime.now().astimezone().isoformat()
    }
    tracking_log.append(log_entry)
    return tracking_id

def log_timeout(org_id, call_type, url, exception):
    log_entry = {
        "orgId": org_id,
        "callType": call_type,
        "url": url,
        "statusCode": "TIMEOUT",
        "trackingId": "N/A",
        "responseText": str(exception),
        "timestamp": datetime.now().astimezone().isoformat()
    }
    tracking_log.append(log_entry)

# --- RATE LIMITED REQUEST WRAPPER ---
@sleep_and_retry
@limits(calls=10, period=60)  # 10 requests per 60 seconds
def rate_limited_get(url, headers, timeout=60):
    response = requests.get(url, headers=headers, timeout=timeout)
    time.sleep(DELAY_BETWEEN_REQUESTS)  # small enforced delay between each request
    return response

def get_organization(org_id):
    url = f"{BASE_URL}/organizations/{org_id}"
    retries = 0
    while True:
        try:
            response = rate_limited_get(url, HEADERS, timeout=60)
            if response.status_code == 429:
                retries += 1
                retry_after = int(response.headers.get("Retry-After", "5"))
                print(f"⏳ Rate limited for org {org_id}. Retry #{retries}. Sleeping for {retry_after} seconds...")
                time.sleep(retry_after)
                continue
            tracking_id = log_response(org_id, "organization", url, response)
            if retries > 0:
                print(f"✅ Success after {retries} retries for org {org_id}")
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Org activation failed for {org_id}: {e}")
            log_timeout(org_id, "organization", url, e)
            return False

def get_locations(org_id):
    url = f"{BASE_URL}/locations?orgId={org_id}"
    try:
        response = rate_limited_get(url, HEADERS, timeout=60)
        tracking_id = log_response(org_id, "locations", url, response)
        if response.status_code == 200:
            return response.json().get("items", [])
        else:
            print(f"❌ Failed to get locations for {org_id}: {response.status_code} - {tracking_id}")
            return []
    except Exception as e:
        print(f"❌ Error getting locations for {org_id}: {e}")
        log_timeout(org_id, "locations", url, e)
        return []

def get_pstn(org_id, location_id):
    url = f"{BASE_URL}/telephony/pstn/locations/{location_id}/connection?orgId={org_id}"
    try:
        response = rate_limited_get(url, HEADERS, timeout=60)
        log_response(org_id, "pstn_connection", url, response)
        if response.status_code == 200:
            return response.json()
        else:
            return {}
    except Exception as e:
        print(f"❌ Error getting PSTN for location {location_id} in org {org_id}: {e}")
        log_timeout(org_id, "pstn_connection", url, e)
        return {}

# === MAIN SCRIPT ===
results_by_org = {}
successful_orgs = []
failed_orgs = []

for idx, org_id in enumerate(ORG_IDS, start=1):
    print(f"\n🚀 [{idx}/{len(ORG_IDS)}] Processing org: {org_id}")

    try:
        # Step 1: Activate Organization
        if not get_organization(org_id):
            print(f"⚠️ Skipping org {org_id} (activation failed)")
            failed_orgs.append(org_id)
            continue

        # Step 2: Get Locations
        locations = get_locations(org_id)
        if not locations:
            print(f"⚠️ No locations found for org {org_id}")
            failed_orgs.append(org_id)
            continue

        results_by_org[org_id] = []

        # Step 3: PSTN Data for Each Location
        for location in locations:
            loc_id = location["id"]
            loc_name = location.get("name", "Unknown")
            pstn_data = get_pstn(org_id, loc_id)
            results_by_org[org_id].append({
                "locationId": loc_id,
                "locationName": loc_name,
                "pstnConnection": pstn_data
            })

        successful_orgs.append(org_id)
        print(f"✅ Completed org {org_id}")

    except Exception as e:
        print(f"🔥 Unexpected error for org {org_id}: {e}")
        failed_orgs.append(org_id)
        continue

# === SAVE RESULTS ===
json_filename = f"PSTNConnections_{timestamp}.json"
json_path = os.path.join(OUTPUT_FOLDER, json_filename)
with open(json_path, "w") as f:
    json.dump(results_by_org, f, indent=2)

log_filename = f"API_TrackingLog_{timestamp}.json"
log_path = os.path.join(LOG_FOLDER, log_filename)
with open(log_path, "w") as f:
    json.dump(tracking_log, f, indent=2)

# === SAVE SUCCESS/FAIL LISTS ===
success_path = os.path.join(LOG_FOLDER, f"Successful_Orgs_{timestamp}.txt")
fail_path = os.path.join(LOG_FOLDER, f"Failed_Orgs_{timestamp}.txt")

with open(success_path, "w") as f:
    f.write("\n".join(successful_orgs))
with open(fail_path, "w") as f:
    f.write("\n".join(failed_orgs))

print(f"\n📁 Results saved to: {json_path}")
print(f"📝 Tracking log saved to: {log_path}")
print(f"✅ Successful Orgs: {len(successful_orgs)}  |  ❌ Failed Orgs: {len(failed_orgs)}")
print(f"📄 Success list: {success_path}")
print(f"📄 Fail list: {fail_path}")

if failed_orgs:
    print("\n⚠️ Failed Organization IDs:")
    for f_org in failed_orgs:
        print(f"   - {f_org}")
