# Work In Progress

**Last Updated:** 2025-12-02 (Session 27)

---

## Current Status

**DATABASE:** Now hosted on Supabase (cloud PostgreSQL)
- **7,650 athletes** (7,449 MAS + 201 foreign)
- **55,703 results** (competition times)
- **48 meets**, **193 clubs**, **86 events**
- **93.5% email coverage** (7,156 athletes have AcctEmail for 2026 registration contact)

**USA Reference Data:** 30,027 athletes, 221,321 period results, 24,928 delta records
**MOT Base Times:** 151 records (34 events, ages 15-23 for non-50m, 18+ for 50m)

**Infrastructure:**
- **Supabase:** Cloud database (PostgreSQL) - 341,054 rows migrated
- **Local SQLite:** Still available as backup at `malaysia_swimming.db`
- **Hosting:** Main site on Exabytes (WordPress), registration portal TBD (Vercel)

---

## Current Goal: 2026 Registration System

Build online registration system where parents can:
1. Receive email with personalized link(s) for their athlete(s)
2. Review pre-filled registration data
3. Update/confirm information
4. Pay registration fee
5. Submit

**Progress:**
- [x] Audit contact data coverage
- [x] Load AcctEmail from registration export (7,156 emails added)
- [x] Load missing athletes from registration data (3,393 new athletes)
- [x] Merge duplicate athletes (22 duplicates resolved)
- [x] Set up Supabase account and project
- [x] Migrate full database to Supabase (341,054 rows)
- [x] Create .env file with credentials
- [x] Create Vercel account for hosting
- [x] Build registration portal UI (registration-portal/)
- [x] Add Registration Admin tab to admin panel
- [x] Add Team Selection tab to admin panel (placeholder)
- [x] Registration portal: Find My Account flow with member lookup
- [x] Registration portal: Account holder type (self vs parent)
- [x] Registration portal: Member detail view with edit/confirm
- [x] Registration portal: Code of Conduct section by member type
- [x] Club contact data: Added club_email, club_admin_name to 9 clubs
- [x] Database cleanup: Fixed 3,371 UUID athlete IDs to numeric
- [ ] Wire registration portal to Supabase (Enter button → real DB lookup)
- [ ] Deploy to Vercel and connect subdomain
- [ ] Set up email sending
- [ ] Research RevenueMonster payment API (B002)
- [ ] Add actual COC text with signature tracking

**Subdomains Needed (on malaysiaaquatics.org):**
- `register.malaysiaaquatics.org` - Registration portal (Vercel)
- `analytics.malaysiaaquatics.org` - Analytics app (Vercel)

---

## Completed This Session (2025-12-02 - Session 27)

### Registration Portal - Full Flow Implemented
- [x] Moved Find My Account / Create New Account buttons to top (centered)
- [x] Account holder type selection: "Myself" vs "My child(ren) as parent/guardian"
- [x] Account lookup with Enter button (simulated for Karen Chong test account)
- [x] Member cards display: name (red), ID, birthdate, gender with Select button
- [x] Member detail view with editable fields (name, birthdate, gender, club, state)
- [x] Code of Conduct section based on member types:
  - Parent/Guardian CoC (when registering as parent)
  - Athlete CoC (when any member is athlete)
  - Coach CoC (when any member is coach)
  - Technical Official CoC (when any member is TO)
- [x] New member form with dropdowns (birthdate, state, club)

### Club Data Enrichment
- [x] Added `club_email` and `club_admin_name` columns to clubs table
- [x] Identified club emails being used as athlete AcctEmail
- [x] Populated 9 clubs with contact info:
  - PJMS Aquatic, Sea Dragon, ISKL, GC Swimming, Aqua Space
  - Istio, Kemaman, Pro Swim Excellent, H20 Swim Team

### Database ID Cleanup
- [x] Fixed 3,371 athletes with UUID-style IDs (from registration import)
- [x] Converted to sequential numeric IDs (4282-7652)
- [x] All athlete IDs now in range 1-7652 (no more 8-digit IDs)

---

## Completed Previous Session (2025-12-02 - Session 26)

