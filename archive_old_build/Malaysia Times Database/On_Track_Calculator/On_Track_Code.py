from flask import Flask, render_template, request, send_file, send_from_directory, url_for, redirect
import os
import sys
import re
from datetime import datetime, date
import pandas as pd
from functools import lru_cache
from io import BytesIO
import threading
import csv
app = Flask(__name__)

MY_STATE_CODES = { 'JHR','KED','KEL','MLK','NSE','PER','PHG','PNG','PRK','SBH','SEL','SWK','TRG','WPKL' }

# Optional Age Points support (import from landing package if available)
try:
    from Malaysia_Times_Database.age_points_core import compute_age_points as _compute_age_points
except Exception:
    def _compute_age_points(*args, **kwargs):
        return None

def _append_age_points(rows):
    if not rows:
        return rows
    out = []
    for r in rows:
        try:
            pts = _compute_age_points(r[0], r[4], r[1], r[6])
        except Exception:
            pts = None
        rr = list(r)
        # If swimmer is 19+ years, leave Age Points blank; otherwise show N/A when unavailable
        age_val = None
        try:
            age_val = int(float(str(r[4]).strip())) if str(r[4]).strip() else None
        except Exception:
            age_val = None
        if pts is not None:
            rr.append(pts)
        else:
            rr.append("") if (age_val is not None and age_val >= 19) else rr.append("N/A")
        out.append(rr)
    return out

def _process_meet_workbook(workbook_path, selected_events, selected_genders, selected_age_groups, include_foreign, state_filter):
    """
    Process a single meet workbook containing both men's and women's results.
    Returns list of processed rows with team codes resolved.
    """
    rows = []
    if not os.path.exists(workbook_path):
        return rows
    
    try:
        # Get cached rows for both genders
        base_rows_m = _get_meet_rows_cached(workbook_path, 'M')
        base_rows_f = _get_meet_rows_cached(workbook_path, 'F')
        
        # Process men's results
        for rr in base_rows_m:
            if rr[1] not in selected_events:
                continue
            if "M" not in selected_genders:
                continue
                
            # Apply age group filter
            if selected_age_groups and 'OPEN' not in selected_age_groups:
                try:
                    age_num = int(float(str(rr[4]).strip())) if str(rr[4]).strip() else None
                except Exception:
                    age_num = None
                if age_num is None:
                    continue
                in_group = False
                if '16-18' in selected_age_groups and 16 <= age_num <= 18:
                    in_group = True
                if '14-15' in selected_age_groups and 14 <= age_num <= 15:
                    in_group = True
                if '12-13' in selected_age_groups and 12 <= age_num <= 13:
                    in_group = True
                if '13U' in selected_age_groups and age_num <= 13:
                    in_group = True
                if not in_group:
                    continue
            
            # Process the row
            processed_row = _process_athlete_row(rr, include_foreign, state_filter)
            if processed_row:
                rows.append(processed_row)
        
        # Process women's results
        for rr in base_rows_f:
            if rr[1] not in selected_events:
                continue
            if "F" not in selected_genders:
                continue
                
            # Apply age group filter
            if selected_age_groups and 'OPEN' not in selected_age_groups:
                try:
                    age_num = int(float(str(rr[4]).strip())) if str(rr[4]).strip() else None
                except Exception:
                    age_num = None
                if age_num is None:
                    continue
                in_group = False
                if '16-18' in selected_age_groups and 16 <= age_num <= 18:
                    in_group = True
                if '14-15' in selected_age_groups and 14 <= age_num <= 15:
                    in_group = True
                if '12-13' in selected_age_groups and 12 <= age_num <= 13:
                    in_group = True
                if '13U' in selected_age_groups and age_num <= 13:
                    in_group = True
                if not in_group:
                    continue
            
            # Process the row
            processed_row = _process_athlete_row(rr, include_foreign, state_filter)
            if processed_row:
                rows.append(processed_row)
                
    except Exception as e:
        print(f"Error processing workbook {workbook_path}: {e}")
        
    return rows

def _process_athlete_row(rr, include_foreign, state_filter):
    """
    Process a single athlete row and resolve team code.
    Returns processed row or None if filtered out.
    """
    try:
        name_norm = _norm_name(rr[2])
        team_val = str(rr[3]).strip() if rr[3] else ''
        
        # PRIORITY 1: Check if preprocessed team_val contains foreign country code
        if team_val and len(team_val) == 3 and team_val.isalpha() and team_val not in MY_STATE_CODES:
            # Foreign athlete - use country code directly
            team_code = team_val
        # PRIORITY 2: Check AthleteINFO for foreign athletes
        elif _is_foreign_by_ai(name_norm):
            # Foreign athlete - use AthleteINFO country_code
            if '_ATHLETEINFO_MAP' in globals():
                ai = _ATHLETEINFO_MAP.get(name_norm)
                if ai and ai.get('country_code'):
                    team_code = ai.get('country_code')
                else:
                    team_code = 'UN'
            else:
                team_code = 'UN'
        # PRIORITY 3: Malaysian athlete in AthleteINFO
        elif '_ATHLETEINFO_MAP' in globals() and _ATHLETEINFO_MAP.get(name_norm):
            # Malaysian athlete in AthleteINFO - use AthleteINFO state_code or club mapping
            ai = _ATHLETEINFO_MAP.get(name_norm)
            if ai and ai.get('state_code'):
                team_code = ai.get('state_code')
            else:
                # Fall back to club→state mapping
                club_key = _norm_team(team_val) if team_val else ""
                key_exact = team_val
                clubs_hit = (_CLUBS_MAP_EXACT.get(key_exact) or _CLUBS_MAP.get(club_key))
                team_code = (clubs_hit[0] if clubs_hit else "")
                if not team_code:
                    team_code = 'UN'
        else:
            # Athlete not in AthleteINFO - use club→state mapping
            club_key = _norm_team(team_val) if team_val else ""
            key_exact = team_val
            clubs_hit = (_CLUBS_MAP_EXACT.get(key_exact) or _CLUBS_MAP.get(club_key))
            team_code = (clubs_hit[0] if clubs_hit else "")
            if not team_code:
                team_code = 'UN'
        
        # Apply state filter if specified
        if state_filter and team_code != state_filter:
            return None
            
        # Apply foreign filter
        is_foreign = (team_code not in MY_STATE_CODES and team_code != 'UN')
        if is_foreign and not include_foreign:
            return None
            
        # Create display name
        display_name = rr[2]
        if is_foreign:
            display_name = f"{display_name} (Non-Malaysian)"
            
        # Return processed row
        return [
            rr[0],  # Gender
            rr[1],  # Event
            display_name,  # Name
            team_code,  # Team/State
            rr[4],  # Age
            rr[5],  # Time
            rr[6],  # AQUA
            rr[7],  # Place
            rr[8],  # On Track Path Time
            rr[9],  # On Track AQUA
            rr[10], # Track Gap
        ]
        
    except Exception as e:
        print(f"Error processing row: {e}")
        return None

