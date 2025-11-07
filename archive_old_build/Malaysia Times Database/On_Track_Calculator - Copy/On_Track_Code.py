from flask import Flask, render_template, request
import os
import re
from datetime import datetime, date
import pandas as pd
from functools import lru_cache

app = Flask(__name__)

# Default Excel files used by the app (no uploads required)
MEN_FILE = "SUKMA_2024_Men.xls"
WOMEN_FILE = "SUKMA_2024_Women.xls"
AQUA_FILE = "Podium_On_Track_Target_AQUA.xlsx"

# Meets available for analysis (expand as needed)
AVAILABLE_MEETS = [
    {
        "id": "sukma2024",
        "label": "SUKMA 2024",
        "abbr": "SUK24",
        "men_path": MEN_FILE,
        "women_path": WOMEN_FILE,
    },
    {
        "id": "miag2025",
        "label": "MIAG 2025",
        "abbr": "MIA25",
        "men_path": "MIAG_2025_Men.xls",
        "women_path": "MIAG_2025_Women.xls",
    },
    {
        "id": "malopen2025",
        "label": "Malaysia Open 2025",
        "abbr": "MO25",
        "men_path": "MO_2025_Men.xls",
        "women_path": "MO_2025_Women.xls",
    },
    {
        "id": "seaage2025",
        "label": "SEA Age 2025",
        "abbr": "SEAG25",
        "men_path": "SEA_Age_2025_Men.xls",
        "women_path": "SEA_Age_2025_Women.xls",
    },
]

# Sheet filtering tokens and Excel helpers
# Skip obvious non‑result sheets; avoid single-letter tokens like 'x' which over‑match
SKIP_SHEET_TOKENS = ("lap", "top results", "5000m")

# Team/state aliases grouped by 3-letter code (easy to extend)
TEAM_ALIASES = {
    "PNG": [
        "Pulau Pinang",
        "Penang Amateur Swimming Associ",
    ],
    "WPKL": [
        "Wilayah Persekutuan",
        "Wp Kuala Lumpur",
        "WP Kuala Lumpur",
    ],
    "SEL": [
        "Selangor",
        "Pade-Supersharkz Swimming Club",
    ],
    "SWK": ["Sarawak"],
    "SBH": ["Sabah"],
    "JHR": [
        "Johor",
        "Pra Johor",
    ],
    "NSE": ["Negeri Sembilan"],
    "PRK": ["Perak"],
    "MLK": ["Melaka"],
    "PHG": ["Pahang"],
    "KEL": ["Kelantan"],
    "TRG": [
        "Terengganu",
        "Persatuan Renang Amatur Trg",
    ],
    "KED": ["Kedah"],
    "PER": ["Perlis"],
}

def _norm_team(s: str) -> str:
    if s is None:
        return ""
    s = str(s).lower().strip()
    # collapse internal whitespace
    s = " ".join(s.split())
    return s

TEAM_CODE_LOOKUP = {}
for code, names in TEAM_ALIASES.items():
    for name in names:
        TEAM_CODE_LOOKUP[_norm_team(name)] = code

# Foreign swimmers list (one name per line in project root)
FOREIGN_NAMES_FILE = "foreign_swimmers.txt"

def _norm_name(s: str) -> str:
    if s is None:
        return ""
    s = str(s).strip().lower()
    # remove punctuation and non-letters, keep spaces
    try:
        import re as _re
        s = _re.sub(r"[^a-z\s]+", " ", s)
    except Exception:
        pass
    # collapse internal whitespace
    s = " ".join(s.split())
    return s

@lru_cache(maxsize=1)
def load_foreign_names(path: str = FOREIGN_NAMES_FILE):
    names = set()
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    names.add(_norm_name(line))
    except Exception:
        pass
    return names


# Stroke mapping for event label
STROKE_MAP = {
    "FR": "Free",
    "BK": "Back",
    "BR": "Breast",
    "BU": "Fly",
    "ME": "IM",
}

# Event options exposed in the UI (initial subset)
EVENT_OPTIONS = [
    "50 Free",
    "100 Free",
    "200 Free",
    "400 Free",
    "800 Free",
    "1500 Free",
    "50 Back",
    "100 Back",
    "200 Back",
    "50 Breast",
    "100 Breast",
    "200 Breast",
    "50 Fly",
    "100 Fly",
    "200 Fly",
    "200 IM",
    "400 IM",
]


