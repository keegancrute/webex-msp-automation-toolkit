# Webex MSP Automation Toolkit

Welcome to the Webex MSP Automation Toolkit — a collection of Python-based tools designed to streamline large-scale operational tasks for Webex Calling, Webex Control Hub, PSTN migrations, OAuth lifecycle management, licensing audits, and Wholesale Billing workflows.

This repository is built for engineers who support multi-tenant environments, managed service providers (MSPs), Cisco partners, and anyone interested in automating Webex administrative workloads at scale.

Each module is independent, script-friendly, and designed around real-world operational workflows used in production environments.

---------------------------------------------------------------------

## Features at a Glance

• Automated Webex OAuth token lifecycle management  
• PSTN discovery, auditing, and bulk migration tooling  
• License retrieval and wide-format license reporting  
• Overages cleanup, analysis, and Excel report generation  
• Wholesale Billing monthly report automation  
• Reliable retry/backoff logic for Webex API calls  
• Timestamped outputs for traceability and auditing  
• Environment-variable based credential handling  

---------------------------------------------------------------------

## Repository Structure

webex-msp-automation-toolkit/
  licenses/           - License retrieval + wide-format reporting tools
  oauth/              - Multi-tenant OAuth token refresh automation
  overages/           - Overage CSV cleaning + full overage pipeline
  pstn/               - PSTN discovery, auditing, migration utilities
  wholesale_billing/  - Automated monthly billing report tooling
  README.md           - This file

Below is a quick summary of each module:

### licenses/
Tools for retrieving license inventories across customer orgs and generating clean, wide-format Excel reports suitable for presentations or capacity planning.

### oauth/
A multi-tenant OAuth credential management system that refreshes tokens, writes updated credential bundles, and logs all refresh activity for auditing.

### overages/
A complete overage-processing pipeline: cleans Webex overage CSV exports, activates orgs, retrieves license data, computes utilization/overages, and generates Excel reports.

### pstn/
Tools for PSTN discovery, PSTN configuration auditing, and bulk or single-org PSTN migrations using Webex Calling PSTN APIs.

### wholesale_billing/
Automates creation, polling, downloading, and transformation of Webex Wholesale Billing reports for the previous month.

---------------------------------------------------------------------

## Requirements

This toolkit runs on Python 3.x and uses:

requests  
pandas  
numpy  
openpyxl  
ratelimit (for PSTN auditor)  
pytz (for PSTN auditor)

Suggestion: create a requirements.txt file and install everything at once with:

pip install -r requirements.txt

---------------------------------------------------------------------

## Authentication & Environment Variables

Most scripts use Webex OAuth credentials. Set environment variables like:

WEBEX_ACCESS_TOKEN="your_token"  
WEBEX_REFRESH_TOKEN="your_refresh_token"  
WEBEX_CLIENT_ID="your_client_id"  
WEBEX_CLIENT_SECRET="your_client_secret"

Each folder's README documents its required variables.

---------------------------------------------------------------------

## Why This Toolkit Exists

Managing large fleets of Webex customer organizations requires repetitive, high-volume API work:

• Fetching licenses across all customers  
• Activating orgs before API calls  
• Discovering PSTN options  
• Running PSTN migrations  
• Cleaning malformed Webex CSV exports  
• Refreshing OAuth tokens across several integrations  
• Generating monthly billing datasets  

This toolkit consolidates these workflows into clear, reusable automation modules.  
The design philosophy:

• Simple to run  
• Safe to customize  
• Easy to extend  
• Transparent in outputs and logs  

---------------------------------------------------------------------

## Getting Started

Clone the repository:

git clone https://github.com/keegancrute/webex-msp-automation-toolkit  
cd webex-msp-automation-toolkit

Install dependencies:

pip install -r requirements.txt

Then open any module folder to view its README and usage instructions.

---------------------------------------------------------------------

## Contributing / Forking

The toolkit is intentionally modular.  
Engineers can fork it, extend it, or integrate pieces into their own automation pipelines.

---------------------------------------------------------------------

## License

This project is licensed under the MIT License.
