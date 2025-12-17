# Webex MSP Automation Toolkit

The **Webex MSP Automation Toolkit** is a production-oriented collection of Python-based tools designed to automate large-scale operational workflows for **Webex Calling**, **Webex Control Hub**, **PSTN discovery and migration**, **OAuth lifecycle management**, **license and overage auditing**, and **Wholesale Billing**.

This repository was developed to support **multi-tenant MSP and Cisco partner environments**, where manual administration does not scale and operational accuracy is critical.

Each module is independent, script-friendly, and modeled after **real-world workflows used in production environments** supporting hundreds of customer organizations.

---------------------------------------------------------------------

## Overview

This toolkit was built to replace repetitive, error-prone administrative tasks with **repeatable, auditable automation** capable of operating safely at scale.

It has been used to support:
- PSTN provider discovery and migration audits
- License inventory and overage reporting for billing and finance teams
- OAuth token lifecycle management for long-running integrations
- Configuration validation across Webex organizations and locations

The design prioritizes **safety, observability, and scalability** over one-off scripting.

---------------------------------------------------------------------

## Features at a Glance

- Automated Webex OAuth token lifecycle management
- PSTN discovery, auditing, and bulk migration tooling
- License retrieval and wide-format Excel reporting
- Overage cleanup, analysis, and report generation
- Wholesale Billing monthly report automation
- Reliable retry and backoff logic for Webex API calls
- Timestamped outputs for traceability and auditing
- Environment-variable-based credential handling

---------------------------------------------------------------------

## Repository Structure

    webex-msp-automation-toolkit/
      licenses/           - License retrieval + wide-format reporting tools
      oauth/              - Multi-tenant OAuth token refresh automation
      overages/           - Overage CSV cleaning + full overage pipeline
      pstn/               - PSTN discovery, auditing, migration utilities
      wholesale_billing/  - Automated monthly billing report tooling
      README.md           - This file

---------------------------------------------------------------------

## Module Summary

### licenses/
Tools for retrieving license inventories across customer organizations and generating clean, wide-format Excel reports suitable for billing, audits, and capacity planning.

### oauth/
A multi-tenant OAuth credential management system that refreshes tokens, writes updated credential bundles, and logs all refresh activity for traceability and auditing.

### overages/
A complete overage-processing pipeline that cleans Webex CSV exports, activates organizations, retrieves license data, computes utilization and overages, and generates Excel reports.

### pstn/
Tools for PSTN discovery, PSTN configuration auditing, and bulk or single-organization PSTN migrations using Webex Calling PSTN APIs.

### wholesale_billing/
Automates the creation, polling, downloading, and transformation of Webex Wholesale Billing reports for the previous billing cycle.

---------------------------------------------------------------------

## How the Toolkit Works (High-Level)

Most scripts in this repository follow a consistent operational pattern:

1. Authenticate using a Webex Partner OAuth access token
2. Activate the target customer organization for API access
3. Retrieve organization-level resources (locations, numbers, licenses)
4. Perform scoped operations (discovery, audit, validation, or migration)
5. Export structured outputs (JSON, CSV, Excel) for review or downstream use

This approach ensures predictable behavior and minimizes API failures when operating at scale.

---------------------------------------------------------------------

## Scale & Safety Considerations

These tools were designed to operate across hundreds of customer organizations and include:

- Explicit organization activation before querying data
- Provider keyword filtering to prevent unintended configuration changes
- Read-only audit modes for validation prior to migration
- Structured, timestamped outputs for verification and rollback planning

---------------------------------------------------------------------

## Requirements

This toolkit runs on Python 3.x and uses the following libraries:

- requests
- pandas
- numpy
- openpyxl
- ratelimit (used by PSTN auditor)
- pytz (used by PSTN auditor)

Create a requirements.txt file and install dependencies with:

    pip install -r requirements.txt

---------------------------------------------------------------------

## Authentication & Environment Variables

Most scripts authenticate using Webex OAuth credentials. Set environment variables such as:

    WEBEX_ACCESS_TOKEN="your_access_token"
    WEBEX_REFRESH_TOKEN="your_refresh_token"
    WEBEX_CLIENT_ID="your_client_id"
    WEBEX_CLIENT_SECRET="your_client_secret"

Each module includes its own README documenting any additional required variables.

---------------------------------------------------------------------

## Getting Started

Clone the repository:

    git clone https://github.com/keegancrute/webex-msp-automation-toolkit
    cd webex-msp-automation-toolkit

Install dependencies:

    pip install -r requirements.txt

Then navigate to any module directory to review usage instructions and examples.

---------------------------------------------------------------------

## Contributing / Forking

This toolkit is intentionally modular. Engineers are encouraged to fork it, extend it, or integrate individual modules into their own automation pipelines.

---------------------------------------------------------------------

## License

This project is licensed under the MIT License.

