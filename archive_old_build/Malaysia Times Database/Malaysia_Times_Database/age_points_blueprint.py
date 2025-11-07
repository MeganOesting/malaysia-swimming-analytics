import os
from flask import Blueprint, render_template, request, jsonify, url_for
import pandas as pd

# Reuse the same workbook and sheet settings
WORKBOOK_FILENAME = os.path.join(os.path.dirname(__file__), "Age_OnTrack_AQUA.xlsx")
SHEET_NAME = "Bakat Base Times"

age_points = Blueprint(
    "age_points",
    __name__,
    template_folder=os.path.join(os.path.dirname(__file__), "..", "Age_Points_Calculator", "templates"),
)


def load_base_table():
    df = pd.read_excel(WORKBOOK_FILENAME, sheet_name=SHEET_NAME, engine="openpyxl")
    df.columns = [str(c).strip() for c in df.columns]
    return df


def parse_time_to_seconds(t):
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
            return float(s)
    return float(s)


@age_points.route("/")
def index():
    df = load_base_table()
    cols = list(df.columns)
    gender_col = None
    age_col = None
    event_col = None
    for c in cols:
        cl = c.lower()
        if "gender" in cl or c.strip().lower() in ("gender", "sex"):
            gender_col = c
        if "age" in cl and age_col is None:
            age_col = c
        if "event" in cl:
            event_col = c
    if gender_col is None:
        gender_col = cols[0]
    if age_col is None:
        age_col = cols[1] if len(cols) > 1 else cols[0]
    if event_col is None:
        event_col = cols[2] if len(cols) > 2 else cols[0]
    genders = sorted(df[gender_col].dropna().astype(str).unique().tolist())
    ages = sorted(df[age_col].dropna().astype(int).unique().tolist())
    preferred_order = [
        "50 Free", "100 Free", "200 Free", "400 Free", "800 Free", "1500 Free",
        "100 Back", "200 Back",
        "100 Breast", "200 Breast",
        "100 Fly", "200 Fly",
        "200 IM", "400 IM",
    ]
    existing_events = df[event_col].dropna().astype(str).unique().tolist()
    events = [e for e in preferred_order if e in existing_events]
    return render_template(
        "index.html",
        genders=genders,
        ages=ages,
        events=events,
        compute_url=url_for("age_points.compute"),
    )


@age_points.route("/compute", methods=["POST"])
def compute():
    payload = request.json
    gender = payload.get("gender")
    age = payload.get("age")
    event = payload.get("event")
    swimmer_time_input = payload.get("swimmer_time")
    df = load_base_table()
    cols = list(df.columns)
    gender_col = next((c for c in cols if "gender" in c.lower() or c.strip().lower() in ("gender", "sex")), cols[0])
    age_col = next((c for c in cols if "age" in c.lower()), cols[1] if len(cols) > 1 else cols[0])
    event_col = next((c for c in cols if "event" in c.lower()), cols[2] if len(cols) > 2 else cols[0])
    base_col = None
    for c in cols:
        if "base" in c.lower() or ("time" in c.lower() and ("base" in c.lower() or "on track" in c.lower())):
            base_col = c
    if base_col is None:
        if len(cols) >= 5:
            base_col = cols[4]
        else:
            for c in cols:
                if pd.api.types.is_numeric_dtype(df[c]):
                    base_col = c
                    break
    filt = (
        df[gender_col].astype(str).str.strip() == str(gender).strip()
    ) & (
        df[age_col].astype(str).str.strip() == str(age).strip()
    ) & (
        df[event_col].astype(str).str.strip() == str(event).strip()
    )
    matches = df[filt]
    if matches.empty:
        return jsonify({"error": "No matching base time found for the selected Gender/Age/Event combination."}), 400
    base_raw = matches.iloc[0][base_col]
    base_seconds = parse_time_to_seconds(base_raw)
    try:
        swimmer_seconds = parse_time_to_seconds(swimmer_time_input)
    except Exception:
        return jsonify({"error": "Could not parse swimmer time. (Use mm:ss.ss)"}), 400
    if base_seconds is None or swimmer_seconds is None or swimmer_seconds == 0:
        return jsonify({"error": "Invalid base or swimmer time."}), 400
    points = round(1000.0 * (base_seconds / swimmer_seconds) ** 3.0)
    return jsonify({
        "base_time": base_seconds,
        "swimmer_time": swimmer_seconds,
        "points": points,
    })
