# Athlete Data Integration Overview (November 2025)

This brief explains, in plain language, how Malaysia Swimming Analytics now keeps athlete information, registrations, and competition results in sync. Use it when presenting to coaches, federation leadership, or anyone who needs a high-level picture of the system.

---

## 1. Why This Integration Matters
- **One record per swimmer:** We can confirm identity using full name, date of birth, national ID (IC/passport), and guardians—all stored once in the athlete table.
- **Faster team operations:** Selection lists automatically pull IC numbers, contact details, and club/state information—no retyping before travel or registration.
- **Actionable analytics:** Age-based rankings (MAP), pathway monitoring (MOT), and AQUA scoring all reference the same athlete IDs, eliminating inconsistency.
- **Registration continuity:** When a swimmer registers for a meet, we compare their entry to the existing athlete record and ask only for updates—not a full form.

---

## 2. Data Sources & What We Capture
| Source | Examples | Key fields captured |
| --- | --- | --- |
| **SportEngine registrations** (`SportEngine Data 08.11.25.xlsx`) | Club membership, meet entries, parent contacts | Birthday, gender, preferred/official names, guardians, phone/email, IC/passport |
| **Official results workbooks** (`MAS_2025_LCM_*`) | State meets, Malaysia Age Group Championships, SEA circuits | Full name as printed, birthdate, event, time, club/state, meet metadata |
| **Manual alias review** (`alias_logic_matches.xlsx`) | Variations such as `GOH, Louise Q` vs `LOUISE GOH, Qi Zheng` | Canonical fullname, additional aliases for future matching |

---

## 3. How We Match Registrations to Results
1. **Normalise** all dates to `YYYY.MM.DD` and strip IC digits to preserve leading zeros.
2. **Cluster aliases** so every swimmer has one “canonical” fullname plus alternate spellings.
3. **Generate review files** (e.g. `sportengine_unmatched_with_candidates_round2.xlsx`) that show:
   - Registration row (first name, last name, birthday)  
   - Candidate result rows that share the same birthday and gender  
   - Match details (first name match, last name match, or both) with confidence %
4. **Approve matches** and run the unified loader, which:
   - Inserts a new athlete record (or updates aliases if the athlete exists)
   - Appends to the `FullyPopulatedAthletes` ledger
   - Writes the assigned `table_id` back into the SportEngine workbook

Repeat until the unmatched registration count is within the acceptable threshold.

---

## 4. Fields We Now Maintain Per Athlete
- `FULLNAME` – Longest, slash-free variant used in official results
- `FIRSTNAME`, `LASTNAME`, `Preferred Name`, `Memb. Middle Initial`
- `BIRTHDATE` (`YYYY.MM.DD`) + original `Birthday` for audit
- `IC` and `AcctIC` (digits only), preserving leading zeros
- Guardian names, phones, and emails for fast roster communication
- Club, state, and location data for meet logistics
- `athlete_alias_1/2` – Stored directly on the athlete record for future matching

All of these live in the `athletes` table and are mirrored in the `FullyPopulatedAthletes` worksheet for transparency.

---

## 5. Impact on Team Selection & System Management
- **Selection rosters:** Build filtered lists (by age, event, rankings) and export contacts instantly.
- **MAP/MOT/AQUA scoring:** Every result links to a verified athlete, so pathway analytics stay accurate.
- **Meet registration:** Swimmers confirm existing details instead of filling repeat forms; admins monitor who still needs updates.
- **Education portal & task lists:** Website buttons can link directly to curated tasks (e.g., “Review unmatched registrations” or “Approve alias suggestions”) using the new review workbooks.

---

## 6. Suggested Talking Points for Presentations
- Begin with the “one record per swimmer” story—show before/after mismatch examples.
- Highlight the round-based review files as proof of due diligence.
- Demonstrate how MAP/MOT/AQUA outputs consume the same athlete IDs.
- Tie roster selection to the guardian contact fields for operational efficiency.
- Close with the remaining backlog (`count_unmatched_registrations.py`) and next result folders slated for matching.

---

For technical implementation details, cross-reference the **Developer Handbook (Section 4 & 6)**. Keep this overview in sync whenever the matching workflow or data sources change.

