# -*- coding: utf-8 -*-
import os
import re
import pandas as pd

USA_RESULTS = 'MOT_Delta_Analysis_Results.csv'
# Handle both old and new folder structures
script_dir = os.path.dirname(os.path.abspath(__file__))
if 'statistical_analysis' in script_dir.lower():
    CAN_WORKBOOK = os.path.join('..', 'data', 'Malaysia On Track Statistical Analysis.xlsx')
    OUT_DIR = os.path.join('..', 'reports')
else:
    CAN_WORKBOOK = 'Malaysia On Track Statistical Analysis.xlsx'
    OUT_DIR = 'reports'
CAN_SHEETS = ['MOT Tables 21', 'MOT Tables 25']  # try in order
CSV_OUT = os.path.join(OUT_DIR, 'Delta_Comparison_USA_vs_Canada.csv')
HTML_OUT = os.path.join(OUT_DIR, 'Delta_Comparison_USA_vs_Canada.html')

TRACK_LABEL_MAP = {
    '1': 'Track 1 (Early)',
    '2': 'Track 2 (Middle)',
    '3': 'Track 3 (Late)',
    'track 1': 'Track 1 (Early)',
    'track 2': 'Track 2 (Middle)',
    'track 3': 'Track 3 (Late)'
}


def load_usa_results() -> pd.DataFrame:
    df = pd.read_csv(USA_RESULTS, encoding='utf-8')
    for c in ['event', 'gender', 'age_from', 'age_to']:
        df[c] = df[c].astype(str)
    for c in ['median_improvement','mean_improvement','std_improvement','q25_improvement','q75_improvement','sample_size']:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce')
    return df


def try_load_canada_table() -> pd.DataFrame | None:
    if not os.path.exists(CAN_WORKBOOK):
        return None
    try:
        xls = pd.ExcelFile(CAN_WORKBOOK)
        for sheet in CAN_SHEETS:
            if sheet in xls.sheet_names:
                return pd.read_excel(CAN_WORKBOOK, sheet_name=sheet)
    except Exception:
        return None
    return None


def to_seconds(val: object) -> float | None:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    s = str(val).strip()
    if s == '':
        return None
    if re.fullmatch(r"\d+(\.\d+)?", s):
        try:
            return float(s)
        except Exception:
            return None
    s = re.sub(r"[^0-9:\.]", "", s)
    if s.count(':') == 0:
        try:
            return float(s)
        except Exception:
            return None
    parts = s.split(':')
    try:
        if len(parts) == 2:
            m = int(parts[0]) if parts[0] else 0
            sec = float(parts[1])
            return m * 60 + sec
        if len(parts) == 3:
            h = int(parts[0]) if parts[0] else 0
            m = int(parts[1]) if parts[1] else 0
            sec = float(parts[2])
            return h * 3600 + m * 60 + sec
    except Exception:
        return None
    return None


def standardize_track_label(label: str) -> str:
    if label is None:
        return ''
    s = str(label).strip().lower()
    # Exact map first
    if s in TRACK_LABEL_MAP:
        return TRACK_LABEL_MAP[s]
    # Contains number?
    for k, v in TRACK_LABEL_MAP.items():
        if k in s:
            return v
    # Fallback to cleaned original
    return str(label).strip()


