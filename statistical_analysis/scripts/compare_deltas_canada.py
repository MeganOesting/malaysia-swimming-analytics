# -*- coding: utf-8 -*-
"""
Compare USA delta analyses with Canada On Track reference deltas
Uses SQLite database for both USA and Canada data (no Excel dependency)
"""
import os
import pandas as pd
from db_schema import get_conn

# Handle both old and new folder structures
script_dir = os.path.dirname(os.path.abspath(__file__))
if 'statistical_analysis' in script_dir.lower():
    # New structure: statistical_analysis/reports/ (from scripts/ go up one level, then into reports/)
    OUT_DIR = os.path.join(script_dir, '..', 'reports')
    USA_RESULTS_CSV = os.path.join(script_dir, '..', 'MOT_Delta_Analysis_Results.csv')  # Fallback
else:
    # Old structure: reports/ in same directory as script
    OUT_DIR = os.path.join(script_dir, 'reports')
    USA_RESULTS_CSV = os.path.join(script_dir, 'MOT_Delta_Analysis_Results.csv')  # Fallback

# Normalize paths to absolute
OUT_DIR = os.path.abspath(OUT_DIR)
USA_RESULTS_CSV = os.path.abspath(USA_RESULTS_CSV) if not os.path.isabs(USA_RESULTS_CSV) else USA_RESULTS_CSV

CSV_OUT = os.path.join(OUT_DIR, 'Delta_Comparison_USA_vs_Canada.csv')
HTML_OUT = os.path.join(OUT_DIR, 'Delta_Comparison_USA_vs_Canada.html')

# Track label mapping (for display purposes)
# Database stores track as integer: 1, 2, 3
# These map to: Track 1 (Early), Track 2 (Middle), Track 3 (Late)


def load_usa_results() -> pd.DataFrame:
    """Load USA delta results from SQLite database"""
    try:
        conn = get_conn()
        query = """
            SELECT 
                gender,
                event,
                age_from,
                age_to,
                sample_size,
                median_improvement,
                mean_improvement,
                std_improvement,
                q25_improvement,
                q75_improvement
            FROM usa_age_deltas
            ORDER BY gender, event, age_from, age_to
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        # Convert types
        for c in ['event', 'gender', 'age_from', 'age_to']:
            df[c] = df[c].astype(str)
        for c in ['median_improvement','mean_improvement','std_improvement','q25_improvement','q75_improvement','sample_size']:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors='coerce')
        
        print(f"✅ Loaded {len(df)} USA delta analyses from database")
        return df
    except Exception as e:
        print(f"⚠️  Error loading from database: {e}")
        print(f"   Falling back to CSV: {USA_RESULTS_CSV}")
        # Fallback to CSV
        if os.path.exists(USA_RESULTS_CSV):
            df = pd.read_csv(USA_RESULTS_CSV, encoding='utf-8')
    for c in ['event', 'gender', 'age_from', 'age_to']:
        df[c] = df[c].astype(str)
    for c in ['median_improvement','mean_improvement','std_improvement','q25_improvement','q75_improvement','sample_size']:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce')
    return df
        else:
            raise FileNotFoundError(f"Neither database nor CSV file found")


def load_canada_from_db() -> pd.DataFrame | None:
    """Load Canada On Track data from SQLite database"""
    try:
        conn = get_conn()
        query = """
            SELECT 
                gender,
                event,
                age,
                track,
                time_seconds,
                time_text
            FROM canada_on_track
            WHERE age BETWEEN 15 AND 18
            ORDER BY gender, event, track, age
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if df.empty:
            print("⚠️  No Canada data found in database")
            return None
        
        print(f"✅ Loaded {len(df)} Canada track entries from database")
        return df
    except Exception as e:
        print(f"⚠️  Error loading Canada data from database: {e}")
    return None


# Note: to_seconds and standardize_track_label functions removed
# Database already provides time_seconds as numeric and track as integer (1,2,3)


def normalize_canada_from_db(df: pd.DataFrame) -> pd.DataFrame | None:
    """Normalize Canada data from database format to wide format for delta computation"""
    if df is None or df.empty:
        return None
    
    # Database format: gender, event, age, track, time_seconds, time_text
    # Convert to wide format: gender, event, age, Track 1 (Early), Track 2 (Middle), Track 3 (Late)
    
    # Create track labels
    track_map = {
        1: 'Track 1 (Early)',
        2: 'Track 2 (Middle)',
        3: 'Track 3 (Late)'
    }
    df['track_label'] = df['track'].map(track_map)
    
    # Pivot to wide format
    pivot = df.pivot_table(
        index=['gender', 'event', 'age'],
        columns='track_label',
        values='time_seconds',
        aggfunc='first'
    ).reset_index()
    
        return pivot


