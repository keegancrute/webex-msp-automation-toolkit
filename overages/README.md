# Webex Overages Tools

This folder contains automation utilities for cleaning Webex overage CSVs and generating full overage reports across multiple customer organizations. These tools support MSP and partner workflows where engineers must routinely:

- Cleans and normalizes Webex overage CSV exports
- Activate customer organizations programmatically
- Retrieve license consumption data
- Compute overages and utilization
- Produce clean, human-readable Excel reports

Each script operates independently, and the pipeline script can run the entire workflow end-to-end.

---

## 1. clean_webex_overages.py — Raw Overage CSV Cleaner

Prepares raw Webex overage CSV files for automation by fixing misaligned rows, normalizing customer names, and extracting `Customer Name` + `Org ID`.

### What It Does
- Corrects structural inconsistencies such as multi-column customer names
- Ensures `Customer Name` and `Customer Org ID` are aligned
- Produces a cleaned, timestamped CSV
- Removes duplicates and preserves only the required two columns

### How It Works
You will be prompted to provide a raw Webex overages CSV.  
The script outputs:

    cleaned_overages_<timestamp>.csv

### Run It
    python3 clean_webex_overages.py

### Output Includes
- Cleaned customer name + org ID pairs
- Provides a preview of processed records for validation

---

## 2. webex_overages_cleaner.py — Full Overage Pipeline

Runs the complete overages workflow:

1. Cleans the raw CSV  
2. Activates each organization via `/v1/organizations/{orgId}`  
3. Retrieves all license objects via `/v1/licenses`  
4. Calculates license utilization metrics, including overage and underuse  
5. Generates a color-coded Excel overage report

### What It Does
- Identifies overused, underutilized, and fully utilized licenses
- Produces structured JSON summaries
- Builds an Excel `.xlsx` file with conditional formatting
- Outputs:
      cleaned_overages_<timestamp>.csv
      successful_orgs_<timestamp>.json
      webex_org_details_<timestamp>.csv
      Webex_License_Overages_<timestamp>.xlsx

### How It Works
The script loads your Webex OAuth token from the environment:

    export WEBEX_ACCESS_TOKEN="your_token_here"

You provide the raw CSV path at runtime and the rest executes automatically.

### Run It
    python3 webex_overages_cleaner.py

### Output Includes
- Cleaned CSV
- License retrieval results
- JSON mappings of org → license objects
- Excel overage report with highlighting:
      Red  = overused
      Blue = underutilized

---

## Recommended Workflow

1. Clean the raw CSV (optional if running the full pipeline):

       python3 clean_webex_overages.py

2. Run the end-to-end overage pipeline:

       python3 webex_overages_cleaner.py

---
