#!/usr/bin/env python3

"""
Webex PSTN Discovery Tool

This script discovers PSTN connection options across all customer organizations
under a Webex Partner account. For each org, it:

    1. Activates the organization (adds it to Managed Customers)
    2. Retrieves all locations
    3. Queries /telephony/config/connectionOptions for each location
    4. Saves raw and provider-filtered PSTN option data to JSON files

This tool is designed for MSPs and Cisco partners performing PSTN migrations,
audits, or large-scale telephony evaluations.

A Webex OAuth access token must be provided via WEBEX_ACCESS_TOKEN.

Usage:
    export WEBEX_ACCESS_TOKEN="your_token_here"
    python3 webex_pstn_discovery.py
"""

import os
import sys
import json
import requests
from datetime import datetime

# === CONFIGURATION ===
BASE_URL = "https://webexapis.com/v1"

# Expect a raw access token from the environment
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

# Optional: provider keyword to filter on (e.g., "veracity", "calltower", "intelepeer")
# Defaults to "veracity" for backwards compatibility, but can be set to any value.
PROVIDER_KEYWORD = os.environ.get("PSTN_PROVIDER_KEYWORD", "veracity").lower()

# === LOG DIRECTORY SETUP ===
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
base_dir = f"PSTN_Discovery_Logs_{timestamp}"
raw_dir = os.path.join(base_dir, "Raw_PSTN_Options")
filtered_dir = os.path.join(base_dir, "Filtered_Provider_Options")
location_dir = os.path.join(base_dir, "Location_Responses")
os.makedirs(raw_dir, exist_ok=True)
os.makedirs(filtered_dir, exist_ok=True)
os.makedirs(location_dir, exist_ok=True)

all_provider_matches = []
errors = []

# === FUNCTIONS ===

def get_all_organizations():
    url = f"{BASE_URL}/organizations"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json().get("items", [])
    else:
        print(f"❌ Failed to retrieve organizations: {response.status_code} - {response.text}")
        return []

def activate_org(org_id):
    url = f"{BASE_URL}/organizations/{org_id}"
    try:
        response = requests.get(url, headers=HEADERS)
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        print(f"❌ Error activating org {org_id}: {e}")
        return False

def get_locations(org_id):
    url = f"{BASE_URL}/locations?orgId={org_id}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        raise Exception(f"Failed to get locations for org {org_id}: {response.status_code} - {response.text}")
    return response.json().get("items", [])

def get_pstn_options(org_id, location_id):
    url = f"{BASE_URL}/telephony/pstn/locations/{location_id}/connectionOptions?orgId={org_id}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        raise Exception(f"Failed to get PSTN options for location {location_id} in org {org_id}: {response.status_code} - {response.text}")
    return response.json().get("items", [])

# === MAIN EXECUTION ===

orgs = get_all_organizations()
print(f"🔍 Found {len(orgs)} organizations")
print(f"🔎 Filtering PSTN options using provider keyword: '{PROVIDER_KEYWORD}'")

for org in orgs:
    org_id = org.get("id")
    print(f"\n🔄 Processing Org: {org_id}")

    try:
        if not activate_org(org_id):
            raise Exception(f"Could not activate org {org_id}")

        locations = get_locations(org_id)
        print(f"📍 Found {len(locations)} locations")

        # Save location list
        with open(os.path.join(location_dir, f"{org_id}.json"), "w") as f:
            json.dump(locations, f, indent=2)

        for loc in locations:
            loc_id = loc.get("id")
            loc_name = loc.get("name", "Unknown")
            try:
                options = get_pstn_options(org_id, loc_id)

                # Save raw options
                with open(os.path.join(raw_dir, f"{org_id}_{loc_id}.json"), "w") as f:
                    json.dump(options, f, indent=2)

                # Filter for entries whose displayName contains the provider keyword
                provider_matches = [
                    item
                    for item in options
                    if PROVIDER_KEYWORD in item.get("displayName", "").lower()
                ]

                if provider_matches:
                    print(f"🔎 Matching PSTN options found for location: {loc_name}")
                    all_provider_matches.append({
                        "org_id": org_id,
                        "location_id": loc_id,
                        "location_name": loc_name,
                        "provider_keyword": PROVIDER_KEYWORD,
                        "matches": provider_matches,
                    })
                    with open(os.path.join(filtered_dir, f"{org_id}_{loc_id}.json"), "w") as f:
                        json.dump(provider_matches, f, indent=2)

            except Exception as e:
                print(f"[✗] PSTN options failed for {loc_name}: {e}")
                errors.append({
                    "org_id": org_id,
                    "location_id": loc_id,
                    "location_name": loc_name,
                    "error": str(e),
                })

    except Exception as e:
        print(f"[✗] Org failed: {e}")
        errors.append({"org_id": org_id, "error": str(e)})

# === WRITE AGGREGATE LOGS ===

with open(os.path.join(base_dir, "all_provider_matches.json"), "w") as f:
    json.dump(all_provider_matches, f, indent=2)

with open(os.path.join(base_dir, "errors.json"), "w") as f:
    json.dump(errors, f, indent=2)

print("\n✅ PSTN Discovery Complete!")
print(f"🔍 Found {len(all_provider_matches)} location(s) matching provider keyword '{PROVIDER_KEYWORD}'")
print(f"📁 Logs saved in: {base_dir}")