def iter_valid_sheets(workbook_path):
    try:
        xl = pd.ExcelFile(workbook_path)
    except Exception:
        return []
    valid = []
    for name in xl.sheet_names:
        lower = name.lower()
        if any(tok in lower for tok in SKIP_SHEET_TOKENS):
            continue
        # Skip relay sheets like "4x100", "4 x 200", etc.
        try:
            import re as _re
            if _re.search(r"\b\d\s*x\s*\d\b", lower):
                continue
        except Exception:
            continue
        valid.append(name)
    return valid


def _clean_key(s: str) -> str:
    if s is None:
        return ""
    return str(s).replace("\xa0", " ").strip().upper()


@lru_cache(maxsize=1)
def load_mot_targets_map(aqua_path=AQUA_FILE, sheet_name="MOT Tables 25"):
    """Load mapping (gender, event, age) -> target time string from MOT table.
    Expects data in columns A (gender), B (event), C (age), M (target time).
    """
    if not os.path.exists(aqua_path):
        return {}
    try:
        df = pd.read_excel(aqua_path, sheet_name=sheet_name, header=None)
    except Exception:
        return {}
    if df is None or df.empty:
        return {}
    mapping = {}
    # Iterate all rows; skip header-like or invalid rows
    for _, row in df.iterrows():
        g = _clean_key(row.get(0))
        ev = _clean_key(row.get(1))
        age = pd.to_numeric(row.get(2), errors='coerce')
        tgt = row.get(12)
        if not g or not ev or pd.isna(age) or tgt is None:
            continue
        try:
            age_i = int(age)
        except Exception:
            continue
        mapping[(g, ev, age_i)] = str(tgt).strip()
    return mapping


def _parse_duration_seconds(val):
    """Parse a duration into seconds. Supports:
    - Day fractions (<1 numeric => seconds)
    - Numeric seconds
    - Strings with ':' like mm:ss.xx or hh:mm:ss
    - Strings with comma decimals
    Returns float seconds or None.
    """
    if val is None:
        return None
    if isinstance(val, float) and pd.isna(val):
        return None
    # Numeric
    if isinstance(val, (int, float)) and not isinstance(val, bool):
        v = float(val)
        if 0 < v < 1:
            return v * 86400.0
        return v
    # String
    s = str(val).strip()
    if not s or s.upper() == "N/A":
        return None
    s = s.replace(",", ".")
    if ":" in s:
        parts = s.split(":")
        try:
            if len(parts) == 3:
                h = int(parts[0]); m = int(parts[1]); ss = float(parts[2])
                return h * 3600 + m * 60 + ss
            if len(parts) == 2:
                m = int(parts[0]); ss = float(parts[1])
                return m * 60 + ss
        except Exception:
            return None
    try:
        return float(s)
    except Exception:
        return None


@lru_cache(maxsize=1)
def load_aqua_points_maps(aqua_path=AQUA_FILE, sheet_name="AQUA POINTS"):
    """Return (male_map, female_map) mapping event header -> base seconds.
    Headers in row 1, male in row 2, female in row 3.
    """
    if not os.path.exists(aqua_path):
        return {}, {}
    try:
        df = pd.read_excel(aqua_path, sheet_name=sheet_name, header=None)
    except Exception:
        return {}, {}
    if df is None or df.empty:
        return {}, {}
    headers = df.iloc[0].tolist()
    male_row = df.iloc[1].tolist() if len(df) > 1 else []
    female_row = df.iloc[2].tolist() if len(df) > 2 else []
    male_map, female_map = {}, {}
    for i, h in enumerate(headers):
        key = _clean_key(h)
        if not key:
            continue
        m_base = _parse_duration_seconds(male_row[i]) if i < len(male_row) else None
        f_base = _parse_duration_seconds(female_row[i]) if i < len(female_row) else None
        if m_base is not None:
            male_map[key] = m_base
        if f_base is not None:
            female_map[key] = f_base
    return male_map, female_map