# Default Excel files used by the app (no uploads required)
MEN_FILE = "SUKMA_2024_Men.xls"
WOMEN_FILE = "SUKMA_2024_Women.xls"
# Consolidated workbook now lives in Malaysia_Times_Database
AQUA_FILE = "Age_OnTrack_AQUA.xlsx"
DOCS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "Malaysia_Times_Database", "static", "docs"))

def _resolve_shared_workbook(p: str) -> str:
    """Try common locations for the shared workbook.
    Returns the first existing path or the original name.
    """
    base_dir = os.path.dirname(__file__)
    candidates = [
        os.path.abspath(os.path.join(base_dir, "..", "Malaysia_Times_Database", p)),
        os.path.abspath(os.path.join(os.getcwd(), "Malaysia_Times_Database", p)),
        os.path.abspath(os.path.join(os.getcwd(), p)),
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return p

def _resolve_meet_path(p: str) -> str:
    """Resolve meet workbook paths (parent/Meets only, per current layout)."""
    base_dir = os.path.dirname(__file__)
    candidate = os.path.abspath(os.path.join(base_dir, "..", "Meets", p))
    return candidate if os.path.exists(candidate) else p

def _resolve_for_check(p: str) -> str:
    # AQUA file is shared; others are meet files living under On_Track_Calculator
    if os.path.basename(p).lower() == os.path.basename(AQUA_FILE).lower():
        return _resolve_shared_workbook(p)
    return _resolve_meet_path(p)

def _get_docs_list():
    items = []
    try:
        if os.path.isdir(DOCS_DIR):
            for name in sorted(os.listdir(DOCS_DIR)):
                path = os.path.join(DOCS_DIR, name)
                if os.path.isfile(path):
                    items.append({
                        "filename": name,
                        "title": name,
                    })
    except Exception:
        pass
    return items

def _find_doc_url_by_keywords(keywords):
    try:
        docs = _get_docs_list()
        for d in docs:
            name_lc = d["filename"].lower()
            if any(kw in name_lc for kw in keywords):
                return url_for('serve_docs', filename=d["filename"])
    except Exception:
        pass
    return None

@app.route('/docs/<path:filename>')
def serve_docs(filename):
    return send_from_directory(DOCS_DIR, filename, as_attachment=False)

@app.route('/map')
def map_page():
    """MAP (Malaysia Age Points) landing page"""
    return render_template('map.html')

@app.route('/mot')
def mot_page():
    """MOT (Malaysia On Track) page with individual assessment"""
    return render_template('mot.html')

@app.route('/ltad')
def ltad_page():
    """LTAD (Long Term Athletic Development) landing page"""
    return render_template('ltad.html')

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
        "men_path": "SEAG_2025_ALL.xlsx",
        "women_path": "SEAG_2025_ALL.xlsx",
    },
    {
        "id": "jan2024",
        "label": "State Championships",
        "abbr": "STATE24",
        "men_path": "January2024StateMeetsMen.xls",
        "women_path": "January2024StateMeetsWomen.xls",
    },
]

# Sheet filtering tokens and Excel helpers
# Skip obvious nonâ€‘result sheets; avoid single-letter tokens like 'x' which overâ€‘match
SKIP_SHEET_TOKENS = ("lap", "top results", "5000m")

def _norm_team(s: str) -> str:
    if s is None:
        return ""
    s = str(s).lower().strip()
    # collapse internal whitespace
    s = " ".join(s.split())
    return s

# Team alias table has been removed in favor of Clubs_By_State.xlsx lookups.

def _is_foreign_by_ai(name_norm: str) -> bool:
    try:
        ai = _ATHLETEINFO_MAP.get(name_norm) if '_ATHLETEINFO_MAP' in globals() else None
        return (str((ai or {}).get('foreign') or '').strip().upper() == 'Y')
    except Exception:
        return False

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
def load_foreign_names():
    # Deprecated path retained for compatibility; now always empty.
    return set()


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
        engine = "xlrd" if str(workbook_path).lower().endswith(".xls") else None
        xl = pd.ExcelFile(workbook_path, engine=engine)
    except Exception:
        return []
    valid = []
    # Special-case: if using our combined SEA Age workbook, prefer only that sheet
    try:
        base = os.path.basename(workbook_path).lower()
        if 'seag_2025_all' in base:
            for name in xl.sheet_names:
                if name.strip().lower() == 'seag_2025_all':
                    return [name]
    except Exception:
        pass
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
    aqua_path = _resolve_shared_workbook(aqua_path)
    if not os.path.exists(aqua_path):
        return {}
    try:
        df = pd.read_excel(aqua_path, sheet_name=sheet_name, header=None)
    except Exception:
        return {}
    if df is None or df.empty:
        return {}
    mapping = {}
    mapping_exact = {}
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
    # Resolve shared workbook path (lives under Malaysia_Times_Database)
    aqua_path = _resolve_shared_workbook(aqua_path)
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

# ----------------------
# Meet rows caching layer
# ----------------------

# Cache of pre-parsed meet rows keyed by (abs_path, gender, mtime)
_MEET_ROWS_CACHE = {}
# Global athlete -> state code mapping (seeded from SUKMA/CSV)
ATHLETE_STATE_MAP = {}
_ATHLETE_STATE_CSV = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "Malaysia_Times_Database", "athlete_state_lookup.csv"))
_ATHLETEINFO_CSV = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "Malaysia_Times_Database", "AthleteINFO.csv"))
_ATHLETEINFO_MAP = {}
_CLUBS_XLSX = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "Malaysia_Times_Database", "Clubs_By_State.xlsx"))

_CLUBS_MAP = {}
_CLUBS_CODES = set()
_CLUBS_MAP_EXACT = {}
_SUKMA_TEAM_BY_NAME = {}

# Common state name aliases -> 3-letter codes
STATE_NAME_TO_CODE = {
    # Core MY states
    'johor': 'JHR', 'pra johor': 'JHR',
    'kedah': 'KED', 'pra kedah': 'KED',
    'kelantan': 'KEL', 'pra kelantan': 'KEL',
    'melaka': 'MLK', 'malacca': 'MLK', 'pra melaka': 'MLK', 'pra malacca': 'MLK',
    'negeri sembilan': 'NSE', 'n. sembilan': 'NSE', 'pra negeri sembilan': 'NSE',
    'perlis': 'PER', 'pra perlis': 'PER',
    'pahang': 'PHG', 'pra pahang': 'PHG',
    'penang': 'PNG', 'pulau pinang': 'PNG', 'pra penang': 'PNG', 'pra pulau pinang': 'PNG',
    'perak': 'PRK', 'pra perak': 'PRK',
    'sabah': 'SBH', 'pra sabah': 'SBH',
    'selangor': 'SEL', 'pra selangor': 'SEL',
    'sarawak': 'SWK', 'pra sarawak': 'SWK',
    'terengganu': 'TRG', 'pra terengganu': 'TRG',
    'kuala lumpur': 'WPKL', 'wp kuala lumpur': 'WPKL', 'wp kl': 'WPKL', 'wpkl': 'WPKL', 'kl': 'WPKL', 'wilayah persekutuan kuala lumpur': 'WPKL',
}