def normalize_canada(df: pd.DataFrame) -> pd.DataFrame | None:
    if df is None or df.empty:
        return None
    cols = {c.lower().strip(): c for c in df.columns}
    # Base fields
    gender_col = next((cols[k] for k in cols if k in ['gender','g']), None)
    event_col = next((cols[k] for k in cols if k in ['event','evt']), None)
    age_col = next((cols[k] for k in cols if k in ['age','ages']), None)
    if not (gender_col and event_col and age_col):
        return None

    # Case A: Wide table with separate track columns
    wide_track_cols = [orig for key, orig in cols.items() if 'track' in key and all(t not in key for t in ['canada track', 'track time'])]
    # Filter out obvious non-time fields
    wide_track_cols = [c for c in wide_track_cols if 'aqua' not in c.lower()]

    if wide_track_cols:
        slim = df[[gender_col, event_col, age_col] + wide_track_cols].copy()
        slim.columns = ['gender', 'event', 'age'] + [re.sub(r"\s+", " ", c).strip() for c in wide_track_cols]
        try:
            slim['age'] = pd.to_numeric(slim['age'], errors='coerce').astype('Int64')
        except Exception:
            return None
        slim = slim[slim['age'].between(15, 18, inclusive='both')]
        # Convert times
        for c in slim.columns:
            if c not in ['gender','event','age']:
                slim[c] = slim[c].apply(to_seconds)
        return slim

    # Case B: Long-like table with 'Canada Track' + a time column per row
    canada_track_label = next((cols[k] for k in cols if 'canada track' == k), None)
    time_cols = [cols[k] for k in cols if k in ['canada track time','canada track time in seconds','time seconds','time']]
    # If not exact key matches, try partial
    if not canada_track_label:
        canada_track_label = next((orig for key, orig in cols.items() if 'canada track' in key), None)
    if not time_cols:
        time_cols = [orig for key, orig in cols.items() if 'track time' in key or key.endswith('in seconds') or key == 'time']

    if canada_track_label and time_cols:
        # Keep only required columns
        use_time_col = time_cols[0]
        slim = df[[gender_col, event_col, age_col, canada_track_label, use_time_col]].copy()
        slim.columns = ['gender','event','age','track_label','time_val']
        try:
            slim['age'] = pd.to_numeric(slim['age'], errors='coerce').astype('Int64')
        except Exception:
            return None
        slim = slim[slim['age'].between(15, 18, inclusive='both')]
        # Standardize track label
        slim['track'] = slim['track_label'].apply(standardize_track_label)
        # Convert time to seconds
        slim['time_val'] = slim['time_val'].apply(to_seconds)
        # Pivot to wide
        pivot = slim.pivot_table(index=['gender','event','age'], columns='track', values='time_val', aggfunc='first').reset_index()
        # Rename track columns to consistent names: ensure only our three tracks appear
        # Already standardized in column names
        return pivot

    # If neither schema matched, give up
    return None


def compute_track_deltas(can: pd.DataFrame) -> pd.DataFrame:
    value_cols = [c for c in can.columns if c not in ['gender','event','age']]
    long = can.melt(id_vars=['gender','event','age'], value_vars=value_cols, var_name='track', value_name='time')
    # Standardize track labels
    long['track'] = long['track'].apply(standardize_track_label)
    long = long.sort_values(['gender','event','track','age'])
    long['age_to'] = long['age'] + 1
    next_time = long.groupby(['gender','event','track'])['time'].shift(-1)
    delta = pd.to_numeric(long['time'], errors='coerce') - pd.to_numeric(next_time, errors='coerce')
    long['delta'] = delta.clip(lower=0)
    deltas = long[long['age'].isin([15,16,17])].dropna(subset=['delta'])
    deltas['age_from'] = deltas['age'].astype(str)
    deltas['age_to'] = deltas['age_to'].astype(str)
    return deltas[['gender','event','track','age_from','age_to','delta']]


def build_comparison():
    usa = load_usa_results()
    usa_sel = usa[['gender','event','age_from','age_to','median_improvement','mean_improvement','std_improvement','q25_improvement','q75_improvement','sample_size']].copy()

    can_raw = try_load_canada_table()
    can_norm = normalize_canada(can_raw) if can_raw is not None else None
    can_deltas = compute_track_deltas(can_norm) if can_norm is not None else None

    if can_deltas is None:
        usa_sel['can_track'] = pd.NA
        usa_sel['can_delta'] = pd.NA
        merged = usa_sel
    else:
        merged = usa_sel.merge(
            can_deltas,
            how='left',
            left_on=['gender','event','age_from','age_to'],
            right_on=['gender','event','age_from','age_to']
        ).rename(columns={'track':'can_track','delta':'can_delta'})
        merged['delta_diff_seconds'] = pd.to_numeric(merged['median_improvement'], errors='coerce') - pd.to_numeric(merged['can_delta'], errors='coerce')

    return merged, can_deltas


def summarize_tracks(can_deltas: pd.DataFrame | None) -> pd.DataFrame | None:
    if can_deltas is None or can_deltas.empty:
        return None
    can_deltas['delta'] = pd.to_numeric(can_deltas['delta'], errors='coerce')
    pivot = can_deltas.pivot_table(
        index=['gender','event','track'],
        columns=['age_from','age_to'],
        values='delta',
        aggfunc='mean'
    )
    pivot.columns = [f"{a}->{b}" for a, b in pivot.columns]
    pivot = pivot.reset_index()
    delta_cols = [c for c in pivot.columns if '->' in c]
    pivot['avg_delta_across_track'] = pivot[delta_cols].mean(axis=1, skipna=True)
    pivot['num_transitions'] = pivot[delta_cols].count(axis=1)
    return pivot


