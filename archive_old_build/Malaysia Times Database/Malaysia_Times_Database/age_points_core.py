import os
from functools import lru_cache
import pandas as pd


WORKBOOK_PATH = os.path.join(os.path.dirname(__file__), "Age_OnTrack_AQUA.xlsx")
SHEET_NAME = "Bakat Base Times"


@lru_cache(maxsize=1)
def _load_base_df():
    if not os.path.exists(WORKBOOK_PATH):
        return None
    try:
        df = pd.read_excel(WORKBOOK_PATH, sheet_name=SHEET_NAME, engine="openpyxl")
    except Exception:
        return None
    if df is None or df.empty:
        return None
    df.columns = [str(c).strip() for c in df.columns]
    return df


def _parse_time_to_seconds(t):
    if t is None or (isinstance(t, float) and pd.isna(t)):
        return None
    if isinstance(t, (int, float)) and not isinstance(t, bool):
        return float(t)
    s = str(t).strip()
    if not s:
        return None
    s = s.replace(",", ".")
    if ":" in s:
        try:
            parts = s.split(":")
            mins = float(parts[-2]) if len(parts) >= 2 else 0.0
            secs = float(parts[-1])
            return mins * 60.0 + secs
        except Exception:
            pass
    try:
        return float(s)
    except Exception:
        return None


def _norm_gender_to_code(g):
    if g is None:
        return None
    s = str(g).strip().lower()
    if s in ("m", "male"):
        return "M"
    if s in ("f", "female"):
        return "F"
    # Pass through single-letter codes
    if s in ("m", "f"):
        return s.upper()
    return None


def compute_age_points(gender, age, event, time_val):
    """Return Age Points (int) or None if not computable.
    gender: 'M'/'F' or 'Male'/'Female'
    age: int-like
    event: like '100 Free'
    time_val: seconds (float) or time string
    """
    df = _load_base_df()
    if df is None:
        return None
    # find likely columns
    cols = list(df.columns)
    gender_col = next((c for c in cols if "gender" in c.lower() or c.lower().strip() in ("gender", "sex")), cols[0])
    age_col = next((c for c in cols if "age" in c.lower()), cols[1] if len(cols) > 1 else cols[0])
    event_col = next((c for c in cols if "event" in c.lower()), cols[2] if len(cols) > 2 else cols[0])
    base_col = None
    for c in cols:
        cl = c.lower()
        if "base" in cl or ("time" in cl and ("base" in cl or "on track" in cl)):
            base_col = c
    if base_col is None:
        if len(cols) >= 5:
            base_col = cols[4]
        else:
            for c in cols:
                if pd.api.types.is_numeric_dtype(df[c]):
                    base_col = c
                    break
    if base_col is None:
        return None

    g = _norm_gender_to_code(gender)
    try:
        age_i = int(str(age).strip())
    except Exception:
        return None
    ev = None if event is None else str(event).strip()
    swimmer_seconds = _parse_time_to_seconds(time_val)
    if g is None or ev is None or swimmer_seconds is None or swimmer_seconds <= 0:
        return None

    # Normalize gender column to 'M'/'F' codes for comparison
    gender_series = df[gender_col].astype(str).str.strip().str.lower()
    gender_series = gender_series.map(lambda x: 'm' if x in ('m','male') else ('f' if x in ('f','female') else x))

    filt = (
        gender_series.str.upper() == str(g)
    ) & (
        df[age_col].astype(str).str.strip() == str(age_i)
    ) & (
        df[event_col].astype(str).str.strip() == ev
    )
    matches = df[filt]
    if matches.empty:
        return None
    base_raw = matches.iloc[0][base_col]
    base_seconds = _parse_time_to_seconds(base_raw)
    if base_seconds is None or base_seconds <= 0:
        return None
    try:
        pts = round(1000.0 * (base_seconds / float(swimmer_seconds)) ** 3.0)
        return int(pts)
    except Exception:
        return None