def compute_track_deltas(can: pd.DataFrame) -> pd.DataFrame:
    """Compute Canada track deltas from wide format data"""
    if can is None or can.empty:
        return None
    
    # Get track columns (exclude gender, event, age)
    value_cols = [c for c in can.columns if c not in ['gender','event','age']]
    
    # Melt to long format
    long = can.melt(
        id_vars=['gender','event','age'],
        value_vars=value_cols,
        var_name='track',
        value_name='time'
    )
    
    # Remove rows with missing times
    long = long.dropna(subset=['time'])
    
    # Sort by gender, event, track, age
    long = long.sort_values(['gender','event','track','age'])
    
    # Compute deltas: time(age) - time(age+1)
    # Positive delta = improvement (faster time at older age)
    long['age_to'] = long['age'] + 1
    
    # Calculate next_time within each track group
    long['next_time'] = long.groupby(['gender','event','track'])['time'].shift(-1)
    
    # Calculate delta: older age should be faster, so delta = time(age) - time(age+1)
    long['delta'] = pd.to_numeric(long['time'], errors='coerce') - pd.to_numeric(long['next_time'], errors='coerce')
    
    # Clamp negative deltas to 0 (no negative improvements)
    long['delta'] = long['delta'].clip(lower=0)
    
    # Keep only transitions 15->16, 16->17, 17->18
    # Only keep rows where we have both current age time AND next age time (valid delta)
    deltas = long[long['age'].isin([15,16,17])].copy()
    # Filter to rows where next_time exists (we have both ages for that track)
    deltas = deltas[deltas['next_time'].notna()]
    # Drop any rows where delta is still NaN (shouldn't happen if next_time exists, but be safe)
    deltas = deltas.dropna(subset=['delta'])
    
    # Convert ages to strings for merging
    deltas['age_from'] = deltas['age'].astype(int).astype(str)
    deltas['age_to'] = deltas['age_to'].astype(int).astype(str)
    
    return deltas[['gender','event','track','age_from','age_to','delta']]


def build_comparison():
    """Build comparison between USA deltas and Canada track deltas"""
    # Load USA deltas from database
    usa = load_usa_results()
    usa_sel = usa[['gender','event','age_from','age_to','median_improvement','mean_improvement','std_improvement','q25_improvement','q75_improvement','sample_size']].copy()

    # Load Canada data from database
    can_raw = load_canada_from_db()
    can_norm = normalize_canada_from_db(can_raw) if can_raw is not None else None
    can_deltas = compute_track_deltas(can_norm) if can_norm is not None else None

    if can_deltas is None or can_deltas.empty:
        print("⚠️  No Canada deltas available - USA data only")
        usa_sel['can_track'] = pd.NA
        usa_sel['can_delta'] = pd.NA
        merged = usa_sel
    else:
        # Merge: Each USA transition can match multiple Canada tracks (Track 1, 2, 3)
        # This creates one row per USA transition per Canada track
        merged = usa_sel.merge(
            can_deltas,
            how='left',
            on=['gender','event','age_from','age_to'],
            suffixes=('_usa', '_can')
        )
        # Rename for clarity
        merged = merged.rename(columns={'track':'can_track','delta':'can_delta'})
        # Calculate difference: USA median improvement - Canada delta
        merged['delta_diff_seconds'] = pd.to_numeric(merged['median_improvement'], errors='coerce') - pd.to_numeric(merged['can_delta'], errors='coerce')
        
        # Debug: Check a sample row
        sample = merged[(merged['gender']=='F') & (merged['event']=='50 Free') & (merged['age_from']=='16') & (merged['age_to']=='17')]
        if not sample.empty:
            print(f"🔍 Debug F 50 Free 16→17: can_track='{sample.iloc[0]['can_track']}', can_delta={sample.iloc[0]['can_delta']}")
        
        print(f"✅ Merged USA and Canada data: {len(merged)} rows")
        print(f"   (USA transitions with Canada track matches)")

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


# Event order: short to long, then Free, Back, Breast, Fly, IM
EVENT_ORDER = [
    '50 Free', '100 Free', '200 Free', '400 Free', '800 Free', '1500 Free',
    '100 Back', '200 Back', '100 Breast', '200 Breast', '100 Fly', '200 Fly',
    '200 IM', '400 IM'
]

