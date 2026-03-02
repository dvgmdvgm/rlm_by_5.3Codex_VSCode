# 📖 Glossary — Scenica

> **Date**: 2026-02-06
> **Modified**: 2026-02-27 (Translated to EN)

---

## Roles

| Term | Description |
|------|-------------|
| **Artist** | Performer: dancer, acrobat, musician, etc. Creates a portfolio, applies for jobs |
| **Employer** | Client: agency, park, circus. Creates jobs, hires artists |

---

## Objects

| Term | Model | Description |
|------|-------|-------------|
| **Job** | `jobs.Job` | A job offer created by an employer |
| **Application** | `jobs.Application` | An artist's application for a job |
| **Contract** | — | An Application with the status `accepted` and both signatures provided |
| **Review** | `users.Review` | Feedback left after a contract is completed |
| **Notification** | `jobs.Notification` | System notification |

---

## Application Statuses

| Status | Meaning |
|--------|---------|
| `new` | New application, not yet viewed |
| `viewed` | Employer has viewed the application |
| `accepted` | Accepted, waiting for signatures |
| `rejected` | Rejected |

---

## Artist Genres

| Code | Name |
|------|------|
| `dancer_modern` | Dancer (Modern/Contemp) |
| `dancer_folk` | Dancer (Folk) |
| `acrobat` | Acrobat |
| `circus` | Circus Performer |
| `musician` | Musician |
| `vocalist` | Vocalist |
| `host` | Host/MC |
| `model` | Model |

---

## Business Terms

| Term | Description |
|------|-------------|
| **Blurring** | Hiding contact details until a subscription is paid |
| **Escrow** | Secure transaction (funds held on the platform's account) |
| **Frozen Fields** | Freezing job conditions at the time of application |
| **KYC** | Know Your Customer — user verification processes |
| **MRR** | Monthly Recurring Revenue — monthly income |

---

## UI Terms

| Term | Description |
|------|-------------|
| **Glass-card** | Semi-transparent card with a blur effect |
| **OLED Dark** | Theme with a deep black background (#0D0D0F) |
| **Bento-cards** | Grid-based card style (as seen in the dashboard) |
