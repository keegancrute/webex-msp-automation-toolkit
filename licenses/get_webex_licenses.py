#!/usr/bin/env python3

"""
Retrieve Webex Licenses for Customer Organizations

This script reads a cleaned overages CSV (Customer Name + Customer Org ID),
activates each organization in the Webex Partner API, and retrieves all
associated licenses via the /v1/licenses endpoint.

Outputs:
    - successful_orgs_<timestamp>.json
    - failed_orgs_<timestamp>.json
    - webex_org_details_<timestamp>.csv

The script requires a valid Webex OAuth token provided via the
WEBEX_ACCESS_TOKEN environment variable.

Usage:
    export WEBEX_ACCESS_TOKEN="your_access_token_here"
    python3 get_webex_licenses.py
"""

import os
import sys
import requests
import pandas as pd
import json
import time
import csv
from datetime import datetime

# Generate timestamp
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

# Constants
CSV_FILE = input("Enter the path to the cleaned CSV file: ")
SUCCESSFUL_JSON = f"successful_orgs_{timestamp}.json"
FAILED_JSON = f"failed_orgs_{timestamp}.json"
ORG_DETAILS_CSV = f"webex_org_details_{timestamp}.csv"

BASE_URL = "https://webexapis.com/v1"

# Load token from environment variable instead of hardcoding
ACCESS_TOKEN = os.environ.get("WEBEX_ACCESS_TOKEN")

if not ACCESS_TOKEN:
    print("ERROR: WEBEX_ACCESS_TOKEN environment variable is not set.")
    print('       export WEBEX_ACCESS_TOKEN="your_access_token_here"')
    sys.exit(1)

HEADERS = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json",
    "Accept": "application/json",
}


DEBUG = True  # Set to False to disable extra logging
MAX_RETRIES = 3  # Retry limit for API requests

# Load CSV Data
df = pd.read_csv(CSV_FILE)
org_data = df[['Customer Name', 'Customer Org ID']].drop_duplicates()

# Initialize results storage
successful_orgs = {}
failed_orgs = []
org_details_list = []  # Stores organization details for CSV output

# Function to activate & get organization details
def activate_organization(org_id):
    url = f"{BASE_URL}/organizations/{org_id}"
    response = requests.get(url, headers=HEADERS)
    
    if response.status_code == 200:
        org_info = response.json()  # Capture org details
        if DEBUG:
            print(f"✅ Activated & Retrieved Org Info: {org_info.get('displayName', 'Unknown')}")
        return org_info  # Return full org details
    else:
        print(f"❌ Failed to activate Org {org_id}: {response.status_code} - {response.text}")
        return None

# Function to fetch licenses for an org with proper error handling
def fetch_licenses(org_id):
    url = f"{BASE_URL}/licenses?orgId={org_id}"

    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, headers=HEADERS)
            
            if response.status_code == 403:
                print(f"🚫 403 Forbidden for Org {org_id}. Skipping retries.")
                return None  # Don't retry 403 errors

            if response.status_code == 429:
                print(f"⚠️ 429 Too Many Requests. Retrying after 10s...")
                time.sleep(10)  # Wait longer for rate limits
                continue  # Retry

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            print(f"🔁 Attempt {attempt+1} failed for Org {org_id}: {e}")
            time.sleep(3)  # Wait before retrying

    return None  # Return None if all retries fail

# Process each org
for index, row in org_data.iterrows():
    customer_name = row['Customer Name']
    org_id = row['Customer Org ID']
    print(f"🔄 Processing: {customer_name} (Org ID: {org_id})")

    # Activate the org and get org details
    org_info = activate_organization(org_id)

    if not org_info:
        failed_orgs.append({
            "customer_name": customer_name,
            "org_id": org_id,
            "status_code": 403,
            "error": "Failed to activate in Managed Customer List"
        })
        continue  # Skip to the next org if activation fails

    # Fetch licenses after activation
    response_data = fetch_licenses(org_id)

    if response_data and "items" in response_data:
        successful_orgs[org_id] = {
            "customer_name": customer_name,
            "org_id": org_id,
            "org_display_name": org_info.get("displayName", "Unknown"),
            "created": org_info.get("created", "Unknown"),
            "country_code": org_info.get("countryCode", "Unknown"),
            "licenses": response_data["items"]
        }

        # Save org details for CSV
        org_details_list.append({
            "Customer Name": customer_name,
            "Org ID": org_id,
            "Org Display Name": org_info.get("displayName", "Unknown"),
            "Created": org_info.get("created", "Unknown"),
            "Country Code": org_info.get("countryCode", "Unknown"),
            "License Count": len(response_data["items"])
        })

    else:
        failed_orgs.append({
            "customer_name": customer_name,
            "org_id": org_id,
            "status_code": response_data.get("status", "No Response") if response_data else "No Response",
            "error": "No licenses returned"
        })

    time.sleep(1)  # Prevent API rate limits

# Save results to JSON
with open(SUCCESSFUL_JSON, "w") as f:
    json.dump(successful_orgs, f, indent=4)
print(f"✅ Successful orgs saved to {SUCCESSFUL_JSON}")

if failed_orgs:
    with open(FAILED_JSON, "w") as f:
        json.dump(failed_orgs, f, indent=4)
    print(f"⚠️ Failed orgs saved to {FAILED_JSON} for retry.")

# Save org details to CSV
with open(ORG_DETAILS_CSV, mode="w", newline="") as file:
    writer = csv.DictWriter(file, fieldnames=["Customer Name", "Org ID", "Org Display Name", "Created", "Country Code", "License Count"])
    writer.writeheader()
    writer.writerows(org_details_list)
print(f"📁 Org details saved to {ORG_DETAILS_CSV}")

print("🎉 Script completed! Check JSON & CSV files for results.")


