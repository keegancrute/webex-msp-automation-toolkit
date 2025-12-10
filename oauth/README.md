# Webex OAuth Token Refresher  
### Multi-Tenant OAuth Credential Vault & Automated Token Lifecycle Manager

This module provides a centralized system for managing **multiple Webex OAuth integrations** across different organizations or applications.  
It securely stores credentials, automatically refreshes OAuth access/refresh tokens, writes new secrets to timestamped output files, and logs all activity for audit and troubleshooting.

This tool was designed for **MSP, Cisco partner, and multi-org automation environments**, where teams frequently manage several Webex integrations simultaneously.

---

## 🚀 Features

- **Multi-tenant OAuth support** (any number of Webex integrations)
- **Automatic access + refresh token rotation**
- **Uses `/v1/access_token` Webex API endpoint**
- **Integration-based success/failure logging**
- **Timestamped token output files** for historical tracking
- **Graceful handling of missing or invalid secrets**
- **Script-friendly JSON structure** for downstream automation
- **No secrets committed to git** (templates only)

---

## 📁 Project Structure

```
oauth/
├── token_updater.py                # Main automation script
├── tokens_master_template.json     # Template for per-org credentials (no secrets)
├── tokens_template.json            # Example output format
├── logs_template.json              # Example log format
├── access_tokens/                  # Output: tokens_<timestamp>.json
├── token_logs/                     # Output: logs_<timestamp>.json
└── README.md                       # You're reading it
```

The real secrets live in **tokens_master.json**, which is intentionally **not committed**.

---

## 🔧 How It Works

### 1. You create a private file:

```
tokens_master.json
```

This file contains **all organizations’ OAuth integration credentials**, in this format:

```json
{
  "Webex Integration 1": {
    "client_id": "YOUR_CLIENT_ID",
    "client_secret": "YOUR_CLIENT_SECRET",
    "access_token": "refreshed_access_token_here",
    "refresh_token": "new_refresh_token_here",
    "scopes": "your_oauth_scopes_url_string",
    "date": "Month Day, Year",
    "status": "success"
  },
  "Webex Integration 2": {
    "client_id": "YOUR_CLIENT_ID",
    "client_secret": "YOUR_CLIENT_SECRET",
    "access_token": "refreshed_access_token_here",
    "refresh_token": "new_refresh_token_here",
    "scopes": "your_oauth_scopes_url_string",
    "date": "Month Day, Year",
    "status": "success"
  },
  "Webex Integration 3": {
    "client_id": "YOUR_CLIENT_ID",
    "client_secret": "YOUR_CLIENT_SECRET",
    "access_token": "refreshed_access_token_here",
    "refresh_token": "new_refresh_token_here",
    "scopes": "your_oauth_scopes_url_string",
    "date": "Month Day, Year",
    "status": "success"
  },
  "Webex Integration 4": {
    "client_id": "YOUR_CLIENT_ID",
    "client_secret": "YOUR_CLIENT_SECRET",
    "access_token": "refreshed_access_token_here",
    "refresh_token": "new_refresh_token_here",
    "scopes": "your_oauth_scopes_url_string",
    "date": "Month Day, Year",
    "status": "success"
  }
}
```

Each “integration entry” represents one Webex OAuth application (or customer org) to refresh.

---

### 2. Run the script:

```
python3 token_updater.py
```

The script will:

- Read `tokens_master.json`
- For each org:
  - POST to `https://webexapis.com/v1/access_token`
  - Exchange `refresh_token` → new tokens
  - Capture expiration metadata
  - Log the operation
- Write updated tokens into:

```
access_tokens/tokens_<timestamp>.json
```

And write an audit log:

```
token_logs/logs_<timestamp>.json
```

---

## 📜 Log Format (Example)

```json
[
  {
    "org": "example_org_1",
    "timestamp": "2025-06-30T14:17:35.509688",
    "status": "success",
    "response": {
      "access_token": "new_token_here",
      "expires_in": 1209599,
      "refresh_token": "new_refresh_token_here",
      "refresh_token_expires_in": 7774733,
      "token_type": "Bearer",
      "scope": "relevant_scope_here"
    }
  },
  {
    "org": "example_org_2",
    "timestamp": "2025-06-30T14:17:35.509688",
    "status": "success",
    "response": {
      "access_token": "new_token_here",
      "expires_in": 1209599,
      "refresh_token": "new_refresh_token_here",
      "refresh_token_expires_in": 7774733,
      "token_type": "Bearer",
      "scope": "relevant_scope_here"
    }
  },
  {
    "org": "example_org_3",
    "timestamp": "2025-06-30T14:17:35.509688",
    "status": "success",
    "response": {
      "access_token": "new_token_here",
      "expires_in": 1209599,
      "refresh_token": "new_refresh_token_here",
      "refresh_token_expires_in": 7774733,
      "token_type": "Bearer",
      "scope": "relevant_scope_here"
    }
  },
  {
    "org": "example_org_4",
    "timestamp": "2025-06-30T14:17:35.509688",
    "status": "success",
    "response": {
      "access_token": "new_token_here",
      "expires_in": 1209599,
      "refresh_token": "new_refresh_token_here",
      "refresh_token_expires_in": 7774733,
      "token_type": "Bearer",
      "scope": "relevant_scope_here"
    }
  }
]
```

Every refresh event is auditable.

---

## 🔐 Security Model

- **tokens_master.json must never be committed to Git.**  
- The repo includes `.gitignore` entries for:
  - `tokens_master.json`
  - `access_tokens/`
  - `token_logs/`
- All example files are templates with **no sensitive data**.
- The system provides natural versioning through timestamped outputs.

This design ensures credentials remain private while allowing the automation to operate reliably across many organizations.

---

## 📦 Installation

```
pip install requests
```

(Optional) Add a `requirements.txt`.

---

## 🧠 Typical Use Cases

This tool is ideal for:

- Managed service providers (MSPs)
- Cisco partners
- Teams with multiple Webex integrations
- Automation pipelines needing rotating OAuth credentials
- Internal tooling where multiple downstream scripts rely on updated tokens

---

## 🧰 Future Enhancements (optional)

- CLI targeting for specific orgs (`--org example_org_1`)
- Email/Slack notifications on failures
- AWS SSM / Azure Key Vault storage backend
- Encryption at rest (Fernet)
- GitHub Actions / cron automation

---

## 👤 Author

Maintained by **Keegan Crute**.  
Built for multi-tenant automation, OAuth lifecycle management, and Webex integration workflows at scale.

Feel free to fork, improve, or incorporate into your own automation platform.
