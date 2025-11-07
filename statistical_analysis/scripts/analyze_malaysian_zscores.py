#!/usr/bin/env python3
"""
Analyze Malaysian Swimmers' Z-Scores Against USA Reference Data
Phase 1 of Malaysian Data Integration

Compares Malaysian swimmers' current performance to USA reference curves by:
1. Extracting Malaysian swimmers from database (age on first day of competition)
2. Calculating z-scores against USA Period Data
3. Identifying which z-score ranges Malaysian swimmers fall into
4. Generating comparison visualization and report
"""

import os
import sys
import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

script_dir = os.path.dirname(os.path.abspath(__file__))
if 'statistical_analysis' in script_dir.lower():
    STATS_DB = os.path.join(script_dir, '..', 'database', 'statistical.db')
    MALAYSIA_DB = os.path.join(script_dir, '..', '..', 'database', 'malaysia_swimming.db')
    PERIOD_DATA_BASE = os.path.join(script_dir, '..', 'data', 'Period Data')
    REPORTS_DIR = os.path.join(script_dir, '..', 'reports')
else:
    STATS_DB = os.path.join('..', 'database', 'statistical.db')
    MALAYSIA_DB = os.path.join('..', 'database', 'malaysia_swimming.db')
    PERIOD_DATA_BASE = os.path.join('data', 'Period Data')
    REPORTS_DIR = 'reports'

# Canonical events mapping
EVENT_MAP = {
    (50, 'FREE'): '50 Free',
    (100, 'FREE'): '100 Free',
    (200, 'FREE'): '200 Free',
    (400, 'FREE'): '400 Free',
    (800, 'FREE'): '800 Free',
    (1500, 'FREE'): '1500 Free',
    (100, 'BACK'): '100 Back',
    (200, 'BACK'): '200 Back',
    (100, 'BREAST'): '100 Breast',
    (200, 'BREAST'): '200 Breast',
    (100, 'FLY'): '100 Fly',
    (200, 'FLY'): '200 Fly',
    (200, 'IM'): '200 IM',
    (400, 'IM'): '400 IM',
}

# Z-score range labels
ZSCORE_RANGES = [
    (float('-inf'), -2.0, 'Extreme Lower (< -2.0 z)'),
    (-2.0, -1.5, 'Very Lower (-2.0 to -1.5 z)'),
    (-1.5, -1.0, 'Lower (-1.5 to -1.0 z)'),
    (-1.0, -0.5, 'Below Average (-1.0 to -0.5 z)'),
    (-0.5, 0, 'Below Average (-0.5 to 0 z)'),
    (0, 0.5, 'Average (0 to 0.5 z)'),
    (0.5, 1.0, 'Above Average (0.5 to 1.0 z)'),
    (1.0, 1.5, 'Top 15.9% (1.0 to 1.5 z)'),
    (1.5, 2.0, 'Top 6.7% (1.5 to 2.0 z)'),
    (2.0, float('inf'), 'Top 2.5% (≥ 2.0 z)'),
]


def find_usa_reference_file(gender: str, event: str, age: int) -> str:
    """Find the most recent USA Period Data file for reference."""
    if not os.path.exists(PERIOD_DATA_BASE):
        return None
    
    period_folders = sorted(
        [d for d in os.listdir(PERIOD_DATA_BASE) if os.path.isdir(os.path.join(PERIOD_DATA_BASE, d))],
        reverse=True
    )
    
    for period in period_folders:
        event_folder_pattern = f"{gender} {event} {period}"
        event_folder_path = os.path.join(PERIOD_DATA_BASE, period, event_folder_pattern)
        
        if os.path.exists(event_folder_path):
            file_pattern = f"{gender} {event} {age} {period}.txt"
            file_path = os.path.join(event_folder_path, file_pattern)
            
            if os.path.exists(file_path):
                return file_path
    
    return None


