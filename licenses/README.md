# Webex License Tools

This folder contains utilities for retrieving, analyzing, and formatting Webex license data across many customer organizations. These tools support MSP and partner automation workflows where engineers frequently need:

- A raw, programmatically retrieved snapshot of all licenses across orgs
- A structured, human-readable license report suitable for customers or leadership
- A clean separation between **license retrieval** and **license formatting**

Each script operates independently and can be run alone or chained together depending on your workflow.

---

## 1. get_webex_licenses.py — Multi-Org License Retrieval

Retrieves all license objects for each organization listed in the cleaned overages CSV (Customer Name + Org ID).

### What It Does
- Activates each organization via `GET /v1/organizations/{orgId}`
- Retrieves all license objects via `GET /v1/licenses`
- Handles retries, rate limits, and API quirks
- Exports:
  - `successful_orgs_TIMESTAMP.json`
  - `failed_orgs_TIMESTAMP.json`
  - `webex_org_details_TIMESTAMP.csv` (org-level license summary)

### How It Works
The script loads your Webex OAuth token from the environment:

    export WEBEX_ACCESS_TOKEN="your_token_here"

You provide the cleaned CSV path when prompted at runtime.

### Run It
    python3 get_webex_licenses.py

### Output Includes
- Activation log (per org)
- License objects (raw JSON)
- Structured license summary CSV

---

## 2. webex_license_count_cleaner.py — Wide-Format Excel License Report

Converts the raw, flat CSV of licenses into a wide Excel report where each org becomes one row and each license type is split into two columns: `(total)` and `(consumed)`.

### What It Does
- Accepts a CSV containing:

      customer_name, org_id, license_name, total_units, consumed_units

- Builds a wide pivot-style table such as:

      | customer_name | org_id | Meetings (total) | Meetings (consumed) | Calling (total) | Calling (consumed) | ... |

- Saves the output to an Excel `.xlsx` file

### Configure It
Inside the script:

    input_file = "INPUT_LICENSES.csv"
    output_file = "LICENSE_REPORT.xlsx"

### Run It
    python3 webex_license_count_cleaner.py

### Recommended Workflow

1. Retrieve raw licenses:

       python3 get_webex_licenses.py

   Produces: `webex_org_details_YYYYMMDD_HHMMSS.csv`

2. Clean & widen the license table:

       python3 webex_license_count_cleaner.py

   Produces: `LICENSE_REPORT.xlsx`

---

## Requirements

    pip install pandas requests ratelimit openpyxl

---

## Security Notes
- No secrets or tokens are stored in these scripts.
- `WEBEX_ACCESS_TOKEN` must be exported as an environment variable.
- Organization ID lists, if used, should not be committed to version control.
