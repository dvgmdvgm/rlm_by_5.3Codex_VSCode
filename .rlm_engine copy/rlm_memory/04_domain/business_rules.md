# 🎯 Business Rules — Scenica

> **Imported from**: `Ideas.md`, `PROJECT_CONTEXT.md`
> **Date**: 2026-02-06
> **Modified**: 2026-02-27 (Translated to EN)

---

## Platform Concept

**Scenica** — marketplace for artists and employers in the entertainment industry.
Positioning: **"Uber for show business"** — an information intermediary, not a party to the transaction.

---

## User Roles

### 🕵️‍♂️ Employer
- Creates jobs (vacancies)
- Browses the artist catalog
- Accepts/rejects applications
- Signs contracts

### 💃 Artist
- Fills out a portfolio (genre, height, video, etc.)
- Applies to jobs
- Signs contracts
- Receives ratings and reviews

---

## Contract Lifecycle

```
Job → Application (new) → Viewed (viewed) → Accepted (accepted) 
→ Employer Signature → Artist Signature → CONTRACT ACTIVE
```

### Important Rules:

1. **Frozen Conditions**: Upon application, the job's terms are copied into the `Application` record.
2. **Editing Lock**: Job conditions cannot be changed if there are any `accepted` applications.
3. **Double Signature**: A contract is valid only when both signatures are present.
4. **Timezones**: Saved at the time of signing for legal validity.

---

## Monetization (Roadmap)

### MVP (Current Stage)
- [x] Contact Blurring (hiding contact info)
- [ ] "Pricing" Page (placeholder)
- [ ] PDF Contract Generation
- [x] Ratings and Reviews

### Next Month
- [ ] Stripe Subscriptions
- [ ] Paid access to contact info (Business plan)

### Six Months
- [ ] Stripe Connect (Escrow / Secure transaction)
- [ ] 10% Transaction commission

---

## Pricing Plans (Planned)

| Plan | Price | Features |
|------|-------|----------|
| **FREE** | $0 | Create jobs, blurred contacts |
| **BUSINESS** | $20-50/mo | Open contacts, advanced filters |
| **AGENCY** | $100+/mo | Excel export, multi-accounts |

### One-time Purchases
- Unlock Contact: $1-5
- Boost Vacancy: $5-15
- Email Blast: $50

---

## Legal Requirements

### GDPR / PIPL
- Consent checkbox at registration
- Data minimization (Passport → Stripe Identity)
- Server in Europe

### Disclaimers
- **Contracts**: "Provided as a template only. Not legal advice"
- **Terms of Use**: "Platform is not a party to any agreement between Users"

---

## User Retention

1. **Escrow (planned)**: Funds held by the platform → builds trust
2. **Blurring**: Hiding contact info until subscription → enables monetization
3. **Reputation**: Reviews and ratings → creates a "digital work record" for the artist