def sort_events(df: pd.DataFrame) -> pd.DataFrame:
    """Sort dataframe by event in canonical order"""
    if 'event' not in df.columns:
        return df
    df = df.copy()
    df['event_order'] = df['event'].map({e: i for i, e in enumerate(EVENT_ORDER)})
    
    # Determine sort columns based on what exists in the dataframe
    sort_cols = ['gender', 'event_order']
    
    if 'age_from' in df.columns and 'age_to' in df.columns:
        # This is the merged dataframe with age transitions
        sort_cols.extend(['age_from', 'age_to'])
    elif 'track' in df.columns:
        # This is the track_summary dataframe
        sort_cols.append('track')
    
    df = df.sort_values(sort_cols).drop('event_order', axis=1)
    return df


def write_reports(merged: pd.DataFrame, can_deltas: pd.DataFrame | None) -> None:
    os.makedirs(OUT_DIR, exist_ok=True)
    # Sort events in canonical order
    merged = sort_events(merged)
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
    if track_summary is not None:
        track_summary = sort_events(track_summary)
    
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

    footer = (
        "<hr style='margin:32px 0;border:none;border-top:1px solid #ccc'>"
        "<p style='font-size:13px;color:#666;line-height:1.0'>"
        "<strong>Generated from statistical analysis database.</strong> "
        "<strong>Data sources:</strong> "
        "• Canada On Track reference times are from April 2025. "
        "See <a href='https://www.swimming.ca/on-track-times/' target='_blank'>Canada On Track website</a> and "
        "<a href='https://www.swimming.ca/wp-content/uploads/2025/04/On-Track-Times-for-SNC-Website-APRIL-2025.pdf' target='_blank'>April 2025 PDF</a>. "
        "• USA Swimming season rankings are from the 2021-2022, 2022-2023, 2023-2024, and 2024-2025 seasons. "
        "USA Swimming seasons run from September 1 of the first year to August 31 of the second year. "
        "• USA Swimming ages are the age of the swimmer on the first day of competition, not their birth year age."
        "</p>"
            )

    html = (
        "<!doctype html>"
        "<html lang='en'>"
        "<head>"
        "<meta charset='utf-8'>"
        "<title>Improvement Analysis - USA vs Canada</title>"
        "<style>"
        "body{font-family:system-ui,Segoe UI,Arial,sans-serif;margin:24px;background:white}"
        "h1{color:#CE1126;border-bottom:3px solid #CE1126;padding-bottom:10px;margin-bottom:8px}"
        "h1 .subtitle{display:block;font-size:0.6em;font-weight:normal;color:#333;margin-top:8px;border:none;padding:0}"
        "table{border-collapse:collapse;width:100%}"
        "th,td{border:1px solid #ccc;padding:6px;font-size:14px}"
        "th{background:#CE1126;color:#fff;text-align:left;font-weight:600}"
        "tr:nth-child(even){background:#fafafa}"
        "tr:hover{background:#f5f5f5}"
        "h2{margin-top:24px;color:#000;border-bottom:2px solid #00247D;padding-bottom:6px}"
        "p{color:#333}"
        "a{color:#CE1126}"
        "a:hover{color:#000;text-decoration:underline}"
        "</style>"
        "</head>"
        "<body>"
        "<h1>Improvement Analysis<span class='subtitle'>(A comprehensive analysis of improvement patterns for competitive swimmers ages 15-18)</span></h1>"
        "<p>Canada deltas computed as time(age) − time(age+1), negatives clamped to 0. Track 1 (Early), Track 2 (Middle), Track 3 (Late).</p>"
        "<h2>Table 1 — Per-age transition comparison</h2>"
        "<table><thead><tr><th>Gender</th><th>Event</th><th>From</th><th>To</th><th>n (USA)</th><th>USA Median Δ (s)</th><th>Canada Track</th><th>Canada Δ (s)</th><th>USA−Canada Δ (s)</th></tr></thead><tbody>" + "".join(rows1) + "</tbody></table>"
        "<h2>Table 2 — Track profiles (per-age deltas and overall average)</h2>" +
        ("<table><thead>" + head2 + "</thead><tbody>" + "".join(rows2) + "</tbody></table>" if rows2 else "<p>No Canada track data available.</p>")
        + footer +
        "</body></html>"
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
