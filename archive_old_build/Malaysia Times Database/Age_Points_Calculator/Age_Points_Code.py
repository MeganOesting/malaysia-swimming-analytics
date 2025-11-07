
import os
from flask import Flask, render_template, request, jsonify, url_for
import pandas as pd
import math

# Edit this filename if your workbook has a different name
# Prefer the consolidated workbook placed under Malaysia_Times_Database
_HERE = os.path.dirname(__file__)
_CANDIDATES = [
    os.path.join(_HERE, "..", "Malaysia_Times_Database", "Age_OnTrack_AQUA.xlsx"),
    os.path.join(os.getcwd(), "Malaysia_Times_Database", "Age_OnTrack_AQUA.xlsx"),
    os.path.join(os.getcwd(), "Age_OnTrack_AQUA.xlsx"),
]
WORKBOOK_FILENAME = next((p for p in _CANDIDATES if os.path.exists(p)), _CANDIDATES[0])
SHEET_NAME = "Bakat Base Times"  # sheet that contains base times

app = Flask(__name__)

def load_base_table():
    # Load the base times sheet into a dataframe. Expect columns:
    # A: Gender, B: Age, C: Event, E: Base Time (either seconds or mm:ss.ff text)
    df = pd.read_excel(WORKBOOK_FILENAME, sheet_name=SHEET_NAME, engine="openpyxl")
    # Ensure expected column names exist; fallback to positional access if not
    # Normalize column names
    df.columns = [str(c).strip() for c in df.columns]
    return df

def parse_time_to_seconds(t):
    """
    Accepts either a numeric value (seconds) or a string like 'mm:ss.ff' and returns seconds (float).
    """
    if pd.isna(t):
        return None
    if isinstance(t, (int, float)):
        return float(t)
    s = str(t).strip()
    if ":" in s:
        try:
            mins = float(s.split(":")[0])
            secs = float(s.split(":")[1])
            return mins * 60.0 + secs
        except Exception:
            # fallback
            return float(s)
    # try direct conversion
    return float(s)

@app.route("/")
def index():
    df = load_base_table()
    # try to find common column names: assume first three cols are Gender, Age, Event if names unclear
    cols = list(df.columns)
    # heuristics
    gender_col = None
    age_col = None
    event_col = None
    for c in cols:
        cl = c.lower()
        if "gender" in cl or c.strip().lower() in ("gender","sex"):
            gender_col = c
        if "age" in cl and age_col is None:
            age_col = c
        if "event" in cl:
            event_col = c
    # fallback to first three columns
    if gender_col is None:
        gender_col = cols[0]
    if age_col is None:
        age_col = cols[1] if len(cols) > 1 else cols[0]
    if event_col is None:
        event_col = cols[2] if len(cols) > 2 else cols[0]
    # read unique values for dropdowns
    genders = sorted(df[gender_col].dropna().astype(str).unique().tolist())
    ages = sorted(df[age_col].dropna().astype(int).unique().tolist())
    # Step 1: Define preferred order manually
    preferred_order = [
        "50 Free", "100 Free", "200 Free", "400 Free", "800 Free", "1500 Free",
        "100 Back", "200 Back",
        "100 Breast", "200 Breast",
        "100 Fly", "200 Fly",
        "200 IM", "400 IM"
    ]

    # Step 2: Keep only events that exist in your Excel sheet
    existing_events = df[event_col].dropna().astype(str).unique().tolist()
    events = [e for e in preferred_order if e in existing_events]

    # Step 3: Pass to template
    return render_template(
        "index.html",
        genders=genders,
        ages=ages,
        events=events,
        compute_url=url_for("compute"),
    )


@app.route("/compute", methods=["POST"])
def compute():
    payload = request.json
    gender = payload.get("gender")
    age = payload.get("age")
    event = payload.get("event")
    swimmer_time_input = payload.get("swimmer_time")
    df = load_base_table()
    # identify cols again (same heuristic)
    cols = list(df.columns)
    gender_col = next((c for c in cols if "gender" in c.lower() or c.strip().lower() in ("gender","sex")), cols[0])
    age_col = next((c for c in cols if "age" in c.lower()), cols[1] if len(cols)>1 else cols[0])
    event_col = next((c for c in cols if "event" in c.lower()), cols[2] if len(cols)>2 else cols[0])
    base_col = None
    # try find column E by name; else choose a numeric-looking column or the 5th column if exists
    for c in cols:
        if "base" in c.lower() or "time" in c.lower() and ("base" in c.lower() or "on track" in c.lower()):
            base_col = c
    if base_col is None:
        if len(cols) >= 5:
            base_col = cols[4]  # column E
        else:
            # find first numeric column
            for c in cols:
                if pd.api.types.is_numeric_dtype(df[c]):
                    base_col = c
                    break
    # filter
    filt = (df[gender_col].astype(str).str.strip() == str(gender).strip()) & \
           (df[age_col].astype(str).str.strip() == str(age).strip()) & \
           (df[event_col].astype(str).str.strip() == str(event).strip())
    matches = df[filt]
    if matches.empty:
        return jsonify({"error":"No matching base time found for the selected Gender/Age/Event combination."}), 400
    # take first match
    base_raw = matches.iloc[0][base_col]
    base_seconds = parse_time_to_seconds(base_raw)
    try:
        swimmer_seconds = parse_time_to_seconds(swimmer_time_input)
    except Exception as e:
        return jsonify({"error":"Could not parse swimmer time. (Use mm:ss.ss)"}), 400
    if base_seconds is None or swimmer_seconds is None or swimmer_seconds == 0:
        return jsonify({"error":"Invalid base or swimmer time."}), 400
    points = round(1000.0 * (base_seconds / swimmer_seconds) ** 3.0)

    return jsonify({
    "base_time": base_seconds,
    "swimmer_time": swimmer_seconds,
    "points": points
})

if __name__ == "__main__":
    print("Run this app with: flask run --host=0.0.0.0 --port=5000 (after setting FLASK_APP=app.py)")
