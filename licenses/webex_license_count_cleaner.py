#!/usr/bin/env python3
"""
Webex License CSV Cleaner
-------------------------
- Reads a raw Webex license CSV file (exported from another script)
- Produces a wide-format Excel file where:
    * Each row = one organization (customer_name + org_id)
    * Each license type = two columns (total, consumed)

This script performs no calculations—it preserves the original values exactly.

Requirements:
    pip install pandas openpyxl
"""

import os
import pandas as pd


def clean_license_csv():
    # === USER INPUT ===
    input_file = "INPUT_LICENSES.csv"   # Replace with your CSV filename
    output_file = "LICENSE_REPORT.xlsx" # Replace with desired output filename

    if not os.path.exists(input_file):
        raise FileNotFoundError(
            f"Input CSV not found: {input_file}\n"
            f"Please update the 'input_file' variable at the top of this script."
        )

    # Load CSV
    df = pd.read_csv(input_file)

    # Keep only required columns
    df = df[["customer_name", "org_id", "license_name", "total_units", "consumed_units"]]

    # Build wide table manually
    rows = []
    for (customer, org), group in df.groupby(["customer_name", "org_id"]):
        row = {"customer_name": customer, "org_id": org}
        for _, r in group.iterrows():
            row[f"{r['license_name']} (total)"] = r["total_units"]
            row[f"{r['license_name']} (consumed)"] = r["consumed_units"]
        rows.append(row)

    # Convert into DataFrame
    wide = pd.DataFrame(rows)

    # Reorder columns for readability
    base_cols = ["customer_name", "org_id"]
    license_cols = sorted(
        set(c.rsplit(" (", 1)[0] for c in wide.columns if c not in base_cols)
    )

    ordered_cols = base_cols + [
        col for lic in license_cols
        for col in (f"{lic} (total)", f"{lic} (consumed)")
        if col in wide.columns
    ]

    wide = wide[ordered_cols]

    # Save output
    wide.to_excel(output_file, index=False)

    print(f"✅ Done. File written to: {output_file}")


if __name__ == "__main__":
    clean_license_csv()
