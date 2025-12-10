# Webex PSTN Automation Toolkit

This folder contains a set of Python automation tools for managing Webex Calling PSTN configurations in multi-tenant MSP and partner environments.  
The toolkit supports large-scale discovery, auditing, and migration of PSTN providers across many Webex organizations.

Each script uses the Webex Partner API and reads the access token from the `WEBEX_ACCESS_TOKEN` environment variable.

---

## Overview of Included Scripts

### 1. `webex_pstn_discovery.py` — PSTN Option Discovery

Discovers PSTN connection options for every organization and location under a partner account.

**Key Capabilities**

- Activates each organization before querying data  
- Retrieves all locations per organization  
- Fetches available PSTN connection options for each location  
- Saves raw PSTN responses, provider-filtered results (optional), and location inventories  

**Provider Filtering**

Filtering is keyword-based. Set an environment variable such as:

    export PSTN_PROVIDER_KEYWORD="calltower"

If not set, it defaults to `veracity` for backward compatibility.

---

### 2. `webex_pstn_auditor.py` — PSTN Configuration Auditor

Audits existing PSTN assignments for a list of organizations.

**Key Capabilities**

- Activates each organization  
- Retrieves all locations  
- Pulls current PSTN connection data per location  
- Produces structured JSON audit output  
- Handles Webex rate limits with retry/backoff logic  

**Logs include**

- HTTP status codes  
- API tracking IDs  
- Response bodies  
- Success and failure lists  

Use this before migrations, during troubleshooting, or to validate customer environments.

---

### 3. `webex_pstn_flipper.py` — Bulk PSTN Migration Tool

Performs mass PSTN migrations across multiple partner-managed organizations.

**Key Capabilities**

- Loops through all organizations defined in `ORG_IDS`  
- Retrieves all locations for each organization  
- Attempts multiple PSTN connection option IDs (`PSTN_OPTION_ID_1`, `PSTN_OPTION_ID_2`, `PSTN_OPTION_ID_3`)  
- Logs location inventories, PSTN update results, and full JSON output  

Use this when migrating many customers to a new PSTN provider in a controlled batch process.

---

### 4. `webex_pstn_swapper.py` — Single-Organization PSTN Migration

Updates PSTN settings for all locations in a single Webex organization.

**Key Capabilities**

- Activates the target organization  
- Retrieves all associated locations  
- Applies one PSTN option ID (`PSTN_OPTION_ID`)  
- Writes structured logs for discovery and update operations  

Use this tool for one-off migrations or targeted PSTN updates.

---

## Requirements

- Python 3.8+  

**Python libraries required**

- `requests`  
- `pytz` (for the auditor)  
- `ratelimit` (for the auditor)  

Install with:

    pip install requests pytz ratelimit

---

## Authentication

Set your Webex access token as an environment variable:

    export WEBEX_ACCESS_TOKEN="your_access_token_here"

Tokens must include appropriate **Webex API** scopes.

---

## Typical Workflow

1. **Discover PSTN options across all orgs**  
   - Run: `webex_pstn_discovery.py`

2. **Audit existing PSTN configurations**  
   - Run: `webex_pstn_auditor.py`

3. **Perform migration**
   - Bulk migration → `webex_pstn_flipper.py`  
   - Single-org migration → `webex_pstn_swapper.py`

---

## Notes

- All output folders are timestamped for traceability.  
- Connection option IDs (`PSTN_OPTION_ID`, etc.) must be supplied by the user.  
- The toolkit is provider-agnostic; any PSTN provider can be targeted.  
- These scripts were developed and used in real MSP production environments supporting hundreds of organizations.
