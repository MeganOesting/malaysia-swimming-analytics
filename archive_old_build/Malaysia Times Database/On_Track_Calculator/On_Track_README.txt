Right‑click the folder On_Track_Calculator and choose “Open with Code.”
Open Codex on the left of the VS screen
Tell Codex: “Read On_Track_README.txt”
Run command
cd C:\Users\megan\OneDrive\Documents\Malaysia On Track\On_Track_Calculator
python On_Track_Code.py
Remind me to save the code after every time you change/update the code
Remind me that ctrl+c is how i stop the code running in command center
Make a copy/backup of the code (snapshot the folder or copy On_Track_Code.py and templates/static).
Update this README with any new aliases or UX changes made today.

The page will read in workbooks directly downloaded from swimrankings.net and use their column format.  If we switch to being able to use the original meet manager output files, then we will need to tell the code where to find the relevant data.  

Optional (Flask CLI): set FLASK_APP=On_Track_Code.py then flask run

Keep On_Track_README.txt up to date with:
What the app does and how to run it.
Current UI flow (select meets on home; after submit, table shows; “Select Meets” button to reset).

TODO: Team/State display
Future UI will show both team code (3–5 letters) and state code (3 letters) in the table.
Format options:
Concatenated in one column: “TEAM STATE” or “TEAM (STATE)” or “TEAM/STATE”
Separate columns: “Team” and “State” (adds an extra column)
Data source:
Team code comes from TEAM_ALIASES mapping in On_Track_Code.py
State code remains the 3-letter code already resolved for the athlete
Implementation notes:
Update row builder in On_Track_Code.py to include state code alongside the current team value.
If concatenating: change the value inserted for the Team column to “TEAM (STATE)” and keep column count the same.
If adding a new column: update headers and CSS widths in templates/index.html, and adjust sortable column indices if needed.
Consider slightly tighter font/width for the combined Team/State cell if it gets crowded.
Styling:
Keep Team/State column at fixed ch-width (e.g., 7–9ch) if concatenated.
If separate columns, set Team ~5ch and State ~4ch; center State for readability.

On Track Calculator — Codex Session Guide

Purpose

Flask web app to analyze Malaysian swimming results against AQUA targets
Reads local Excel workbooks; no uploads
Sortable table with AQUA, On‑Track targets, differences, and meet attribution
How To Run

Python 3.9+
Optional venv:
python -m venv .venv
..venv\Scripts\activate
Install once:
pip install Flask pandas xlrd==1.2.0 openpyxl
Start: python On_Track_Code.py
Open: http://127.0.0.1:5000/
UI Overview

Header: title flanked by small MAS logos; meet logos row below
Filters (always visible under logos):
Meets: multi‑select
Gender: Male, Female (both combine)
State: 3‑letter code or “All States”
Events: multi‑select
Free: 50, 100, 200, 400, 800, 1500
Back: 50, 100, 200
Breast: 50, 100, 200
Fly: 50, 100, 200
IM: 200, 400
Include foreign swimmers: on/off
Results: Show all times | Show best times only (fastest per swimmer per event)
Apply Selection: compact button
Table: updates in place (no page change)
Columns (left → right)

Gender, Event, Name, Team, Age, Meet, Time, AQUA, Place, On Track Target Time, On Track AQUA, Difference
Notes:
Meet is an abbreviation: SUK24 (SUKMA 2024), MIA25 (MIAG 2025), MO25 (Malaysia Open 2025), SEAG25 (SEA Age 2025)
Place 1/2/3 highlighted (gold/silver/bronze)
Foreign swimmers show “(Non‑Malaysian)” after Name when included
Sorting

Click the icon under the header text to sort a column:
Time (first click asc)
Place (first click asc)
Difference (first click desc)
Age (first click asc)
Active column shows ▲/▼ and a subtle highlight; others show a neutral ◇
Default server sort: Place ascending (1, 2, 3…)
Data Sources (per sheet)

B: Gender (M/F)
C: Distance (e.g., 50)
D: Stroke (Fr/Bk/BR/Bu/Me)
E: Name
F: Birthdate (dd.mm.yyyy ‑ used for age)
I: Time (display string)
J: Time (seconds — optional/unused currently)
K: AQUA points (pre‑calculated; used directly)
M: Place
N: Meet date (dd.mm.yyyy ‑ age as of 31 Dec meet year)
Q: Team/Club/State text (mapped to a 3‑letter state code)
Calculations

Age = meet_year − birth_year (as of 31 Dec)
AQUA = value read directly from column K
On Track Target Time:
Podium_On_Track_Target_AQUA.xlsx, sheet “MOT Tables 25”
Key: Gender (A) + Event (B, e.g., “50 Free”) + Age (C) → value from column M
On Track AQUA:
Podium_On_Track_Target_AQUA.xlsx, sheet “AQUA POINTS”
Headers row 1; base times: row 2 (male), row 3 (female)
baseSec = seconds(base), tSec = seconds(On Track Target Time)
AQUA = int(1000 * (baseSec / tSec)^3)
Difference = AQUA − On Track AQUA
Meet Files (project root)

SUKMA 2024: SUKMA_2024_Men.xls, SUKMA_2024_Women.xls
MIAG 2025: MIAG_2025_Men.xls, MIAG_2025_Women.xls
Malaysia Open 2025: MO_2025_Men.xls, MO_2025_Women.xls
SEA Age 2025: SEA_Age_2025_Men.xls, SEA_Age_2025_Women.xls
Always required: Podium_On_Track_Target_AQUA.xlsx
Logos in static/: MAS_Logo.png, SUKMA_2024_Logo.png, MIAG_2025_Logo.png, MO_2025_Logo.png, SEA_Age_2025_Logo.png
Team/State Codes

TEAM_ALIASES in On_Track_Code.py maps many team/club/state strings to a 3‑letter state code
Examples: “Penang Amateur Swimming Associ” → PNG; “Wp Kuala Lumpur”/“WP Kuala Lumpur” → WPKL; “Pade‑Supersharkz Swimming Club” → SEL; “Persatuan Renang Amatur Trg” → TRG; “Pra Johor” → JHR
Add aliases by appending to TEAM_ALIASES; normalization collapses whitespace and lowercases
Foreign Swimmers

List in foreign_swimmers.txt (one name per line; normalization removes punctuation and collapses spaces)
“Include foreign swimmers” filter:
Off: rows removed
On: Name shows “(Non‑Malaysian)”
Sheet Selection Rules

Skipped sheets: names containing “Lap”, “Top Results”, “5000m”
Also skipped: relay patterns like “4x100”, “4 x 200” (but not general “x”)
Troubleshooting

Missing files: copy listed filenames to project root
.xls load fails: pip install xlrd==1.2.0
Port in use: set FLASK_RUN_PORT=5001 then flask run
End‑of‑Day Reminders