def _state_code_from_name(name: str) -> str:
    try:
        s = (name or '').strip().lower()
        if not s:
            return ''
        # collapse multiple spaces
        s = ' '.join(s.split())
        return STATE_NAME_TO_CODE.get(s, '')
    except Exception:
        return ''

def _map_team_to_code(team_raw: str) -> str:
    """Resolve a raw team/club/state string to a 3-letter state code.
    Uses clubs map (exact, normalized), then state-name aliases, then 3-letter passthrough.
    """
    try:
        if not team_raw:
            return ''
        key_exact = str(team_raw).strip()
        club_key = _norm_team(team_raw)
        hit = (_CLUBS_MAP_EXACT.get(key_exact) or _CLUBS_MAP.get(club_key))
        if hit:
            return (hit[0] or '').strip().upper()
        alias = _state_code_from_name(team_raw)
        if alias:
            return alias
        raw = str(team_raw).strip().upper()
        if raw and len(raw) == 3 and raw.isalpha():
            return raw
    except Exception:
        return ''
    return ''

def _norm_name_strip_paren(s: str) -> str:
    try:
        import re as _re
        base = _re.sub(r"\(.*?\)", " ", s or "")
    except Exception:
        base = s or ''
    return _norm_name(base)

def _infer_local_athlete_states(base_rows):
    """From a list of pre-parsed rows [.., Name, Team, ..], infer a per-athlete
    state code using any rows where Team is not 'Malaysia' and maps to a code.
    Returns dict of normalized name -> 3-letter code, choosing the most frequent.
    """
    counts = {}
    try:
        for rr in (base_rows or []):
            try:
                nm = _norm_name_strip_paren(rr[2])
                team_val = (rr[3] or '').strip()
            except Exception:
                continue
            if not nm or not team_val or team_val.lower() == 'malaysia':
                continue
            code = _map_team_to_code(team_val)
            if not code:
                continue
            d = counts.setdefault(nm, {})
            d[code] = d.get(code, 0) + 1
    except Exception:
        pass
    result = {}
    for nm, d in counts.items():
        try:
            # pick the code with max count
            best = max(d.items(), key=lambda kv: kv[1])[0]
            result[nm] = best
        except Exception:
            continue
    return result
def _meet_cache_key(workbook_path: str, gender_filter: str):
    try:
        resolved = _resolve_meet_path(workbook_path)
        mtime = os.path.getmtime(resolved) if os.path.exists(resolved) else 0
    except Exception:
        resolved = workbook_path
        mtime = 0
    return (os.path.abspath(resolved), str(gender_filter).upper(), mtime)

def _preparse_meet_rows(workbook_path, gender_filter="M"):
    """Parse entire meet workbook for a single gender into rows without UI filters.
    Returns rows with columns: [Gender, Event, Name, Team, Age, Time, AQUA, Place,
    On Track Path Time, On Track AQUA, Track Gap]. Foreign swimmers are annotated.
    """
    rows = []
    sheets = iter_valid_sheets(workbook_path)
    for sheet in sheets:
        try:
            engine = "xlrd" if str(workbook_path).lower().endswith(".xls") else None
            if engine:
                df = pd.read_excel(workbook_path, sheet_name=sheet, header=None, engine=engine)
            else:
                df = pd.read_excel(workbook_path, sheet_name=sheet, header=None)
        except Exception:
            continue

        # Map columns by index
        colB = df.get(1)   # Gender
        colC = df.get(2)   # Distance
        colD = df.get(3)   # Stroke
        colE = df.get(4)   # Name
        colF = df.get(5)   # Birthdate (dd.mm.yyyy)
        colG = df.get(6)   # Age (optional direct age)
        colI = df.get(8)   # Time (Excel col I)
        colK = df.get(10)  # AQUA points (Excel col K)
        colM = df.get(12)  # Place (Excel col M)
        colQ = df.get(16)  # Team/State (Excel col Q)
        colN = df.get(13)  # Meet date (dd.mm.yyyy)
        if colB is None or colC is None or colD is None or colE is None:
            continue

        gender = colB.astype(str).str.strip().str.upper()
        distance = pd.to_numeric(colC, errors='coerce')
        stroke = colD.astype(str).str.strip().str.upper()
        name = colE.astype(str).str.strip()

        # Candidate mask: gender + has name + distance in allowed set
        mask = (
            (gender == str(gender_filter).upper()) &
            (name != "") &
            (distance.isin([50, 100, 200, 400, 800, 1500]))
        )

        def _extract_year(val):
            if pd.isna(val):
                return None
            if isinstance(val, (pd.Timestamp, datetime, date)):
                try:
                    return int(val.year)
                except Exception:
                    return None
            if isinstance(val, (int, float)):
                if 1900 <= int(val) <= 2100:
                    return int(val)
                try:
                    ts = pd.to_datetime(val, unit='d', origin='1899-12-30', errors='coerce')
                    if pd.notna(ts):
                        return int(ts.year)
                except Exception:
                    pass
                return None
            s = str(val).strip()
            ts = pd.to_datetime(s, dayfirst=True, errors='coerce')
            if pd.notna(ts):
                try:
                    return int(ts.year)
                except Exception:
                    return None
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
                if not ev_label:
                    continue

                # Get Nation code from column 6 (Nation column) first
                nation_code = ""
                if df.get(6) is not None and idx in df.get(6).index and pd.notna(df.get(6).loc[idx]):
                    nation_code = str(df.get(6).loc[idx]).strip().upper()
                
                # Team as recorded in the meet - if foreign, use nation code as state
                team_val = ""
                if nation_code and nation_code != 'MAS':
                    # Foreign athlete - use nation code as state
                    team_val = nation_code
                elif colQ is not None and idx in colQ.index and pd.notna(colQ.loc[idx]):
                    # Malaysian athlete - use club name for later state mapping
                    raw = str(colQ.loc[idx]).strip()
                    team_val = raw
                
