# Website Task Map – Athlete Data Integration (November 2025)

This document outlines the user-facing actions we plan to expose in the education portal and admin website. Each button/task points to a data workflow that now exists in code or documentation.

---

## 1. Education Portal (For Coaches & Parents)
| Button / Task | Purpose | Linked Resource |
| --- | --- | --- |
| **Understand MAP/MOT/AQUA** | Explain the three scoring systems and how they drive rankings. | `docs/README.md` (Points Systems section) |
| **How we build the athlete database** | Plain-language overview of registration/result matching. | `docs/Athlete_Data_Integration_Overview.md` |
| **Why we collect IC and guardian contacts** | Show benefits for team logistics, travel, and emergency access. | Section 5 of `docs/Athlete_Data_Integration_Overview.md` |
| **Registration update checklist** | Tell families what data they must confirm each season. | Create checklist in portal referencing SportEngine fields |

---

## 2. Admin Portal – Data Steward Tasks
| Portal Action | Description | Script / Workbook |
| --- | --- | --- |
| **Review unmatched registrations** | Open latest `sportengine_unmatched_with_candidates*.xlsx` and approve/reject suggestions. | `temp_scripts/build_unmatched_sportengine_matches_*.py` outputs |
| **Promote approved matches** | Run the unified loader to insert/update athletes and aliases. | `temp_scripts/populate_candidate_matches.py` |
| **Check registration coverage** | Display count of total vs unmatched registrations. | `temp_scripts/count_unmatched_registrations.py` |
| **Sync aliases with database** | Ensure canonical fullname + aliases stay aligned after manual edits. | `temp_scripts/apply_alias_clusters_to_table.py` |
| **Export athlete contact list** | Filter athletes by event/age and export guardian contact sheet. | New admin UI feature; pulls from `athletes` table (fields documented in Handbook §5) |

---

## 3. Analytics & Reporting
| Button / Report | Purpose | Data Dependency |
| --- | --- | --- |
| **MAP/MOT Rankings by Age** | Show MAP/MOT scores for age clusters (e.g., 12–14). | Requires `athletes` with `BIRTHDATE`, `results` table scoring routines |
| **AQUA Points Leaderboard** | Compare performances internationally. | Same as above; uses AQUA formulas |
| **Team Selection Wizard** | Filter by age, club, or event and output roster with IC + guardians. | `athletes` contact fields and `results` linkages |
| **Recording manual overrides** | Log alias or club corrections. | Append notes to `WHAT_S_NEXT.md` for audit trail |

---

## 4. Development Checklist for UI Integration
1. **Surface status cards** in the admin dashboard:
   - “Registrations mapped” (value from `count_unmatched_registrations.py`)
   - “Review queue” (link to latest `sportengine_unmatched_with_candidates_*.xlsx`)
2. **Task buttons** trigger documentation or scripts:
   - For docs: open the Markdown-rendered page inside the portal.
   - For scripts: show the exact command from `SESSION_START.md` so staff can copy/paste.
3. **Roster export button** uses the new athlete schema (IC, guardians, alias coverage).
4. **Education portal content** pulls key paragraphs from the layman overview to keep messaging consistent.

---

Keep this task map in sync with future rounds of matching or UI development. Any new workflow should appear here, linked either to a script, a workbook, or a documentation page.***