def load_usa_reference_data(gender: str, event: str, age: int) -> tuple:
    """Load USA reference data and return (times_list, mean, std_dev)."""
    file_path = find_usa_reference_file(gender, event, age)
    
    if not file_path:
        return None, None, None
    
    try:
        # Load tab-separated file
        df = pd.read_csv(file_path, sep='\t', encoding='utf-8', on_bad_lines='skip')
        
        # Find time column (may be 'Time', 'time', etc.)
        time_col = None
        for col in df.columns:
            if 'time' in col.lower() and 'seconds' not in col.lower():
                time_col = col
                break
        
        if time_col is None:
            # Try to find numeric column that looks like times
            for col in df.columns:
                if df[col].dtype in [np.float64, np.float32, np.int64, np.int32]:
                    sample_vals = df[col].dropna().head(10)
                    if len(sample_vals) > 0 and all(20 < v < 3600 for v in sample_vals):  # Reasonable time range
                        time_col = col
                        break
        
        if time_col is None:
            print(f"Warning: Could not find time column in {file_path}")
            return None, None, None
        
        # Convert to seconds if needed (handle MM:SS.mm format)
        times = []
        for val in df[time_col].dropna():
            if isinstance(val, str):
                if ':' in val:
                    parts = val.split(':')
                    if len(parts) == 2:
                        times.append(float(parts[0]) * 60 + float(parts[1]))
                    else:
                        try:
                            times.append(float(val))
                        except:
                            pass
                else:
                    try:
                        times.append(float(val))
                    except:
                        pass
            else:
                times.append(float(val))
        
        if len(times) == 0:
            return None, None, None
        
        times_array = np.array(times)
        mean = np.mean(times_array)
        std_dev = np.std(times_array, ddof=1) if len(times_array) > 1 else 0.0
        
        return times_array.tolist(), mean, std_dev
        
    except Exception as e:
        print(f"Error loading USA reference file {file_path}: {e}")
        return None, None, None


def calculate_zscore(malaysian_time: float, usa_mean: float, usa_std: float) -> float:
    """Calculate z-score: positive = faster (better), negative = slower."""
    if usa_std == 0:
        return 0.0
    return (usa_mean - malaysian_time) / usa_std


def categorize_zscore(z: float) -> str:
    """Categorize z-score into range."""
    for min_z, max_z, label in ZSCORE_RANGES:
        if min_z <= z < max_z:
            return label
    # Handle edge case
    if z >= 2.0:
        return 'Top 2.5% (≥ 2.0 z)'
    return 'Extreme Lower (< -2.0 z)'