# Compute age as of Dec 31 of meet year: meet_year - birth_year
                age_val = ""
                try:
                    by = _extract_year(colF.loc[idx]) if colF is not None and idx in colF.index else None
                    my = _extract_year(colN.loc[idx]) if colN is not None and idx in colN.index else None
                    if by is not None and my is not None:
                        diff = my - by
                        if 1 <= diff <= 50:
                            age_val = str(diff)
                except Exception:
                    age_val = ""
                # Fallback: use Age from column G if available
                if not age_val and colG is not None and idx in colG.index and pd.notna(colG.loc[idx]):
                    try:
                        age_num_try = int(float(str(colG.loc[idx]).strip()))
                        if 1 <= age_num_try <= 50:
                            age_val = str(age_num_try)
                    except Exception:
                        pass

                # Time value as-is string from column I
                time_val = ""
                if colI is not None and idx in colI.index and pd.notna(colI.loc[idx]):
                    time_val = str(colI.loc[idx]).strip()

                # AQUA points from column K (precalculated)
                aqua_val = ""
                if colK is not None and idx in colK.index and pd.notna(colK.loc[idx]):
                    try:
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
                on_track_aqua = ""
                try:
                    t_sec = _parse_duration_seconds(on_track_target)
                    if t_sec:
                        male_map, female_map = load_aqua_points_maps()
                        base_sec = (male_map if gender_filter == "M" else female_map).get(_clean_key(ev_label))
                        if base_sec and t_sec > 0:
                            on_track_aqua = str(int(1000.0 * (base_sec / t_sec) ** 3))
                        else:
                            on_track_aqua = "N/A"
                    else:
                        on_track_aqua = ""
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

                # Determine foreign status by AthleteINFO; annotate but do not filter here
                display_name = name.loc[idx]
                is_foreign = _is_foreign_by_ai(_norm_name(display_name))
                if is_foreign:
                    display_name = f"{display_name} (Non-Malaysian)"

                rows.append([
                    ("Male" if str(gender_filter).upper()=="M" else "Female"),
                    ev_label,
                    display_name,
                    team_val,
                    age_val,
                    time_val,
                    aqua_val,
                    place_val,
                    on_track_target,
                    on_track_aqua,
                    diff_val,
                ])
    return rows

def _get_meet_rows_cached(workbook_path, gender_filter="M"):
    key = _meet_cache_key(workbook_path, gender_filter)
    if key in _MEET_ROWS_CACHE:
        return _MEET_ROWS_CACHE[key]
    rows = _preparse_meet_rows(workbook_path, gender_filter)
    _MEET_ROWS_CACHE[key] = rows
    return rows

def _load_athlete_state_csv():
    out = {}
    try:
        if os.path.exists(_ATHLETE_STATE_CSV):
            import csv
            with open(_ATHLETE_STATE_CSV, newline='', encoding='utf-8') as f:
                for row in csv.DictReader(f):
                    n = _norm_name(row.get('name')) if row.get('name') else ''
                    s = (row.get('state') or '').strip().upper()
                    if n and s:
                        out[n] = s
    except Exception:
        pass
    return out

def _build_athlete_state_map():
    # Seed from CSV
    try:
        ATHLETE_STATE_MAP.update(_load_athlete_state_csv())
    except Exception:
        pass


def _reload_clubs_map():
    """Load Clubs_By_State.xlsx into name -> state_code maps.
    Primary strategy: use sheet name as state code, column A as club/team name.
    Fallback: if column C has a code, prefer that over sheet title.
    Builds both exact (case-sensitive) and normalized (_norm_team) maps.
    """
    global _CLUBS_MAP, _CLUBS_MAP_EXACT, _CLUBS_CODES
    mapping = {}
    mapping_exact = {}
    codes = set()
    try:
        if os.path.exists(_CLUBS_XLSX):
            try:
                import openpyxl
            except Exception:
                openpyxl = None
            if openpyxl is not None:
                try:
                    wb = openpyxl.load_workbook(_CLUBS_XLSX, data_only=True)
                    for ws in wb.worksheets:
                        sheet_code = (ws.title or '').strip().upper()
                        if sheet_code:
                            codes.add(sheet_code)
                        for r in ws.iter_rows(values_only=True):
                            try:
                                name = (str(r[0]) if r and len(r) >= 1 and r[0] is not None else '').strip()
                                code_cell = (str(r[2]) if r and len(r) >= 3 and r[2] is not None else '').strip().upper()
                            except Exception:
                                continue
                            if not name:
                                continue
                            code = code_cell or sheet_code
                            if not code:
                                continue
                            mapping_exact[name] = (code, '')
                            mapping[_norm_team(name)] = (code, '')
                except Exception:
                    pass
            # Fallback: pandas reader if openpyxl path failed
            if not mapping:
                try:
                    xls = pd.ExcelFile(_CLUBS_XLSX, engine='openpyxl')
                    for sheet in xls.sheet_names:
                        try:
                            codes.add(str(sheet).strip().upper())
                            df = pd.read_excel(_CLUBS_XLSX, sheet_name=sheet, header=None, engine='openpyxl')
                            if df is None or df.empty:
                                continue
                            for _, row in df.iterrows():
                                try:
                                    name = str(row.iloc[0]) if row.shape[0] >= 1 else ''
                                    code = str(row.iloc[2]) if row.shape[0] >= 3 else ''
                                except Exception:
                                    continue
                                name = (name or '').strip()
                                code = (code or '').strip().upper() or str(sheet).strip().upper()
                                if not name or not code:
                                    continue
                                mapping_exact[name] = (code, '')
                                mapping[_norm_team(name)] = (code, '')
                        except Exception:
                            continue
                except Exception:
                    pass
    except Exception:
        mapping = {}
        mapping_exact = {}
    _CLUBS_MAP = mapping
    _CLUBS_MAP_EXACT = mapping_exact
    _CLUBS_CODES = codes if codes else set()


def _build_sukma_lookup():
    """Build mapping from normalized athlete name -> SUKMA team string.
    Uses SUKMA 2024 men/women cached rows so we can infer a state when
    other meets list Team as 'Malaysia'.
    """
    global _SUKMA_TEAM_BY_NAME
    out = {}
    try:
        men = _resolve_meet_path("SUKMA_2024_Men.xls")
        women = _resolve_meet_path("SUKMA_2024_Women.xls")
        for path, g in ((men, 'M'), (women, 'F')):
            try:
                if path and os.path.exists(path):
                    rows = _get_meet_rows_cached(path, g)
                    for rr in rows:
                        try:
                            nm = _norm_name(rr[2]) if len(rr) > 2 else ''
                            tm = str(rr[3]).strip() if len(rr) > 3 and rr[3] else ''
                        except Exception:
                            nm, tm = '', ''
                        if nm and tm and tm.lower() != 'malaysia' and nm not in out:
                            out[nm] = tm
            except Exception:
                continue
    except Exception:
        out = {}
    _SUKMA_TEAM_BY_NAME = out



