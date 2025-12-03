# Work In Progress

**Last Updated:** 2025-12-03 (Session 30)

---

## Current Status

**DATABASE:** Bi-directional sync between Supabase (cloud) and SQLite (local)
- **7,650 athletes** in SQLite, syncing to Supabase
- **55,703 results**, **48 meets**, **193 clubs**, **4 coaches**
- **93.5% email coverage** for 2026 registration

**HOSTING:** Both apps deployed to Vercel
- `mas-registration` - Registration portal
- `mas-analytics` - Analytics dashboard

**MOT Base Times:** 151 records (34 events, ages 15-23)
**USA Reference Data:** 30,027 athletes, 221,321 period results, 24,928 delta records

---

## IMMEDIATE: Configure DNS at Exabytes

**Add these CNAME records in Exabytes DNS for malaysiaaquatics.org:**

| Type | Name | Value |
|------|------|-------|
| CNAME | `register` | `703340cc0a6babe6.vercel-dns-017.com` |
| CNAME | `analytics` | `578dca52ee593a72.vercel-dns-017.com` |

After DNS propagates (5-30 min), both subdomains will be live.

---

## Bi-Directional Database Sync

**Architecture:** SQLite (Admin Panel) <-> Supabase (Registration Portal)

**Sync Commands:**
```bash
python scripts/sync_databases.py status   # Check sync status
python scripts/sync_databases.py push     # Push SQLite -> Supabase
python scripts/sync_databases.py pull     # Pull Supabase -> SQLite
python scripts/sync_databases.py backup   # Backup both databases
```

**Auto-sync:** Admin panel now auto-syncs athlete updates to Supabase.

**TODO:** Add `updated_at` column to Supabase (run in SQL Editor):
```sql
ALTER TABLE athletes ADD COLUMN updated_at TIMESTAMPTZ DEFAULT NOW();
UPDATE athletes SET updated_at = NOW() WHERE updated_at IS NULL;
```

---

## Current Goal: 2026 Registration System

**Completed:**
- [x] Deploy registration portal to Vercel (`mas-registration`)
- [x] Deploy analytics app to Vercel (`mas-analytics`)
- [x] Configure custom domains in Vercel
- [x] Set up bi-directional database sync

**Remaining Tasks:**
- [ ] Configure DNS at Exabytes (CNAME records above)
- [ ] Wire registration portal to Supabase (Enter button -> real DB lookup)
- [ ] Set up email sending (Gmail or SendGrid)
- [ ] Research RevenueMonster payment API
- [ ] Add Code of Conduct text with signature tracking

---

## Recently Completed (Session 30)

- Deployed both apps to Vercel (mas-registration, mas-analytics)
- Set up GitHub -> Vercel auto-deploy pipeline
- Created bi-directional sync system (`scripts/sync_databases.py`)
- Added Supabase sync to admin panel athlete updates
- Added `updated_at` column to SQLite athletes table
- Updated handbook with DNS configuration and Vercel details
- Fixed TypeScript build exclusion for registration-portal

---

## Previously Completed (Session 29)

- Fixed MOT age 23 data (was showing 00:00.00 - table had no age 23 rows)
- Added MOT methodology overview to landing page with dual data source explanation
- Created printable MOT PDF with dynamic generation from database
- Script: `python scripts/generate_mot_pdf.py` regenerates PDF after podium updates

---

## TODO (Not Started)

### High Priority
- [ ] Upload SEAG_2025_ALL.xlsx to database
- [ ] Upload 2024/2025 SEA Age and AYG results
- [ ] Fix `records` table import to Supabase (75 rows failed)

### Medium Priority
- [ ] Add ability to ADD aliases (not just edit existing)
- [ ] Add passport type information to athletes table

---

## Deferred

- **Relay Events:** Skipped in all uploads (lack age group data). Design relay storage later.
- **TypeScript Error:** meet-management.tsx compilation error - not blocking

---

## Personal Reminders

### Malaysia TD Work
- Course letter review
- Foundations required before Level 1
- Schedule: KL end of Jan Foundations, Feb Level 1 (Feb 10-13)
- MIAG meet: Feb 5-8th

### SEA Age Selection
- Remind this is their only qualifying opportunity
- If changing criteria, announce before Jan 1st
- Ask athletes for confirmation FIRST, then fill event programs
- Run proposal by Marylin and Nurul

---

## Post-Upload Checklist

After loading results:
1. `python scripts/check_duplicate_results.py`
2. `python scripts/check_duplicate_athletes.py`

---

*For detailed history, see: `docs/Malaysia Swimming Analytics Handbook.md`*
