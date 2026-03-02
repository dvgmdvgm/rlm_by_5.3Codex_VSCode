# 🚀 DEPLOYMENT - Release and Infrastructure

> **Category**: 11_deployment  
> **Updated**: 2026-02-27
> **Modified**: 2026-02-27 (Translated to EN)

---

## 📋 Category Description

This category contains information regarding system deployment and infrastructure:
- Environment definitions (development, staging, production).
- Configuration parameters for different system modules.
- Descriptions of required secrets and credentials (not the values themselves!).
- Step-by-step deployment and rollback procedures.

---

## 📂 Files in this Category

| File | Description | Updated |
|------|-------------|---------|

---

## 🔍 Search Triggers

- "What is the procedure for deploying to [environment]?"
- "Which environments are currently configured?"
- "What environment variables are required for [feature]?"
- "List all necessary credentials for the system."
- "Show the configuration for [service]."

---

## ⚠️ CRITICAL SAFETY RULE

**NEVER store raw secret values, passwords, or API keys in these files!**

Document requirements only:
- ✅ **DO**: "We require a client secret for Google OAuth 2.0."
- ❌ **DON'T**: "GOOGLE_OAUTH_SECRET=abc123xyz"