def _warm_all_meets_async():
    def _warm():
        try:
            _build_athlete_state_map()
        except Exception:
            pass
        try:
            _reload_clubs_map()
        except Exception:
            pass
        try:
            _build_sukma_lookup()
        except Exception:
            pass
        # Preload AthleteINFO.csv into memory so Malaysia overrides can use it
        try:
            global _ATHLETEINFO_MAP
            _ATHLETEINFO_MAP = {}
            if os.path.exists(_ATHLETEINFO_CSV):
                with open(_ATHLETEINFO_CSV, newline='', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        nm = (row.get('name') or '').strip()
                        if not nm:
                            continue
                        key = _norm_name(nm)
                        rec = {
                            'state_code': (row.get('state_code') or '').strip().upper(),
                            'team_name': (row.get('team_name') or '').strip(),
                            'verified': (row.get('verified') or '').strip().upper(),
                            'foreign': (row.get('foreign') or '').strip().upper(),
                        }
                        prev = _ATHLETEINFO_MAP.get(key)
                        if not prev:
                            _ATHLETEINFO_MAP[key] = rec
                        else:
                            prev_score = (1 if prev.get('verified') == 'Y' else 0) + (1 if prev.get('state_code') else 0)
                            new_score = (1 if rec.get('verified') == 'Y' else 0) + (1 if rec.get('state_code') else 0)
                            if new_score > prev_score:
                                _ATHLETEINFO_MAP[key] = rec
        except Exception:
            pass
    try:
        threading.Thread(target=_warm, daemon=True).start()
    except Exception:
        pass


def extract_male_50_free_rows(
    workbook_path,
    max_sheets=None,
    selected_events=None,
    gender_filter="M",
    include_foreign=True,
    state_filter: str = "",
    selected_age_groups=None,
):
    """
    Read up to `max_sheets` valid sheets from the menâ€™s workbook and return rows
    for Gender, Event, Name (other columns blank) where:
      B == 'M' (male), C == 50 (distance), D == 'Fr' (stroke), E has a name.
    """
    rows = []
    sheets = iter_valid_sheets(workbook_path)
    used = 0
    for sheet in sheets:
        try:
            # header=None so B,C,D,E => cols 1,2,3,4
            engine = "xlrd" if str(workbook_path).lower().endswith(".xls") else None
            if engine:
                df = pd.read_excel(
                    workbook_path,
                    sheet_name=sheet,
                    header=None,
                    engine=engine,
                )
            else:
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
        colG = df.get(6)   # Age (optional direct age)
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

                # Team as recorded in the meet (do not map to state here)
                team_val = ""
                if colQ is not None and idx in colQ.index and pd.notna(colQ.loc[idx]):
                    raw = str(colQ.loc[idx]).strip()
                    team_val = raw
                # Optional state code filter (based on resolved team_val)
                if state_filter and str(team_val).upper() != str(state_filter).upper():
                    continue

                # Compute age as of Dec 31 of meet year: meet_year - birth_year
                age_val = ""
                age_num = None
                try:
                    by = _extract_year(colF.loc[idx]) if colF is not None and idx in colF.index else None
                    my = _extract_year(colN.loc[idx]) if colN is not None and idx in colN.index else None
                    if by is not None and my is not None:
                        diff = my - by
                        if 1 <= diff <= 50:
                            age_val = str(diff)
                            age_num = diff
                except Exception:
                    age_val = ""

                # Fallback: use Age from column G if available
                if not age_val and colG is not None and idx in colG.index and pd.notna(colG.loc[idx]):
                    try:
                        age_num_try = int(float(str(colG.loc[idx]).strip()))
                        if 1 <= age_num_try <= 50:
                            age_val = str(age_num_try)
                            age_num = age_num_try
                    except Exception:
                        pass

                # Age group filter (if provided and 'OPEN' not selected)
                if selected_age_groups and 'OPEN' not in selected_age_groups:
                    # Exclude rows without a numeric age when specific groups selected
                    if age_num is None:
                        continue
                    in_group = False
                    if '16-18' in selected_age_groups and 16 <= age_num <= 18:
                        in_group = True
                    if '14-15' in selected_age_groups and 14 <= age_num <= 15:
                        in_group = True
                    if '12-13' in selected_age_groups and 12 <= age_num <= 13:
                        in_group = True
                    if '13U' in selected_age_groups and age_num <= 13:
                        in_group = True
                    if not in_group:
                        continue

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
                # If there is no applicable target time, leave AQUA blank
                on_track_aqua = ""
                try:
                    t_sec = _parse_duration_seconds(on_track_target)
                    if t_sec:
                        male_map, female_map = load_aqua_points_maps()
                        base_sec = (male_map if gender_filter == "M" else female_map).get(_clean_key(ev_label))
                        if base_sec and t_sec > 0:
                            on_track_aqua = str(int(1000.0 * (base_sec / t_sec) ** 3))
                        else:
                            # Target exists but base missing => show N/A
                            on_track_aqua = "N/A"
                    else:
                        # Keep blank when no target time
                        on_track_aqua = ""
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
        selected_ids = request.form.getlist('meets') or request.form.getlist('selected_meet_ids') or []
        show_selection_form = False
    else:
        # Start with no meets selected on first load
        selected_ids = []
        show_selection_form = False
        # Warm the cache for all meets in the background on initial load
        _warm_all_meets_async()

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

    # Age group filter (multi-select)
    if request.method == 'POST':
        selected_age_groups = request.form.getlist('age_groups') or ['OPEN']
    else:
        selected_age_groups = ['OPEN']

    # Validate required files for selected meets + AQUA (only when meets selected)
    missing_paths = []
    if selected_meets:
        required_paths = {AQUA_FILE}
        for m in selected_meets:
            if m.get('men_path'):
                required_paths.add(m['men_path'])
            if m.get('women_path'):
                required_paths.add(m['women_path'])
        missing_paths = [p for p in sorted(required_paths) if not os.path.exists(_resolve_for_check(p))]

    # If selection is applied and required files are present, build rows from cache
    rows = []
    if not show_selection_form and selected_meets:
        try:
            rows = []
            for meet in selected_meets:
                # Check if this is a combined workbook (both genders in one file)
                combined_path = meet.get('combined_path')
                if combined_path:
                    # Process combined workbook
                    workbook_path = _resolve_meet_path(combined_path)
                    if workbook_path and os.path.exists(workbook_path):
                        meet_rows = _process_meet_workbook(workbook_path, selected_events, selected_genders, selected_age_groups, include_foreign, state_filter)
                        meet_code = meet.get('abbr') or meet.get('label')
                        for row in meet_rows:
                            row.insert(5, meet_code)  # Insert meet code after Age
                            rows.append(row)
                else:
                    # Process separate men's and women's workbooks (legacy format)
                    men_path = meet.get('men_path')
                    women_path = meet.get('women_path')
                    meet_code = meet.get('abbr') or meet.get('label')
                    
                    if men_path:
                        r_men = _resolve_meet_path(men_path)
                        if r_men and os.path.exists(r_men):
                            meet_rows = _process_meet_workbook(r_men, selected_events, ['M'], selected_age_groups, include_foreign, state_filter)
                            for row in meet_rows:
                                row.insert(5, meet_code)
                                rows.append(row)
                    
                    if women_path:
                        r_women = _resolve_meet_path(women_path)
                        if r_women and os.path.exists(r_women):
                            meet_rows = _process_meet_workbook(r_women, selected_events, ['F'], selected_age_groups, include_foreign, state_filter)
                            for row in meet_rows:
                                row.insert(5, meet_code)
                                rows.append(row)
        except Exception:
            rows = []

    # Headers for the results table
    headers = [
        "Gender",
        "Event",
        "Name",
        "State",
        "Age",
        "Meet",
        "Time",
        "AQUA",
        "Place",
        "On Track<br>Path Time",
        "On Track<br>AQUA",
        "Track<br>Gap",
        "Age Points",
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

    # Use a stable, fixed Name column width to avoid layout shifts
    # Narrowed per feedback; hover shows full name
    name_col_ch = 24

    # Append Age Points per row at the end
    rows = _append_age_points(rows)

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
        state_codes=(sorted({v[0] for v in _CLUBS_MAP.values()}) if _CLUBS_MAP else []),
        selected_age_groups=selected_age_groups,
        event_options=EVENT_OPTIONS,
        missing_paths=missing_paths,
        available_meets=AVAILABLE_MEETS,
        show_selection_form=show_selection_form,
        name_col_ch=name_col_ch,
        docs_links=_get_docs_list(),
        map_url=_find_doc_url_by_keywords(["age", "map", "bakat"]),
        mot_url=_find_doc_url_by_keywords(["on track", "mot", "target"]),
        ltad_url=_find_doc_url_by_keywords(["ltad", "long term"]),
    )

@app.get('/admin/reload-athleteinfo')
def admin_reload_athleteinfo():
    try:
        # Soft reload AthleteINFO.csv into memory; ignore errors
        global _ATHLETEINFO_MAP
        _ATHLETEINFO_MAP = {}
        if os.path.exists(_ATHLETEINFO_CSV):
            with open(_ATHLETEINFO_CSV, newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    nm = (row.get('name') or '').strip()
                    if not nm:
                        continue
                    key = _norm_name(nm)
                    rec = {
                        'state_code': (row.get('state_code') or '').strip().upper(),
                        'team_name': (row.get('team_name') or '').strip(),
                        'verified': (row.get('verified') or '').strip().upper(),
                    }
                    prev = _ATHLETEINFO_MAP.get(key)
                    if not prev:
                        _ATHLETEINFO_MAP[key] = rec
                    else:
                        prev_score = (1 if prev.get('verified') == 'Y' else 0) + (1 if prev.get('state_code') else 0)
                        new_score = (1 if rec.get('verified') == 'Y' else 0) + (1 if rec.get('state_code') else 0)
                        if new_score > prev_score:
                            _ATHLETEINFO_MAP[key] = rec
    except Exception:
        pass
    return redirect(url_for('index'))

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

    missing_paths = [p for p in sorted(required_paths) if not os.path.exists(_resolve_for_check(p))]
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
        "Track Gap",
        "Age Points",
    ]
    rows = []
    selected_labels = [m['label'] for m in selected_meets]
    return render_template('results.html', headers=headers, rows=rows, selected_meets=selected_labels)

# Note: '/select' route removed; selection is handled on the home page.

@app.post('/export')
def export_results():
    # Parse filters similar to index()
    selected_ids = request.form.getlist('meets') or request.form.getlist('selected_meet_ids') or ['sukma2024']
    selected_meets = [m for m in AVAILABLE_MEETS if m['id'] in selected_ids]

    selected_events = request.form.getlist('events') or ["50 Free"]
    selected_genders = [g.upper() for g in request.form.getlist('genders')] or ["M"]
    include_foreign = bool(request.form.get('include_foreign'))
    results_mode = request.form.get('results_mode', 'all')
    if results_mode not in ('all', 'best'):
        results_mode = 'all'
    state_filter = (request.form.get('state_code', '') or '').strip().upper()
    selected_age_groups = request.form.getlist('age_groups') or ['OPEN']

    # Build rows across meets (from cache)
    rows = []
    for meet in selected_meets:
        # Check if this is a combined workbook (both genders in one file)
        combined_path = meet.get('combined_path')
        if combined_path:
            # Process combined workbook
            workbook_path = _resolve_meet_path(combined_path)
            if workbook_path and os.path.exists(workbook_path):
                meet_rows = _process_meet_workbook(workbook_path, selected_events, selected_genders, selected_age_groups, include_foreign, state_filter)
                meet_code = meet.get('abbr') or meet.get('label')
                for row in meet_rows:
                    row.insert(5, meet_code)  # Insert meet code after Age
                    rows.append(row)
        else:
            # Process separate men's and women's workbooks (legacy format)
            men_path = meet.get('men_path')
            women_path = meet.get('women_path')
            meet_code = meet.get('abbr') or meet.get('label')
            
            if men_path:
                r_men = _resolve_meet_path(men_path)
                if r_men and os.path.exists(r_men):
                    meet_rows = _process_meet_workbook(r_men, selected_events, ['M'], selected_age_groups, include_foreign, state_filter)
                    for row in meet_rows:
                        row.insert(5, meet_code)
                        rows.append(row)
            
            if women_path:
                r_women = _resolve_meet_path(women_path)
                if r_women and os.path.exists(r_women):
                    meet_rows = _process_meet_workbook(r_women, selected_events, ['F'], selected_age_groups, include_foreign, state_filter)
                    for row in meet_rows:
                        row.insert(5, meet_code)
                        rows.append(row)

    headers = [
        "Gender",
        "Event",
        "Name",
        "State",
        "Age",
        "Meet",
        "Time",
        "AQUA",
        "Place",
        "On Track Path Time",
        "On Track AQUA",
        "Track Gap",
        "Age Points",
    ]

    # Reduce to best if requested
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

    # Apply sort based on current UI selection
    sort_col = request.form.get('sort_col')
    sort_dir = request.form.get('sort_dir', 'asc')
    try:
        sort_col = int(sort_col) if sort_col is not None and str(sort_col).strip() != '' else None
    except Exception:
        sort_col = None

    # Map template column (1-based) to rows index (0-based)
    col_map = {5: 4, 7: 6, 9: 8, 12: 11, 13: 12}  # Age, Time, Place, Difference, Age Points
    if rows:
        if sort_col in col_map:
            idx = col_map[sort_col]
            asc = (sort_dir != 'desc')
            if sort_col == 7:  # Time: use duration seconds; keep N/A last
                def key_fn(r):
                    sec = _parse_duration_seconds(r[idx])
                    if sec is None:
                        return (1, 0)
                    return (0, sec if asc else -sec)
            else:  # Numeric columns: Age, Place, Difference; keep N/A last
                def _p(v):
                    try:
                        return float(str(v))
                    except Exception:
                        return None
                def key_fn(r):
                    val = _p(r[idx])
                    if val is None:
                        return (1, 0)
                    return (0, val if asc else -val)
            rows.sort(key=key_fn)
        else:
            # Default to Place asc; keep blanks last
            def _p(v):
                try:
                    return float(str(v))
                except Exception:
                    return None
            rows.sort(key=lambda r: (_p(r[8]) is None, _p(r[8]) if _p(r[8]) is not None else 0))

    # Append Age Points for export as well
    rows = _append_age_points(rows)

    # Export as XLSX
    df = pd.DataFrame(rows, columns=headers)
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Results')
    buf.seek(0)
    return send_file(
        buf,
        as_attachment=True,
        download_name='On_Track_Results.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )


@app.get('/admin/reload-clubs')
def admin_reload_clubs():
    try:
        _reload_clubs_map()
    except Exception:
        pass
    return redirect(url_for('index'))


@app.get('/admin/debug-club')
def admin_debug_club():
    try:
        try:
            _reload_clubs_map()
        except Exception:
            pass
        name = request.args.get('name', '')
        name_raw = name
        key_exact = (name.strip()) if name else ''
        key_norm = _norm_team(name)
        exact_val = _CLUBS_MAP_EXACT.get(key_exact) if '_CLUBS_MAP_EXACT' in globals() else None
        norm_val = _CLUBS_MAP.get(key_norm) if '_CLUBS_MAP' in globals() else None
        codes = sorted(_CLUBS_CODES) if ('_CLUBS_CODES' in globals() and _CLUBS_CODES) else []
        lines = []
        lines.append(f"name_raw: {name_raw!r}")
        lines.append(f"key_exact: {key_exact!r}")
        lines.append(f"key_norm: {key_norm!r}")
        lines.append(f"exact_hit: {exact_val!r}")
        lines.append(f"norm_hit: {norm_val!r}")
        lines.append(f"codes_count: {len(codes)}")
        if codes:
            sample = ", ".join(codes[:20])
            lines.append("codes_sample: " + sample)
        return "<pre>" + "\n".join(lines) + "</pre>"
    except Exception as e:
        return f"<pre>error: {e!r}</pre>", 500


@app.get('/admin/flush-cache')
def admin_flush_cache():
    """Clear cached meet rows and reload club/state maps."""
    try:
        try:
            _MEET_ROWS_CACHE.clear()
        except Exception:
            pass
        try:
            # Clear LRU caches for AQUA/MOT
            load_mot_targets_map.cache_clear()  # type: ignore[attr-defined]
        except Exception:
            pass
        try:
            load_aqua_points_maps.cache_clear()  # type: ignore[attr-defined]
        except Exception:
            pass
        try:
            _build_athlete_state_map()
        except Exception:
            pass
        try:
            _reload_clubs_map()
        except Exception:
            pass
        return "<pre>cache: cleared</pre>", 200
    except Exception as e:
        return f"<pre>error: {e!r}</pre>", 500


@app.get('/admin/debug-q-scan')
def admin_debug_q_scan():
    """Diagnose why Team/State (col Q) appears blank or unmapped.

    Query params:
      - meet: workbook filename (e.g., January2024StateMeetsMen.xls)
      - gender: 'M' or 'F' (default 'M')
      - limit: max rows to show (default 50)
      - show_all=1 to show all rows (otherwise only problematic ones)
    """
    try:
        try:
            _reload_clubs_map()
        except Exception:
            pass

        meet = request.args.get('meet', '')
        gender = (request.args.get('gender', 'M') or 'M').upper()
        limit = int(request.args.get('limit', '50') or '50')
        show_all = (request.args.get('show_all', '0') == '1')
        if not meet:
            return "<pre>Usage: /admin/debug-q-scan?meet=FILENAME&gender=M&limit=100</pre>", 400
        resolved = _resolve_meet_path(meet)
        if not os.path.exists(resolved):
            return f"<pre>meet not found: {resolved!r}</pre>", 404

        base_rows = _get_meet_rows_cached(resolved, gender)
        lines = []
        def _last_codes(s: str, n: int = 6):
            try:
                return [ord(c) for c in s[-n:]] if s else []
            except Exception:
                return []
        shown = 0
        for rr in base_rows:
            try:
                name = str(rr[2])
                team_val = rr[3]
                q_str = str(team_val) if team_val is not None else ''
                q_strip = q_str.strip()
                key_exact = (q_strip if q_strip else '')
                key_norm = _norm_team(q_str)
                exact_hit = _CLUBS_MAP_EXACT.get(key_exact) if ('_CLUBS_MAP_EXACT' in globals()) else None
                norm_hit = _CLUBS_MAP.get(key_norm) if ('_CLUBS_MAP' in globals()) else None
                reason = []
                if team_val in (None, ''):
                    reason.append('rr[3] is empty')
                if team_val not in (None, '') and not q_strip:
                    reason.append('rr[3] only whitespace')
                if not exact_hit and not norm_hit:
                    reason.append('no mapping hit')
                if q_strip.lower() == 'malaysia':
                    # Malaysia override check
                    ov = ATHLETE_STATE_MAP.get(_norm_name(name)) if 'ATHLETE_STATE_MAP' in globals() else None
                    if ov:
                        reason.append(f"malaysia-override:{ov}")
                    else:
                        reason.append('malaysia-no-override')

                # Filter to problematic rows unless show_all requested
                is_problem = (team_val in (None, '') or not q_strip or (not exact_hit and not norm_hit))
                if not show_all and not is_problem:
                    continue

                lines.append('---')
                lines.append(f"name: {name!r}")
                lines.append(f"team_val_repr: {q_str!r}")
                lines.append(f"q_len: {len(q_str)}")
                lines.append(f"q_strip_repr: {q_strip!r}")
                lines.append(f"q_strip_len: {len(q_strip)}")
                lines.append(f"q_last_codes: {_last_codes(q_str)}")
                lines.append(f"key_exact: {key_exact!r}")
                lines.append(f"key_norm: {key_norm!r}")
                lines.append(f"exact_hit: {exact_hit!r}")
                lines.append(f"norm_hit: {norm_hit!r}")
                lines.append(f"reason: {', '.join(reason) if reason else 'ok'}")
                shown += 1
                if shown >= limit:
                    break
            except Exception as _e:
                lines.append(f"row_error: {_e!r}")
                continue

        if not lines:
            return "<pre>no rows to show</pre>"
        return "<pre>" + "\n".join(lines) + "</pre>"
    except Exception as e:
        return f"<pre>error: {e!r}</pre>", 500
@app.get('/admin/missing-states')
def admin_missing_states():
    try:
        try:
            _reload_clubs_map()
        except Exception:
            pass
        rows = []
        # Build a quick map from meet path to abbr/label
        meet_info = {}
        for m in AVAILABLE_MEETS:
            meet_info[m.get('men_path')] = (m.get('abbr') or m.get('label') or '')
            meet_info[m.get('women_path')] = (m.get('abbr') or m.get('label') or '')
        for m in AVAILABLE_MEETS:
            for gender in ('M','F'):
                path = m.get('men_path') if gender=='M' else m.get('women_path')
                if not path:
                    continue
                r = _resolve_meet_path(path)
                if not (r and os.path.exists(r)):
                    continue
                base_rows = _get_meet_rows_cached(r, gender)
                for rr in base_rows:
                    # Resolve state using exact A->C map, then fallback normalized
                    team_val = str(rr[3]).strip() if rr[3] else ''
                    key_exact = team_val if team_val else ''
                    key_norm = _norm_team(team_val)
                    exact_hit = _CLUBS_MAP_EXACT.get(key_exact) if ('_CLUBS_MAP_EXACT' in globals()) else None
                    norm_hit = _CLUBS_MAP.get(key_norm) if ('_CLUBS_MAP' in globals()) else None
                    team_code = exact_hit[0] if exact_hit else (norm_hit[0] if norm_hit else '')
                    if not team_code:
                        rows.append({
                            'gender': rr[0],
                            'event': rr[1],
                            'name': rr[2],
                            'team_val': team_val,
                            'meet': meet_info.get(m.get('men_path') if gender=='M' else m.get('women_path'), ''),
                        })
        if not rows:
            return '<pre>No rows missing State.</pre>'
        # Render minimal HTML table
        html = ['<table border="1" cellpadding="4" cellspacing="0">']
        html.append('<tr><th>Meet</th><th>Gender</th><th>Event</th><th>Name</th><th>Q (raw)</th></tr>')
        for r in rows:
            html.append('<tr>'
                        f'<td>{r["meet"]}</td>'
                        f'<td>{r["gender"]}</td>'
                        f'<td>{r["event"]}</td>'
                        f'<td>{r["name"]}</td>'
                        f'<td>{r["team_val"]}</td>'
                        '</tr>')
        html.append('</table>')
        return ''.join(html)
    except Exception as e:
        return f"<pre>error: {e!r}</pre>", 500


@app.get('/admin/debug-athlete')
def admin_debug_athlete():
    """Show January meet Q-team for a given athlete and SUKMA team presence.
    Usage: /admin/debug-athlete?name=GOH,%20LI%20Hen
    """
    try:
        # Ensure clubs map is ready
        try:
            _reload_clubs_map()
        except Exception:
            pass

        target = (request.args.get('name') or 'GOH, LI Hen').strip()
        target_norm = _norm_name_strip_paren(target)
        lines = []
        lines.append(f"target: {target!r}")
        lines.append(f"target_norm: {target_norm!r}")
        lines.append(f"clubs_map sizes: norm={len(_CLUBS_MAP or {})}, exact={len(_CLUBS_MAP_EXACT or {})}")

        # January state meets
        jan_files = [
            ('January2024StateMeetsMen.xls', 'M'),
            ('January2024StateMeetsWomen.xls', 'F'),
        ]
        for fname, g in jan_files:
            p = _resolve_meet_path(fname)
            lines.append(f"-- January file: {fname} exists={bool(p and os.path.exists(p))}")
            if p and os.path.exists(p):
                try:
                    rows = _get_meet_rows_cached(p, g)
                    hits = 0
                    for rr in rows:
                        nm = _norm_name_strip_paren(rr[2])
                        if nm == target_norm:
                            team_val = (rr[3] or '').strip()
                            code = _map_team_to_code(team_val)
                            lines.append(f"  match gender={g} event={rr[1]!r} Q_raw={team_val!r} mapped={code!r}")
                            hits += 1
                    if hits == 0:
                        lines.append("  no matches in this file")
                except Exception as _e:
                    lines.append(f"  error reading {fname}: {_e!r}")

        # SUKMA meets
        sukma_files = [
            ('SUKMA_2024_Men.xls', 'M'),
            ('SUKMA_2024_Women.xls', 'F'),
        ]
        for fname, g in sukma_files:
            p = _resolve_meet_path(fname)
            lines.append(f"-- SUKMA file: {fname} exists={bool(p and os.path.exists(p))}")
            if p and os.path.exists(p):
                try:
                    rows = _get_meet_rows_cached(p, g)
                    hits = 0
                    for rr in rows:
                        nm = _norm_name_strip_paren(rr[2])
                        if nm == target_norm:
                            team_val = (rr[3] or '').strip()
                            code = _map_team_to_code(team_val)
                            lines.append(f"  match gender={g} event={rr[1]!r} SUKMA_Q={team_val!r} mapped={code!r}")
                            hits += 1
                    if hits == 0:
                        lines.append("  no matches in this file")
                except Exception as _e:
                    lines.append(f"  error reading {fname}: {_e!r}")

        # Cache quick hit
        cache_hit = _SUKMA_TEAM_BY_NAME.get(target_norm) if '_SUKMA_TEAM_BY_NAME' in globals() else None
        lines.append(f"sukma_cache_team: {cache_hit!r}")
        lines.append("done")
        return "<pre>" + "\n".join(lines) + "</pre>", 200
    except Exception as e:
        return f"<pre>error: {e!r}</pre>", 500


@app.get('/admin/reload-foreign')
def admin_reload_foreign():
    try:
        load_foreign_names.cache_clear()
    except Exception:
        pass
    return redirect(url_for('index'))


@app.get('/admin/reload-sukma')
def admin_reload_sukma():
    try:
        global _SUKMA_TEAM_BY_NAME
        _SUKMA_TEAM_BY_NAME = {}
        try:
            _build_sukma_lookup()
        except Exception:
            pass
        return "<pre>sukma_cache: reloaded; size=%d</pre>" % (len(_SUKMA_TEAM_BY_NAME or {})), 200
    except Exception as e:
        return f"<pre>error: {e!r}</pre>", 500


@app.get('/admin/debug-resolve')
def admin_debug_resolve():
    try:
        name = request.args.get('name', '')
        if not name:
            return "<pre>Usage: /admin/debug-resolve?name=FILENAME</pre>", 400
        resolved = _resolve_meet_path(name)
        exists = os.path.exists(resolved)
        info = [
            f"name: {name!r}",
            f"resolved: {resolved!r}",
            f"exists: {exists}",
            f"cwd: {os.getcwd()!r}",
        ]
        return "<pre>" + "\n".join(info) + "</pre>", 200
    except Exception as e:
        return f"<pre>error: {e!r}</pre>", 500

if __name__ == '__main__':
    app.run(debug=True)