### Registration Portal UI Built
- [x] Created `registration-portal/` as separate Next.js app
- [x] Registration form UI with main page styling (inline labels, checkboxes)
- [x] Phone country code dropdown (MY, SG, ID, TH, etc.)
- [x] Member registration: Type (Athlete/Coach/Technical Official), Discipline, Division
- [x] Disciplines: Swimming, Artistic Swimming, Open Water, Water Polo, Diving
- [x] Divisions: Open, Para, Masters

### Admin Panel - New Tabs Added
- [x] **Registration Management tab** - Dashboard with link to public registration portal
- [x] **Team Selection tab** - Placeholder with documented workflow

### Database Schema Created
- [x] `scripts/registration_schema.sql` - Full schema for registration system

### Documentation Updated
- [x] Handbook: Added Coach Certification Tracking (future feature)
- [x] Handbook: Added National Team Selection Panel (timeline-driven workflow)
- [x] Fixed TypeScript errors in admin panel

---

## Next Session Reminders

### Registration Portal - Continue Development
1. **Wire to Supabase** - Connect Enter button to actual database lookup
2. **Member detail edit flow** - Save changes when Confirm & Return clicked
3. **Payment integration** - Research RevenueMonster API (B002)
4. **Code of Conduct** - Add actual COC text with signature tracking
5. **Add new member** - Flow for adding members not in database

### Registration Flow Testing
- Test "Myself" flow (registering as coach/athlete/official)
- Test "Parent" flow (registering children)
- Test Create New Account flow
- Test mixed member types (athlete + coach on same account)

---

## Completed Previous Session (2025-12-01 - Session 25)

### 2026 Registration Data Preparation
- [x] Audited contact data coverage in database:
  - Before: 76 emails (1.9%), 1,987 phones (46.4%)
  - 29% of athletes had NO contact info
- [x] Loaded registration export `customexport (9).xlsx`:
  - Added `AcctEmail` column to athletes table
  - 3,777 existing athletes updated with AcctEmail
  - 3,393 new athletes inserted with full registration data
  - 78 duplicates in spreadsheet skipped
- [x] Merged 22 duplicate athlete pairs:
  - Kept record with results, copied missing fields from duplicate
  - 52 total fields merged (AcctEmail, IC, address, guardian info)
  - Deleted duplicate records after merge
- [x] Final database: 7,650 athletes, 93.5% with AcctEmail

### Supabase Cloud Database Setup
- [x] Created Supabase account and project "MalaysiaAquatics"
- [x] Created full database schema (22 tables):
  - Core: athletes, foreign_athletes, results, meets, events, clubs
  - Base times: aqua_base_times, map_base_times, mot_base_times, podium_target_times, canada_on_track
  - USA reference: usa_athlete, usa_raw_period_data, usa_delta_data
  - Supporting: states, coaches, records, nation_corrections, custom_field_definitions
  - New: registrations_2026 (for tracking registration status)
- [x] Exported all SQLite data to CSV (18 files)
- [x] Imported all data to Supabase via REST API:
  - 341,054 total rows imported
  - Only `records` table failed (75 rows) - foreign key issue, can fix later
- [x] Created `.env` file with Supabase credentials
- [x] Schema file: `scripts/supabase_migration.sql`
- [x] Import script: `scripts/import_to_supabase_api.py`

### 2026 Registration Strategy Document
- [x] Created `docs/2026_Registration_Strategy.md`:
  - Contact data analysis (93.5% email coverage now possible)
  - Personalized email link approach
  - Implementation phases (email campaign, alternate contact, public portal)
  - Portal features and pre-filled data fields
  - Payment integration requirements (RevenueMonster)
  - Admin dashboard requirements
  - Security considerations

---

## Completed Previous Session (2025-12-01 - Session 24)