def load_malaysian_data():
    """Load Malaysian swimmers' results from database."""
    if not os.path.exists(MALAYSIA_DB):
        print(f"Malaysia database not found: {MALAYSIA_DB}")
        print("Trying alternative location...")
        alt_paths = [
            os.path.join(script_dir, '..', '..', 'times_database', 'database', 'malaysia_swimming.db'),
            os.path.join(script_dir, '..', '..', 'times_database', 'database', 'swimming.db'),
        ]
        for alt_path in alt_paths:
            if os.path.exists(alt_path):
                print(f"Found database at: {alt_path}")
                global MALAYSIA_DB
                MALAYSIA_DB = alt_path
                break
        else:
            return None
    
    conn = sqlite3.connect(MALAYSIA_DB)
    
    # Query Malaysian swimmers
    # We need: name, gender, age (on first day of competition), event, time_seconds, meet_date
    # Age calculation: need meet_date and birth_date from athletes table
    
    query = """
    SELECT 
        r.athlete_name,
        r.gender,
        r.age,  -- This should be age on first day of competition
        r.distance,
        r.stroke,
        r.time_seconds,
        r.meet_date,
        m.name as meet_name,
        a.birth_date
    FROM results r
    JOIN meets m ON r.meet_id = m.id
    LEFT JOIN athletes a ON r.athlete_id = a.id
    WHERE (r.is_foreign = 0 OR r.is_foreign IS NULL OR r.is_foreign = FALSE)
        AND r.age BETWEEN 15 AND 18
        AND r.time_seconds IS NOT NULL
        AND r.time_seconds > 0
    ORDER BY r.gender, r.distance, r.stroke, r.age, r.time_seconds
    """
    
    try:
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if len(df) == 0:
            print("No Malaysian swimmer data found in database")
            return None
        
        # Map to canonical events
        df['event'] = df.apply(
            lambda row: EVENT_MAP.get((row['distance'], row['stroke'].upper()), None),
            axis=1
        )
        
        # Filter out unmapped events
        df = df[df['event'].notna()].copy()
        
        # Recalculate age on first day of competition if we have birth_date
        if 'birth_date' in df.columns and 'meet_date' in df.columns:
            for idx, row in df.iterrows():
                if pd.notna(row['birth_date']) and pd.notna(row['meet_date']):
                    try:
                        birth = pd.to_datetime(row['birth_date'])
                        meet = pd.to_datetime(row['meet_date'])
                        # Age on first day of competition
                        age_calc = meet.year - birth.year - ((meet.month, meet.day) < (birth.month, birth.day))
                        df.at[idx, 'age'] = age_calc
                    except:
                        pass  # Keep existing age if calculation fails
        
        # Filter to ages 15-18
        df = df[df['age'].between(15, 18)].copy()
        
        print(f"Loaded {len(df)} Malaysian swimmer results")
        return df
        
    except Exception as e:
        print(f"Error querying Malaysian database: {e}")
        import traceback
        traceback.print_exc()
        conn.close()
        return None


