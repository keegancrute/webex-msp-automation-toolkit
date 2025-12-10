# Webex License Tools

This folder contains two utilities for collecting and formatting Webex license data across multiple customer organizations. 
They are designed for MSP, partner, and automation workflows where engineers frequently need:

- A raw, programmatically retrieved snapshot of all licenses across orgs
- A cleaned, human-readable Excel report suitable for delivery to customers or leadership

Both scripts operate independently and can be run in sequence or used separately depending on your workflow.

---

## 1. `webex_license_counter.py` — License Retrieval & Reporting

Fetches all license data from Webex for the organizations you specify.

### What It Does
- Activates each organization via `GET /v1/organizations/{orgId}`
- Retrieves all license objects via `GET /v1/licenses`
- Handles paging, rate limits, and API quirks
- Exports:
  - `successful_orgs_TIMESTAMP.json`
  - `failed_orgs_TIMESTAMP.json`
  - `webex_licenses_TIMESTAMP.csv` (flat license table)

### How It Works
The script pulls your Webex token from the environment:

    export WEBEX_ACCESS_TOKEN="your_token_here"

Then you manually populate the `ORGS` list inside the script with organization IDs.

### Run It

    python3 webex_license_counter.py

### Output Explained
- Activation log — whether each org successfully activated
- License records — every license object as returned by Webex
- Flattened CSV — one row per license type, per org

---

## 2. `webex_license_count_cleaner.py` — Wide-Format Excel Cleaner

Takes the raw CSV produced by the license counter and transforms it into a wide Excel report where each org becomes a row and each license type gets two columns: `(total)` and `(consumed)`.

### What It Does
- Reads a flat CSV of licenses
- Requires these columns:

      customer_name, org_id, license_name, total_units, consumed_units

- Builds a wide pivot-style table, for example:

      | customer_name | org_id | Meetings (total) | Meetings (consumed) | Calling (total) | Calling (consumed) | ... |

- Saves the output to an Excel `.xlsx` file

### Configure It
Inside the script, set:

      input_file = "INPUT_LICENSES.csv"
      output_file = "LICENSE_REPORT.xlsx"

### Run It

      python3 webex_license_count_cleaner.py

---

## Recommended Workflow

1. Fetch raw license data:

       python3 webex_license_counter.py

   Produces: `webex_licenses_YYYYMMDD_HHMMSS.csv`

2. Clean & widen the CSV:

       python3 webex_license_count_cleaner.py

   Produces: `LICENSE_REPORT.xlsx`

---

## Requirements

      pip install pandas requests ratelimit

---

## Security Notes
- No secrets or tokens are stored in these scripts.
- `WEBEX_ACCESS_TOKEN` must be exported as an environment variable.
- Organization ID lists must be populated manually and should not be committed.
