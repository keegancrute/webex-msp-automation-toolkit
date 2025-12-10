#!/usr/bin/env python3

"""
Clean Webex Overages CSV Files

This script processes raw Webex overages CSVs by fixing misaligned customer
names, extracting customer name and org ID, and generating a clean output file.

Usage:
    python3 clean_webex_overages.py
"""


import pandas as pd
import csv
import os
from datetime import datetime

def clean_csv(input_filename):
    """Preprocess CSV to fix misaligned customer names and standardize output."""
    
    if not os.path.exists(input_filename):  # Ensure the file exists
        raise FileNotFoundError(f"❌ File not found: {input_filename}")

    # Auto-generate cleaned filename with timestamp to avoid duplicates
    today = datetime.today().strftime("%B_%d_%H-%M")  # Example: "February_25_14-30"
    output_filename = f"cleaned_overages_{today}.csv"

    with open(input_filename, "r", encoding="utf-8") as infile, open(output_filename, "w", encoding="utf-8", newline="") as outfile:
        reader = csv.reader(infile, delimiter=",", skipinitialspace=True)
        writer = csv.writer(outfile, quotechar='"', delimiter=",", quoting=csv.QUOTE_MINIMAL)  

        for row in reader:
            if len(row) < 2:  # Skip empty or invalid rows
                continue
            
            # Ensure that customer name and Org ID are correctly aligned
            fixed_row = fix_misaligned_row(row)

            # Only keep "Customer Name" and "Customer Org ID"
            cleaned_row = fixed_row[:2]
            writer.writerow(cleaned_row)

    return output_filename

def fix_misaligned_row(row):
    """Fixes cases where the Customer Name column is split due to commas."""
    if len(row) > 6:
        # If too many columns, assume first columns are part of customer name
        customer_name = " ".join(row[:-5])  # Merge everything before the Org ID into the name
        org_id = row[-5]  # Assume Org ID is the 5th column from the end
        return [customer_name, org_id]  # Return fixed columns
    elif len(row) < 6:
        # If too few columns, add empty placeholders
        return row + [""] * (6 - len(row))
    return row

def load_csv(filename):
    """Loads the cleaned CSV into pandas, extracting only Customer Name & Org ID."""
    try:
        df = pd.read_csv(filename, quotechar='"')  # Ensures quoted fields stay intact
        df = df.iloc[:, :2]  # Keep only the first 2 columns
        df.columns = ["Customer Name", "Customer Org ID"]  # Ensure proper naming
        df = df.drop_duplicates()  # Remove duplicate entries
        return df
    except Exception as e:
        raise ValueError(f"❌ Error loading CSV: {e}")

# ✅ Ask user for the file path
file_path = input("Enter the full path to the Overages CSV file: ")

try:
    # Process CSV and generate cleaned output
    cleaned_file = clean_csv(file_path)
    
    # Load cleaned CSV into pandas and display
    customer_data = load_csv(cleaned_file)
    
    print("✅ File cleaned successfully! Here are the first 5 rows:")
    print(customer_data.head())

    print(f"✅ Cleaned data saved as: {cleaned_file}")

except Exception as e:
    print(e)
