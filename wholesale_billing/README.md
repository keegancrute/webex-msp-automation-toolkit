# Webex Wholesale Billing Tools

This folder contains automation utilities for retrieving and processing Webex Wholesale Billing usage reports for the previous month. These tools support MSP and partner workflows where engineers regularly need:

- Automated access to Webex Wholesale Billing data
- Consistent and repeatable report generation
- Normalized CSV formatting suitable for finance, operations, and leadership
- An auditable workflow that mirrors Webex’s billing report lifecycle

The primary script in this folder performs the entire workflow end-to-end.

---

## 1. webex_wholesale_billing_report.py — Automated Monthly Billing Report

Retrieves, validates, downloads, and transforms Webex Wholesale Billing reports for the previous month.

### What It Does

- Determines the previous billing period
- Checks for an existing report (COMPLETED / IN_PROGRESS / REQUESTED)
- Creates a new report if necessary
- Polls until the report reaches COMPLETED
- Downloads the CSV using the temporary download URL
- Applies a transformation that:
  - Removes the first four columns
  - Extracts usage from Column K (index 6 after trimming)
  - Computes BILLABLE_UNITS = ceil(ColumnK / days_in_last_month)
  - Appends BILLABLE_UNITS as the final column

### Output Files

<Month>-<Year>-Wholesale-Usage_<timestamp>_ORIGINAL.csv  
<Month>-<Year>-Wholesale-Usage_<timestamp>.csv  

- The _ORIGINAL file is the raw Webex export.  
- The final CSV contains the normalized, billable-unit–ready dataset.

---

## Environment Variables

The script requires Webex OAuth credentials to be supplied via environment variables:

WEBEX_CLIENT_ID="xxxx"  
WEBEX_CLIENT_SECRET="xxxx"  
WEBEX_ACCESS_TOKEN="xxxx"  
WEBEX_REFRESH_TOKEN="xxxx"  

Credentials are read at runtime and are not stored in the source code.

---

## Dependencies

Install the required Python packages:

pip install pandas numpy requests

---

## Usage

Run the script:

python3 webex_wholesale_billing_report.py

The script will:

1. Determine the previous month’s billing period
2. Ensure a report exists and is completed
3. Download the original CSV export
4. Generate a transformed CSV with BILLABLE_UNITS appended

Both the original and transformed CSV files will be written to the current working directory.