def extract_male_50_free_rows(workbook_path, max_sheets=None, selected_events=None, gender_filter="M", include_foreign=True, state_filter: str = ""):
    """
    Read up to `max_sheets` valid sheets from the men’s workbook and return rows
    for Gender, Event, Name (other columns blank) where:
      B == 'M' (male), C == 50 (distance), D == 'Fr' (stroke), E has a name.
    """
    rows = []
    sheets = iter_valid_sheets(workbook_path)
    used = 0
    for sheet in sheets:
        try:
            # header=None so B,C,D,E => cols 1,2,3,4
            df = pd.read_excel(
                workbook_path,
                sheet_name=sheet,
                header=None,
            )
        except Exception:
            used += 1
            if max_sheets and used >= max_sheets:
                break
            continue

        # Map columns by index
        colB = df.get(1)  # Gender
        colC = df.get(2)  # Distance
        colD = df.get(3)  # Stroke
        colE = df.get(4)   # Name
        colF = df.get(5)   # Birthdate (dd.mm.yyyy)
        colI = df.get(8)   # Time (Excel col I)
        colJ = df.get(9)   # Time in seconds (Excel col J) [not used yet]
        colK = df.get(10)  # AQUA points (Excel col K)
        colM = df.get(12)  # Place (Excel col M)
        colQ = df.get(16)  # Team/State (Excel col Q)
        colN = df.get(13)  # Meet date (dd.mm.yyyy)
        if colB is None or colC is None or colD is None or colE is None:
            used += 1
            if max_sheets and used >= max_sheets:
                break
            continue

        gender = colB.astype(str).str.strip().str.upper()
        distance = pd.to_numeric(colC, errors='coerce')
        stroke = colD.astype(str).str.strip().str.upper()
        name = colE.astype(str).str.strip()

        # Default events if not provided
        if not selected_events:
            selected_events = ["50 Free"]

        # Candidate mask: gender + has name + distance in allowed set
        mask = (
            (gender == str(gender_filter).upper()) &
            (name != "") &
            (distance.isin([50, 100, 200, 400, 800, 1500]))
        )
        def _extract_year(val):
            if pd.isna(val):
                return None
            # pandas Timestamp or python datetime/date
            if isinstance(val, (pd.Timestamp, datetime, date)):
                try:
                    return int(val.year)
                except Exception:
                    return None
            # Numeric: could be a year or Excel serial date
            if isinstance(val, (int, float)):
                # If looks like a year
                if 1900 <= int(val) <= 2100:
                    return int(val)
                # Try Excel serial (origin 1899-12-30)
                try:
                    ts = pd.to_datetime(val, unit='d', origin='1899-12-30', errors='coerce')
                    if pd.notna(ts):
                        return int(ts.year)
                except Exception:
                    pass
                return None
            # String parsing
            s = str(val).strip()
            # Try day-first parse like 14.05.2005
            ts = pd.to_datetime(s, dayfirst=True, errors='coerce')
            if pd.notna(ts):
                try:
                    return int(ts.year)
                except Exception:
                    return None
            # Fallback: regex for 4-digit year
            m = re.search(r"(19\d{2}|20\d{2})", s)
            if m:
                return int(m.group(1))
            return None

        if mask.any():
            for idx in df.index[mask]:
                # Event label from distance + stroke mapping for this row
                dist_val = distance.loc[idx]
                stroke_code = str(stroke.loc[idx]).upper() if idx in stroke.index else ""
                stroke_label = STROKE_MAP.get(stroke_code, "")
                try:
                    ev_label = f"{int(dist_val)} {stroke_label}" if stroke_label else ""
                except Exception:
                    ev_label = ""
                if ev_label and ev_label not in selected_events:
                    continue

                # Resolve team code from column Q (fallback: raw string)
                team_val = ""
                if colQ is not None and idx in colQ.index and pd.notna(colQ.loc[idx]):
                    raw = str(colQ.loc[idx]).strip()
                    team_val = TEAM_CODE_LOOKUP.get(_norm_team(raw), raw)
                # Optional state code filter (based on resolved team_val)
                if state_filter and str(team_val).upper() != str(state_filter).upper():
                    continue

                # Compute age as of Dec 31 of meet year: meet_year - birth_year
                age_val = ""
                try:
                    by = _extract_year(colF.loc[idx]) if colF is not None and idx in colF.index else None
                    my = _extract_year(colN.loc[idx]) if colN is not None and idx in colN.index else None
                    if by is not None and my is not None and 0 < my - by < 120:
                        age_val = str(my - by)
                except Exception:
                    age_val = ""

                # Time value as-is string from column I
                time_val = ""
                if colI is not None and idx in colI.index and pd.notna(colI.loc[idx]):
                    time_val = str(colI.loc[idx]).strip()

                # AQUA points from column K (precalculated)
                aqua_val = ""
                if colK is not None and idx in colK.index and pd.notna(colK.loc[idx]):
                    try:
                        # Prefer integer-looking string if numeric
                        v = colK.loc[idx]
                        if isinstance(v, (int, float)) and not isinstance(v, bool):
                            aqua_val = str(int(v))
                        else:
                            aqua_val = str(v).strip()
                    except Exception:
                        aqua_val = ""

                # Lookup On Track Target from MOT table (AQUA workbook sheet "MOT Tables 25")
                on_track_target = "N/A"
                try:
                    male_event_key = _clean_key(ev_label)
                    gender_key = str(gender_filter).upper()
                    age_i = int(float(age_val)) if age_val not in (None, "") else None
                    if age_i is not None:
                        mot_map = load_mot_targets_map()
                        on_track_target = mot_map.get((gender_key, male_event_key, age_i), "N/A")
                except Exception:
                    on_track_target = "N/A"

                # Compute On Track AQUA using base from AQUA POINTS and on_track_target seconds
                on_track_aqua = "N/A"
                try:
                    t_sec = _parse_duration_seconds(on_track_target)
                    male_map, female_map = load_aqua_points_maps()
                    base_sec = (male_map if gender_filter == "M" else female_map).get(_clean_key(ev_label))
                    if base_sec and t_sec and t_sec > 0:
                        on_track_aqua = str(int(1000.0 * (base_sec / t_sec) ** 3))
                except Exception:
                    on_track_aqua = "N/A"

                # Difference = AQUA - On Track AQUA (only when both numeric)
                diff_val = ""
                try:
                    a = None if aqua_val in (None, "", "N/A") else int(float(str(aqua_val)))
                    ota = None if on_track_aqua in (None, "", "N/A") else int(float(str(on_track_aqua)))
                    if a is not None and ota is not None:
                        diff_val = str(a - ota)
                except Exception:
                    diff_val = ""

                # Place from column M (prepopulated in sheets)
                place_val = ""
                if colM is not None and idx in colM.index and pd.notna(colM.loc[idx]):
                    place_val = str(colM.loc[idx]).strip()

                # Determine foreign status by name; optionally filter or label
                display_name = name.loc[idx]
                foreign_names = load_foreign_names()
                is_foreign = _norm_name(display_name) in foreign_names
                if is_foreign and not include_foreign:
                    continue
                if is_foreign:
                    display_name = f"{display_name} (Non-Malaysian)"

                rows.append([
                    ("Male" if str(gender_filter).upper()=="M" else "Female"),  # Gender
                    ev_label,           # Event
                    display_name,       # Name (with Non-Malaysian tag if applicable)
                    team_val,           # Team/State (mapped)
                    age_val,            # Age
                    time_val,           # Time
                    aqua_val,           # AQUA
                    place_val,          # Place
                    on_track_target,    # On Track Target Time
                    on_track_aqua,      # On Track AQUA
                    diff_val,           # Difference (AQUA - On Track AQUA)
                ])

        used += 1
        if max_sheets and used >= max_sheets:
            break
    return rows