### Athlete Panel Field Enhancements
- [x] Field data now shows as grey text inside input boxes
- [x] API call to fetch full athlete details on selection
- [x] "Update All Changes" button to save all modified fields at once
- [x] IC Number field restructured (5 boxes: YY, MM, DD, PB, ####)
- [x] Phone number fields with country code dropdown (28 countries)
- [x] Email validation with visual feedback
- [x] Address section restructured with postal_code and address_state

### Passport/IC Data Migration
- [x] Migrated 208 passport numbers from IC to passport_number field
- [x] Nation detection from passport format (195 athletes updated)
- [x] IC/Nation data cleanup (fixed malformed ICs, set remaining to MAS)
- [x] Final: 4,078 MAS + 201 foreign athletes, 0 without nation

---

## TODO (Not Started)

### High Priority - Registration System
- [ ] Create Vercel account for registration portal hosting
- [ ] Build registration portal frontend (Next.js)
- [ ] Set up email sending system (Gmail batched or SendGrid)
- [ ] Research RevenueMonster payment API (B002)
- [ ] Design admin dashboard for registration tracking

### High Priority - Data Uploads
- [ ] Upload SEAG_2025_ALL.xlsx to database (B003 - now unblocked)
- [ ] Upload 2024/2025 SEA Age and AYG results
- [ ] Fix `records` table import to Supabase (75 rows failed)

### Medium Priority
- [ ] Update app to use Supabase instead of SQLite
- [ ] Add ability to ADD aliases (not just edit existing)
- [ ] Add passport type information to athletes table

---

## Deferred Tasks

### Relay Events
**STATUS:** Relays intentionally SKIPPED in all uploads
- Relay results lack age group data needed for proper results table entry
- **TODO LATER:** Design relay storage (team-based? linked to athletes?)

### TypeScript Error
- [ ] Fix compilation error in meet-management.tsx - not blocking

---

## Infrastructure Summary

### Database Options
| Option | Location | Use Case |
|--------|----------|----------|
| **Supabase** | Cloud (Singapore) | Primary - registration + analytics |
| **SQLite** | Local file | Backup, offline development |

### Credentials (.env file)
- `SUPABASE_URL` - Project URL
- `SUPABASE_PUBLISHABLE_KEY` - API key for client access
- `SUPABASE_DB_PASSWORD` - Direct PostgreSQL access
- See `.env` file for full list (DO NOT commit to git!)

### Hosting Plan
| Component | Service | URL | Status |
|-----------|---------|-----|--------|
| Main website | Exabytes (WordPress) | malaysiaaquatics.org | Active |
| Registration portal | Vercel | register.malaysiaaquatics.org | UI built, not deployed |
| Analytics app | Vercel | analytics.malaysiaaquatics.org | Account created, code not deployed |
| Database | Supabase | bvmqstoeahseklvmvdlx.supabase.co | Active (341k rows) |
| Email | Gmail | malaysia.aquatics@gmail.com | Need to configure |
| Payments | RevenueMonster | TBD | Need to research |

### Registration Portal Files
| File | Purpose |
|------|---------|
| `registration-portal/` | Next.js app for public registration |
| `registration-portal/src/pages/index.tsx` | Main registration form |
| `scripts/registration_schema.sql` | Database schema for registration system |
| `src/admin/features/registration-management/` | Admin panel tab |
| `src/admin/features/team-selection/` | Team selection admin tab |

---

## Known Data Quality Notes

### Athletes with Birthdate Discrepancies
These athletes have different birthdates in different SwimRankings files:
- LOO, Jhe Yee
- Muhammad Irish D
- KOEK GELACIO, Amanda M
Will be corrected during 2026 registration.

### Athletes to Watch
| Name | Note |
|------|------|
| MU ZI LONG, Lewis | DSA Swimming Club, registered MAS but NOT eligible - confirm nation |
| Sarah Ignasaki | Female, NOT eligible to represent MAS - alert when found |

---

## Post-Upload Reminders

After loading results:
1. Run `python scripts/check_duplicate_results.py`
2. Run `python scripts/check_duplicate_athletes.py`

---

## Personal Reminders (Non-Code)

### Malaysia TD Work
- Course letter review - adjust if needed
- MUST TELL everyone: Foundations required before Level 1 (check skip requirements)
- Schedule through states: KL end of Jan Foundations, Feb Level 1 (Feb 10-13)
- MIAG meet: Feb 5-8th

### SEA Age Selection Criteria
- Remind SEA Age this is their only qualifying opportunity
- If changing criteria, announce before Jan 1st
- Proposed: A qualifiers ranked 1-3, then remaining B qualifiers ranked 1-3
- Ask athletes for confirmation FIRST, then fill event programs
- Open events go to top MAP point scorers (development priority)
- Run proposal by Marylin and Nurul

---
NOTE i asked eric and Magnus to give me comp place for Worlds world jrs adn WUGS, also i can note lead off times for relays from these meets, will be a manual entry