def analyze_malaysian_zscores():
    """Main analysis function."""
    print("=" * 80)
    print("MALAYSIAN SWIMMERS Z-SCORE ANALYSIS")
    print("Phase 1: Comparing Malaysian Performance to USA Reference Curves")
    print("=" * 80)
    
    # Load Malaysian data
    print("\n1. Loading Malaysian swimmer data...")
    malaysia_df = load_malaysian_data()
    
    if malaysia_df is None or len(malaysia_df) == 0:
        print("❌ No Malaysian data found. Please ensure meet data has been loaded into the database.")
        return
    
    print(f"   ✅ Loaded {len(malaysia_df)} results from {malaysia_df['athlete_name'].nunique()} unique swimmers")
    
    # Calculate z-scores for each result
    print("\n2. Calculating z-scores against USA reference data...")
    
    results = []
    missing_refs = set()
    
    for idx, row in malaysia_df.iterrows():
        gender = row['gender']
        event = row['event']
        age = int(row['age'])
        time_sec = float(row['time_seconds'])
        
        # Load USA reference
        usa_times, usa_mean, usa_std = load_usa_reference_data(gender, event, age)
        
        if usa_mean is None:
            missing_refs.add(f"{gender} {event} {age}")
            continue
        
        # Calculate z-score
        z = calculate_zscore(time_sec, usa_mean, usa_std)
        z_range = categorize_zscore(z)
        
        results.append({
            'name': row['athlete_name'],
            'gender': gender,
            'event': event,
            'age': age,
            'time_seconds': time_sec,
            'time_text': row.get('time_string', f"{time_sec:.2f}"),
            'meet_name': row.get('meet_name', ''),
            'meet_date': row.get('meet_date', ''),
            'usa_mean': usa_mean,
            'usa_std': usa_std,
            'z_score': z,
            'z_range': z_range
        })
    
    if len(results) == 0:
        print("❌ No results with valid USA reference data found")
        if missing_refs:
            print(f"\nMissing USA references for: {sorted(missing_refs)}")
        return
    
    results_df = pd.DataFrame(results)
    
    print(f"   ✅ Calculated z-scores for {len(results_df)} results")
    
    if missing_refs:
        print(f"\n   ⚠️  Missing USA references for {len(missing_refs)} event/age combinations")
        print(f"   Missing: {', '.join(sorted(list(missing_refs))[:10])}{'...' if len(missing_refs) > 10 else ''}")
    
    # Generate summary statistics
    print("\n3. Generating summary statistics...")
    
    # Overall statistics
    overall_stats = {
        'total_results': len(results_df),
        'unique_swimmers': results_df['name'].nunique(),
        'avg_z_score': results_df['z_score'].mean(),
        'median_z_score': results_df['z_score'].median(),
        'min_z_score': results_df['z_score'].min(),
        'max_z_score': results_df['z_score'].max(),
    }
    
    # By z-score range
    range_counts = results_df['z_range'].value_counts().to_dict()
    
    # By event
    event_stats = results_df.groupby(['gender', 'event']).agg({
        'z_score': ['count', 'mean', 'median', 'min', 'max'],
        'name': 'nunique'
    }).round(3)
    
    # By age
    age_stats = results_df.groupby(['gender', 'age']).agg({
        'z_score': ['count', 'mean', 'median'],
    }).round(3)
    
    # Save detailed CSV
    csv_path = os.path.join(REPORTS_DIR, 'Malaysian_ZScore_Analysis.csv')
    results_df.to_csv(csv_path, index=False, encoding='utf-8')
    print(f"   ✅ Saved detailed results: {csv_path}")
    
    # Generate HTML report
    print("\n4. Generating HTML report...")
    html_path = os.path.join(REPORTS_DIR, 'Malaysian_vs_USA_ZScore_Comparison.html')
    generate_html_report(results_df, overall_stats, range_counts, event_stats, age_stats, html_path)
    print(f"   ✅ Saved HTML report: {html_path}")
    
    # Print summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total Malaysian results analyzed: {overall_stats['total_results']}")
    print(f"Unique swimmers: {overall_stats['unique_swimmers']}")
    print(f"Average z-score: {overall_stats['avg_z_score']:.3f}")
    print(f"Median z-score: {overall_stats['median_z_score']:.3f}")
    print(f"Z-score range: {overall_stats['min_z_score']:.3f} to {overall_stats['max_z_score']:.3f}")
    print(f"\nZ-Score Range Distribution:")
    for range_name, count in sorted(range_counts.items(), key=lambda x: x[1], reverse=True):
        pct = (count / len(results_df)) * 100
        print(f"  {range_name}: {count} ({pct:.1f}%)")
    
    print(f"\n✅ Analysis complete! See {html_path}")


def generate_html_report(results_df, overall_stats, range_counts, event_stats, age_stats, output_path):
    """Generate HTML comparison report."""
    
    # Calculate percentages for z-score ranges
    range_data = []
    for range_name, count in sorted(range_counts.items(), key=lambda x: x[1], reverse=True):
        pct = (count / len(results_df)) * 100
        range_data.append({
            'range': range_name,
            'count': count,
            'pct': pct
        })
    
    # Build event stats table
    event_rows = []
    for (gender, event), stats in event_stats.iterrows():
        event_rows.append({
            'gender': gender,
            'event': event,
            'count': int(stats[('z_score', 'count')]),
            'avg_z': stats[('z_score', 'mean')],
            'median_z': stats[('z_score', 'median')],
            'min_z': stats[('z_score', 'min')],
            'max_z': stats[('z_score', 'max')],
            'unique_swimmers': int(stats[('name', 'nunique')])
        })
    
    # Build age stats table
    age_rows = []
    for (gender, age), stats in age_stats.iterrows():
        age_rows.append({
            'gender': gender,
            'age': int(age),
            'count': int(stats[('z_score', 'count')]),
            'avg_z': stats[('z_score', 'mean')],
            'median_z': stats[('z_score', 'median')]
        })
    
    html_content = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Malaysian vs USA Z-Score Comparison</title>