@app.route('/', methods=['GET', 'POST'])
def index():
    # First visit (GET): show meet selection under logos.
    # After submit (POST): hide selection, show table, and add a 'Select Meets' button.
    if request.method == 'POST':
        # Allow meet selection to persist via either 'meets' or hidden 'selected_meet_ids'
        selected_ids = request.form.getlist('meets') or request.form.getlist('selected_meet_ids') or ['sukma2024']
        show_selection_form = False
    else:
        # Default to SUKMA selected; keep unified single-page filters always visible
        selected_ids = ['sukma2024']
        show_selection_form = False

    selected_meets = [m for m in AVAILABLE_MEETS if m['id'] in selected_ids]

    # Event filter (supports multiple)
    if request.method == 'POST':
        selected_events = request.form.getlist('events') or ["50 Free"]
    else:
        selected_events = ["50 Free"]

    # Gender filter (M/F; supports multiple)
    if request.method == 'POST':
        selected_genders = [g.upper() for g in request.form.getlist('genders')] or ["M"]
    else:
        selected_genders = ["M"]

    # Include foreign swimmers (default True)
    if request.method == 'POST':
        include_foreign = bool(request.form.get('include_foreign'))
    else:
        include_foreign = True

    # Results mode: 'all' (default) or 'best'
    if request.method == 'POST':
        results_mode = request.form.get('results_mode', 'all')
        if results_mode not in ('all', 'best'):
            results_mode = 'all'
    else:
        results_mode = 'all'

    # State filter (optional 3-letter code)
    if request.method == 'POST':
        state_filter = request.form.get('state_code', '').strip().upper()
    else:
        state_filter = ''

    # Validate required files for selected meets + AQUA (only when meets selected)
    missing_paths = []
    if selected_meets:
        required_paths = {AQUA_FILE}
        for m in selected_meets:
            if m.get('men_path'):
                required_paths.add(m['men_path'])
            if m.get('women_path'):
                required_paths.add(m['women_path'])
        missing_paths = [p for p in sorted(required_paths) if not os.path.exists(p)]

    # If selection is applied and required files are present, read 1 sheet
    rows = []
    if not show_selection_form and selected_meets:
        try:
            rows = []
            for meet in selected_meets:
                men_path = meet.get('men_path')
                women_path = meet.get('women_path')
                meet_code = meet.get('abbr') or meet.get('label')
                if men_path and os.path.exists(men_path) and "M" in selected_genders:
                    r_m = extract_male_50_free_rows(
                        men_path,
                        selected_events=selected_events,
                        gender_filter="M",
                        include_foreign=include_foreign,
                        state_filter=state_filter,
                    )
                    for rr in r_m:
                        rr.insert(5, meet_code)
                    rows += r_m
                if women_path and os.path.exists(women_path) and "F" in selected_genders:
                    r_f = extract_male_50_free_rows(
                        women_path,
                        selected_events=selected_events,
                        gender_filter="F",
                        include_foreign=include_foreign,
                        state_filter=state_filter,
                    )
                    for rr in r_f:
                        rr.insert(5, meet_code)
                    rows += r_f
        except Exception:
            rows = []

    # Headers for the results table
    headers = [
        "Gender",
        "Event",
        "Name",
        "Team",
        "Age",
        "Meet",
        "Time",
        "AQUA",
        "Place",
        "On Track<br>Target Time",
        "On Track<br>AQUA",
        "Difference",
    ]
    selected_labels = [m['label'] for m in selected_meets]

    # Optionally reduce to best time per (Gender, Event, Name)
    if rows and results_mode == 'best':
        best = {}
        for r in rows:
            key = (str(r[0]).strip(), str(r[1]).strip(), _norm_name(r[2]))
            t = _parse_duration_seconds(r[6])
            if key not in best:
                best[key] = (r, t)
            else:
                _, cur_t = best[key]
                if t is not None and (cur_t is None or t < cur_t):
                    best[key] = (r, t)
        rows = [v[0] for v in best.values()]

    # Default sort: by Place (asc), blanks/N/A last
    def _parse_int(val):
        try:
            return int(float(str(val)))
        except Exception:
            return None
    if rows:
        rows.sort(
            key=lambda r: (
                _parse_int(r[8]) is None,              # Place is column index 8 after inserting Meet at 5
                _parse_int(r[8]) if _parse_int(r[8]) is not None else 0,
            )
        )

    # Compute name column width (chars) = longest name + 3 buffer
    if rows:
        try:
            name_col_ch = max(len(str(r[2])) for r in rows if len(r) > 2) + 1
        except Exception:
            name_col_ch = 12
    else:
        name_col_ch = 12

    return render_template(
        'index.html',
        headers=headers,
        rows=rows,
        selected_meets=selected_labels,
        selected_meet_ids=selected_ids,
        selected_events=selected_events,
        selected_genders=selected_genders,
        include_foreign=include_foreign,
        results_mode=results_mode,
        state_filter=state_filter,
        state_codes=sorted(list(TEAM_ALIASES.keys())),
        event_options=EVENT_OPTIONS,
        missing_paths=missing_paths,
        available_meets=AVAILABLE_MEETS,
        show_selection_form=show_selection_form,
        name_col_ch=name_col_ch,
    )

