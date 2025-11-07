# What's Next — November 2025 Roadmap

This file captures the live handoff plan. Update it at the end of every working session.

---

## ✅ Recent Progress
- Consolidated athlete data sources merged via `temp_scripts/rebuild_consolidated_athletes.py` → `consolidated_athlete_ID_rebuilt.xlsx`.
- `athlete_aliases` table created and seeded (`temp_scripts/setup_athlete_aliases.py`).
- Open records datasets (open SCM/LCM men & women) inserted with relay metadata.
- Admin upload flow surfaces detailed validation results (gender/nation/club mismatches, missing aliases).

---

## 🎯 Active Priorities
1. **Athlete Master Refresh**
   - Finalize a new loader that reads `consolidated_athlete_ID_rebuilt.xlsx` and repopulates `athletes` + `athlete_aliases` in a single deterministic pass.
   - Document any records that lack IC/birthdate so the owner can resolve them offline.

2. **Meet Upload QA (SUKMA focus)**
   - Continue testing men’s and women’s SUKMA files.
   - Record missing aliases in `temp_scripts/missing_aliases.txt` and resolve them via `athlete_aliases`.
   - Log nation or club overrides needed for future automation.

3. **Alias Management UX**
   - Design API endpoint + admin panel UI to add aliases without shell scripts.
   - Persist user decisions (alias → athlete mapping, nation overrides) for future conversions.

4. **Records & Reference Data**
   - Populate remaining record categories (age-group, single-age, SEA 61 relays) using new schema fields (`is_relay`, `team_entity`, `age_basis`).
   - Ensure record insertion scripts clear conflicting rows before reloading (unique constraint on `event_id`, `category_type`, `category_value`).

5. **Documentation & Handoff**
   - Keep `SESSION_START.md` and `Malaysia Swimming Analytics Handbook.md` in sync with actual workflows.
   - Note manual fixes (aliases, club/nation overrides) here or in `temp_scripts/missing_aliases.txt` before closing the session.

---

## 📝 Backlog / Future Considerations
- Build admin tooling for nation/club corrections during upload review.
- Expand conversion script to write audit logs (per file, per validation error).
- Evaluate migration path from SQLite to PostgreSQL once athlete/meet flows are stable.
- Confirm relay handling (team metadata) with upcoming SEA Age meet files.

---

## 📋 End-of-Session Template
When you finish a session, append a short note below this line:

```
[YYYY-MM-DD] What changed, outstanding blockers, next safe action.
```

Keep the next developer unblocked.