<style>
body{{font-family:system-ui,Segoe UI,Arial,sans-serif;margin:24px;color:#000;max-width:1400px;background:white}}
h1{{margin:0 0 16px;color:#CE1126;border-bottom:3px solid #CE1126;padding-bottom:10px}}
h2{{color:#000;margin-top:30px;margin-bottom:15px;border-bottom:2px solid #00247D;padding-bottom:6px}}
table{{border-collapse:collapse;width:100%;margin:15px 0}}
th,td{{border:1px solid #ccc;padding:8px;text-align:left;color:#000}}
th{{background:#CE1126;color:#fff;font-weight:600}}
tr:nth-child(even){{background:#fafafa}}
tr:hover{{background:#f5f5f5}}
.summary-box{{background:white;border-left:4px solid #CE1126;padding:16px;margin:20px 0}}
a{{color:#CE1126;text-decoration:none}}
a:hover{{color:#000;text-decoration:underline}}
.stat-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:15px;margin:20px 0}}
.stat-card{{background:white;border:1px solid #ccc;padding:12px;border-radius:4px;text-align:center}}
.stat-value{{font-size:1.8em;font-weight:bold;color:#CE1126;margin:5px 0}}
.stat-label{{color:#000;font-size:0.9em}}
.positive{{color:#00247D;font-weight:600}}
.negative{{color:#CE1126;font-weight:600}}
</style>
</head>
<body>
<h1>Malaysian Swimmers vs USA Reference: Z-Score Analysis</h1>

<div class="summary-box">
<h2>Overview</h2>
<p>This report compares Malaysian swimmers' current performance to USA Swimming reference data (top 500 per event/gender/age). 
Z-scores indicate how Malaysian swimmers perform relative to the USA mean: positive z-scores indicate faster times (better performance), 
negative z-scores indicate slower times.</p>

<div class="stat-grid">
    <div class="stat-card">
        <div class="stat-value">{overall_stats['total_results']}</div>
        <div class="stat-label">Total Results Analyzed</div>
    </div>
    <div class="stat-card">
        <div class="stat-value">{overall_stats['unique_swimmers']}</div>
        <div class="stat-label">Unique Swimmers</div>
    </div>
    <div class="stat-card">
        <div class="stat-value">{overall_stats['avg_z_score']:.3f}</div>
        <div class="stat-label">Average Z-Score</div>
    </div>
    <div class="stat-card">
        <div class="stat-value">{overall_stats['median_z_score']:.3f}</div>
        <div class="stat-label">Median Z-Score</div>
    </div>
    <div class="stat-card">
        <div class="stat-value">{overall_stats['min_z_score']:.3f}</div>
        <div class="stat-label">Minimum Z-Score</div>
    </div>
    <div class="stat-card">
        <div class="stat-value">{overall_stats['max_z_score']:.3f}</div>
        <div class="stat-label">Maximum Z-Score</div>
    </div>
</div>
</div>

<h2>1. Z-Score Range Distribution</h2>
<p>Where do Malaysian swimmers fall on the USA performance curve?</p>
<table>
<thead>
<tr><th>Z-Score Range</th><th>Count</th><th>Percentage</th><th>Interpretation</th></tr>
</thead>
<tbody>
"""
    
    for r in range_data:
        interpretation = ""
        if "Top 2.5%" in r['range'] or "Top 6.7%" in r['range'] or "Top 15.9%" in r['range']:
            interpretation = "Elite level - On track for international competition"
        elif "Above Average" in r['range']:
            interpretation = "Above USA average - Strong performance"
        elif "Average" in r['range']:
            interpretation = "Near USA average - Competitive"
        elif "Below Average" in r['range']:
            interpretation = "Below USA average - Development needed"
        else:
            interpretation = "Significantly below USA average - Substantial improvement needed"
        
        z_class = "positive" if r['avg_z'] > 0 else "negative" if r['avg_z'] < -0.5 else ""
        
        html_content += f"""
<tr>
    <td><strong>{r['range']}</strong></td>
    <td>{r['count']}</td>
    <td>{r['pct']:.1f}%</td>
    <td>{interpretation}</td>
</tr>"""
    
    html_content += """
</tbody>
</table>

<h2>2. Performance by Event</h2>
<table>
<thead>
<tr><th>Gender</th><th>Event</th><th>Results</th><th>Swimmers</th><th>Avg Z</th><th>Median Z</th><th>Min Z</th><th>Max Z</th></tr>
</thead>
<tbody>
"""
    
    for row in sorted(event_rows, key=lambda x: (x['gender'], x['event'])):
        avg_class = "positive" if row['avg_z'] > 0 else "negative" if row['avg_z'] < -0.5 else ""
        
        html_content += f"""
<tr>
    <td><strong>{row['gender']}</strong></td>
    <td><strong>{row['event']}</strong></td>
    <td>{row['count']}</td>
    <td>{row['unique_swimmers']}</td>
    <td class="{avg_class}">{row['avg_z']:.3f}</td>
    <td>{row['median_z']:.3f}</td>
    <td>{row['min_z']:.3f}</td>
    <td>{row['max_z']:.3f}</td>
</tr>"""
    
    html_content += """
</tbody>
</table>

<h2>3. Performance by Age</h2>
<table>
<thead>
<tr><th>Gender</th><th>Age</th><th>Results</th><th>Avg Z</th><th>Median Z</th></tr>
</thead>
<tbody>
"""
    
    for row in sorted(age_rows, key=lambda x: (x['gender'], x['age'])):
        avg_class = "positive" if row['avg_z'] > 0 else "negative" if row['avg_z'] < -0.5 else ""
        
        html_content += f"""
<tr>
    <td><strong>{row['gender']}</strong></td>
    <td>{row['age']}</td>
    <td>{row['count']}</td>
    <td class="{avg_class}">{row['avg_z']:.3f}</td>
    <td>{row['median_z']:.3f}</td>
</tr>"""
    
    html_content += f"""
</tbody>
</table>

<h2>4. Key Insights</h2>
<div class="summary-box">
<h3>Interpreting the Results</h3>
<ul>
    <li><strong>Positive Z-Scores:</strong> Malaysian swimmers with positive z-scores are performing faster than the USA mean for that event/age/gender. These are strong performances relative to USA benchmarks.</li>
    <li><strong>Z-Score ≥ 1.5:</strong> Swimmers in the "Top 6.7%" or "Top 2.5%" ranges (z ≥ 1.5) are performing at elite levels and may be "on track" for international competition.</li>
    <li><strong>Negative Z-Scores:</strong> Swimmers with negative z-scores are slower than the USA mean. This is expected for developing swimmers but indicates areas for improvement.</li>
    <li><strong>Event Comparison:</strong> Compare average z-scores across events to identify which events Malaysian swimmers perform strongest in relative to USA benchmarks.</li>
    <li><strong>Age Patterns:</strong> Observe how average z-scores change by age to understand developmental trajectories.</li>
</ul>

<h3>Limitations</h3>
<ul>
    <li>This analysis uses <strong>current year data only</strong> - we cannot yet calculate improvement deltas (requires multi-year data)</li>
    <li>Age is calculated as <strong>age on first day of competition</strong> to match USA data methodology</li>
    <li>Z-scores are calculated against USA top 500, which represents elite competitive swimmers (top 7-12% of all competitive swimmers)</li>
    <li>Results may include multiple times per swimmer if they swam the same event in multiple meets</li>
</ul>
</div>

<hr style="margin:40px 0;border:none;border-top:2px solid #ddd">
<p style="color:#666;font-size:12px"><em>
Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br>
Data Source: Malaysian meet results from database, compared to USA Swimming top 500 reference data<br>
Phase: 1 of 3 - Malaysian Data Integration (Z-Score Analysis)
</em></p>

</body>
</html>"""
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)


if __name__ == '__main__':
    analyze_malaysian_zscores()