@app.route('/run', methods=['GET', 'POST'])
def run_calculations():
    # Determine selected meets (default to SUKMA 2024 on GET)
    if request.method == 'POST':
        selected_ids = request.form.getlist('meets') or ['sukma2024']
    else:
        selected_ids = ['sukma2024']

    selected_meets = [m for m in AVAILABLE_MEETS if m['id'] in selected_ids]

    # Build required file list based on selection + global AQUA
    required_paths = {AQUA_FILE}
    for m in selected_meets:
        if m.get('men_path'):
            required_paths.add(m['men_path'])
        if m.get('women_path'):
            required_paths.add(m['women_path'])

    missing_paths = [p for p in sorted(required_paths) if not os.path.exists(p)]
    if missing_paths:
        missing_html = "<br>".join(missing_paths)
        return (f"<h2>Missing required data files:<br>{missing_html}</h2>", 400)

    # For now, just render headers (no rows yet) and show which meets were selected
    headers = [
        "Gender",
        "Event",
        "Name",
        "Age",
        "Time",
        "AQUA",
        "Place",
        "On Track<br>Target Time",
        "On Track<br>AQUA",
        "Difference",
    ]
    rows = []
    selected_labels = [m['label'] for m in selected_meets]
    return render_template('results.html', headers=headers, rows=rows, selected_meets=selected_labels)

# Note: '/select' route removed; selection is handled on the home page.

if __name__ == '__main__':
    app.run(debug=True)
    # State filter (optional 3-letter code)
    if request.method == 'POST':
        state_filter = request.form.get('state_code', '').strip().upper()
    else:
        state_filter = ''