def write_reports(merged: pd.DataFrame, can_deltas: pd.DataFrame | None) -> None:
    os.makedirs(OUT_DIR, exist_ok=True)
    merged.to_csv(CSV_OUT, index=False, encoding='utf-8')

    rows1 = []
    for _, r in merged.iterrows():
        def fmt(x):
            return '' if pd.isna(x) else f"{float(x):.3f}"
        rows1.append(
            f"<tr>"
            f"<td>{r.get('gender','')}</td>"
            f"<td>{r.get('event','')}</td>"
            f"<td>{r.get('age_from','')}</td>"
            f"<td>{r.get('age_to','')}</td>"
            f"<td>{int(r.get('sample_size') or 0)}</td>"
            f"<td>{fmt(r.get('median_improvement'))}</td>"
            f"<td>{'' if pd.isna(r.get('can_track')) else r.get('can_track')}</td>"
            f"<td>{fmt(r.get('can_delta'))}</td>"
            f"<td>{fmt(r.get('delta_diff_seconds'))}</td>"
            f"</tr>"
        )

    rows2 = []
    track_summary = summarize_tracks(can_deltas)
    legend = (
        "<div style='margin:8px 0;padding:8px;border:1px solid #eee;background:#fafafa'>"
        "<strong>Track legend:</strong> Track 1 (Early), Track 2 (Middle), Track 3 (Late)."
        "</div>"
    )
    if track_summary is not None:
        trans_cols = [c for c in track_summary.columns if '->' in c]
        head2 = (
            "<tr><th>Gender</th><th>Event</th><th>Track</th>" +
            ''.join(f"<th>{c}</th>" for c in trans_cols) +
            "<th>Avg Δ across track</th><th># transitions</th></tr>"
        )
        for _, r in track_summary.iterrows():
            cells = ''.join(f"<td>{'' if pd.isna(r.get(c)) else f'{float(r.get(c)):.3f}'}</td>" for c in trans_cols)
            rows2.append(
                f"<tr><td>{r.get('gender','')}</td><td>{r.get('event','')}</td><td>{r.get('track','')}</td>" +
                cells +
                f"<td>{'' if pd.isna(r.get('avg_delta_across_track')) else f'{float(r.get('avg_delta_across_track')):.3f}'}</td>"+
                f"<td>{int(r.get('num_transitions') or 0)}</td></tr>"
            )

    html = (
        "<!doctype html><meta charset='utf-8'><title>USA vs Canada Deltas</title>"
        "<style>body{font-family:system-ui,Segoe UI,Arial,sans-serif;margin:24px}table{border-collapse:collapse;width:100%}th,td{border:1px solid #ddd;padding:6px;font-size:14px}th{background:#f5f5f5;text-align:left}h2{margin-top:24px}</style>"
        "<h1>USA Median Deltas vs Canada On Track (Track 1–3)</h1>"
        "<p>Canada deltas computed as time(age) − time(age+1), negatives clamped to 0.</p>"
        "<h2>Table 1 — Per-age transition comparison</h2>"
        "<table><thead><tr><th>Gender</th><th>Event</th><th>From</th><th>To</th><th>n (USA)</th><th>USA Median Δ (s)</th><th>Canada Track</th><th>Canada Δ (s)</th><th>USA−Canada Δ (s)</th></tr></thead><tbody>" + "".join(rows1) + "</tbody></table>"
        + legend +
        "<h2>Table 2 — Track profiles (per-age deltas and overall average)</h2>" +
        ("<table><thead>" + head2 + "</thead><tbody>" + "".join(rows2) + "</tbody></table>" if rows2 else "<p>No Canada track data available.</p>")
    )
    with open(HTML_OUT, 'w', encoding='utf-8') as f:
        f.write(html)


def main() -> None:
    merged, can_deltas = build_comparison()
    write_reports(merged, can_deltas)
    print(f"Wrote: {CSV_OUT}")
    print(f"Wrote: {HTML_OUT}")


if __name__ == '__main__':
    main()
