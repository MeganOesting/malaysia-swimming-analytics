#!/usr/bin/env python3
"""
Generate Event-Specific MOT Delta Analysis Reports
Creates comprehensive reports for each event, similar to F_50_Free_MOT_Delta_Analysis.html
"""

import os
import pandas as pd
import sqlite3
from pathlib import Path

def get_conn():
    """Get SQLite database connection"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if 'statistical_analysis' in script_dir.lower():
        db_path = os.path.join(script_dir, '..', 'database', 'statistical.db')
    else:
        db_path = os.path.join('..', 'database', 'statistical.db')
    return sqlite3.connect(db_path)


def load_canada_data():
    """Load Canada On Track data from database"""
    conn = get_conn()
    query = """
        SELECT gender, event, age, track, time_text, time_seconds, aqua_points
        FROM canada_on_track
        ORDER BY gender, event, track, age
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def load_usa_deltas():
    """Load USA delta analysis from database"""
    conn = get_conn()
    query = """
        SELECT gender, event, age_from, age_to, sample_size,
               median_improvement, mean_improvement, std_improvement,
               q25_improvement, q75_improvement
        FROM usa_age_deltas
        ORDER BY gender, event, age_from, age_to
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def load_zscore_data():
    """Load z-score range analysis data"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if 'statistical_analysis' in script_dir.lower():
        csv_path = os.path.join(script_dir, '..', 'reports', 'Improvement_by_ZScore_Range.csv')
    else:
        csv_path = 'reports/Improvement_by_ZScore_Range.csv'
    
    if os.path.exists(csv_path):
        return pd.read_csv(csv_path)
    return None


def load_reappearance_data():
    """Load swimmer reappearance analysis data"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if 'statistical_analysis' in script_dir.lower():
        csv_path = os.path.join(script_dir, '..', 'reports', 'Swimmer_Reappearance_Analysis.csv')
    else:
        csv_path = 'reports/Swimmer_Reappearance_Analysis.csv'
    
    if os.path.exists(csv_path):
        return pd.read_csv(csv_path)
    return None


def load_zscore_patterns():
    """Load z-score pattern analysis (1.5-2.0 range patterns)"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if 'statistical_analysis' in script_dir.lower():
        csv_path = os.path.join(script_dir, '..', 'reports', 'ZScore_Pattern_Analysis.csv')
    else:
        csv_path = 'reports/ZScore_Pattern_Analysis.csv'
    
    if os.path.exists(csv_path):
        return pd.read_csv(csv_path)
    return None


def compute_canada_deltas(canada_df, gender, event):
    """Compute Canada track deltas for a specific event"""
    event_data = canada_df[(canada_df['gender'] == gender) & (canada_df['event'] == event)].copy()
    
    tracks = {}
    for track in sorted(event_data['track'].unique()):
        track_data = event_data[event_data['track'] == track].sort_values('age')
        track_dict = {}
        for _, row in track_data.iterrows():
            track_dict[int(row['age'])] = {
                'time_text': row['time_text'],
                'time_seconds': row['time_seconds']
            }
        
        # Compute deltas
        deltas = {}
        ages = sorted(track_dict.keys())
        for i in range(len(ages) - 1):
            age_from = ages[i]
            age_to = ages[i+1]
            delta = track_dict[age_from]['time_seconds'] - track_dict[age_to]['time_seconds']
            delta = max(0, delta)  # Clamp negative
            deltas[f"{age_from}->{age_to}"] = delta
        
        tracks[track] = {'times': track_dict, 'deltas': deltas}
    
    return tracks


def format_time(seconds):
    """Format time in seconds to display format"""
    if seconds < 60:
        return f"{seconds:.2f}"
    else:
        mins = int(seconds // 60)
        secs = seconds % 60
        return f"{mins}:{secs:.2f}"


def get_zscore_data_for_transitions(zscore_df, gender, event, transitions):
    """Get z-score data for specific transitions"""
    if zscore_df is None:
        return {}
    
    result = {}
    for age_from, age_to in transitions:
        trans_data = zscore_df[
            (zscore_df['gender'] == gender) &
            (zscore_df['event'] == event) &
            (zscore_df['age_from'] == age_from) &
            (zscore_df['age_to'] == age_to)
        ].copy()
        
        # Sort by z-score (highest first)
        trans_data = trans_data.sort_values('mean_zscore', ascending=False)
        result[f"{age_from}->{age_to}"] = trans_data
    
    return result


def generate_event_report(gender, event, canada_df, usa_df, zscore_df, reappearance_df=None, zscore_patterns_df=None):
    """Generate comprehensive report for one event"""
    
    # Get Canada data
    canada_tracks = compute_canada_deltas(canada_df, gender, event)
    
    # Get USA data
    usa_event = usa_df[(usa_df['gender'] == gender) & (usa_df['event'] == event)].copy()
    
    # Determine which transitions exist
    transitions = []
    for _, row in usa_event.iterrows():
        transitions.append((int(row['age_from']), int(row['age_to'])))
    
    if not transitions:
        print(f"⚠️  No USA data for {gender} {event}")
        return None
    
    # Get z-score data
    zscore_data = get_zscore_data_for_transitions(zscore_df, gender, event, transitions)
    
    # Determine Canada track start ages
    track_start_ages = {}
    for track, data in canada_tracks.items():
        ages = sorted(data['times'].keys())
        if ages:
            track_start_ages[track] = min(ages)
    
    # Generate HTML
    html_parts = []
    html_parts.append("<!DOCTYPE html>")
    html_parts.append("<html lang='en'>")
    html_parts.append("<head>")
    html_parts.append("<meta charset='utf-8'>")
    html_parts.append(f"<title>{gender} {event} MOT Delta Analysis</title>")
    html_parts.append("""
    <style>
    body{font-family:system-ui,Segoe UI,Arial,sans-serif;margin:24px;max-width:1200px;color:#000;background:white}
    h1{color:#CE1126;border-bottom:3px solid #CE1126;padding-bottom:8px}
    h2{color:#000;margin-top:32px;border-bottom:2px solid #00247D;padding-bottom:6px}
    h3{color:#000;margin-top:24px}
    table{border-collapse:collapse;width:100%;margin:16px 0}
    th,td{border:1px solid #ccc;padding:10px;font-size:14px;text-align:left;color:#000}
    th{background:#CE1126;color:#fff;font-weight:600}
    tr:nth-child(even){background:#fafafa}
    .highlight{background:#fff9e6}
    .summary-box{background:#fff;border-left:4px solid #CE1126;padding:16px;margin:20px 0}
    .comparison-table{width:auto;margin:16px 0}
    .comparison-table th{background:#CE1126;color:#fff}
    .delta-positive{color:#008000;font-weight:600}
    .delta-negative{color:#cc0000;font-weight:600}
    .zscore-box{background:#fff9e6;border-left:4px solid #ffc107;padding:16px;margin:20px 0}
    a{color:#CE1126;text-decoration:none}
    a:hover{color:#000;text-decoration:underline}
    </style>
    </head>
    <body>
    """)
    
    html_parts.append(f"<h1>{gender} {event}: MOT Delta Determination Analysis</h1>")
    html_parts.append(f"<p><strong>Purpose:</strong> Analyze Canada On Track reference deltas and USA swimming improvement statistics to determine appropriate Malaysia On Track (MOT) deltas for {gender} {event} transitions.</p>")
    
    # Quick summary
    html_parts.append("<div class='summary-box'>")
    html_parts.append("<h3 style='margin-top:0'>Quick Summary</h3>")
    html_parts.append("<ul>")
    for age_from, age_to in transitions:
        usa_row = usa_event[
            (usa_event['age_from'] == age_from) & 
            (usa_event['age_to'] == age_to)
        ]
        if len(usa_row) > 0:
            median = usa_row.iloc[0]['median_improvement']
            n = usa_row.iloc[0]['sample_size']
            html_parts.append(f"<li><strong>{age_from}→{age_to} Transition:</strong> USA median = {median:.3f}s (n={n:.0f})</li>")
    html_parts.append("</ul>")
    html_parts.append("</div>")
    
    # Canada On Track Data
    html_parts.append("<h2>1. Canada On Track Reference Data</h2>")
    
    track_labels = {1: "Track 1 (Early Developers)", 2: "Track 2 (Middle Developers)", 3: "Track 3 (Late Developers)"}
    
    for track in sorted(canada_tracks.keys()):
        track_data = canada_tracks[track]
        ages = sorted(track_data['times'].keys())
        
        if not ages:
            continue
        
        html_parts.append(f"<h3>{track_labels.get(track, f'Track {track}')}")
        if track in track_start_ages:
            html_parts.append(f" - Entry Age {track_start_ages[track]}")
        html_parts.append("</h3>")
        
        html_parts.append("<table>")
        html_parts.append("<thead><tr><th>Age</th><th>Time (text)</th><th>Time (seconds)</th><th>Delta from Previous</th></tr></thead><tbody>")
        
        prev_age = None
        for age in ages:
            time_info = track_data['times'][age]
            delta_cell = "—"
            
            if prev_age is not None:
                trans_key = f"{prev_age}->{age}"
                if trans_key in track_data['deltas']:
                    delta = track_data['deltas'][trans_key]
                    if delta > 0:
                        delta_cell = f"<span class='delta-positive'>{delta:.3f}s ({prev_age}→{age})</span>"
                    else:
                        delta_cell = f"{delta:.3f}s ({prev_age}→{age})"
            
            html_parts.append(f"<tr><td>{age}</td><td>{time_info['time_text']}</td><td>{time_info['time_seconds']:.2f}</td><td>{delta_cell}</td></tr>")
            prev_age = age
        
        html_parts.append("</tbody></table>")
    
    # Canada Delta Summary
    html_parts.append("<h3>Canada Delta Summary</h3>")
    html_parts.append("<table class='comparison-table'>")
    html_parts.append("<thead><tr><th>Transition</th>")
    for track in sorted(canada_tracks.keys()):
        html_parts.append(f"<th>{track_labels.get(track, f'Track {track}')}</th>")
    html_parts.append("</tr></thead><tbody>")
    
    all_transitions = set()
    for track_data in canada_tracks.values():
        all_transitions.update(track_data['deltas'].keys())
    
    for trans in sorted(all_transitions):
        html_parts.append(f"<tr><td><strong>{trans}</strong></td>")
        for track in sorted(canada_tracks.keys()):
            delta = canada_tracks[track]['deltas'].get(trans, None)
            if delta is not None and delta > 0:
                html_parts.append(f"<td class='delta-positive'>{delta:.3f}s</td>")
            elif delta == 0:
                html_parts.append(f"<td>0.000s</td>")
            else:
                html_parts.append(f"<td>—</td>")
        html_parts.append("</tr>")
    
    html_parts.append("</tbody></table>")
    
    # USA Statistics
    html_parts.append("<h2>2. USA Swimming Improvement Statistics</h2>")
    html_parts.append("<table>")
    html_parts.append("<thead><tr><th>Transition</th><th>Sample Size</th><th>Median Δ</th><th>Mean Δ</th><th>Std Dev</th><th>Q25</th><th>Q75</th></tr></thead><tbody>")
    
    for age_from, age_to in transitions:
        usa_row = usa_event[
            (usa_event['age_from'] == age_from) & 
            (usa_event['age_to'] == age_to)
        ]
        if len(usa_row) > 0:
            row = usa_row.iloc[0]
            median = row['median_improvement']
            median_class = 'delta-positive' if median > 0 else 'delta-negative'
            html_parts.append(f"<tr>")
            html_parts.append(f"<td><strong>{age_from}→{age_to}</strong></td>")
            html_parts.append(f"<td>{row['sample_size']:.0f} athletes</td>")
            html_parts.append(f"<td class='{median_class}'>{median:.3f}s</td>")
            html_parts.append(f"<td>{row['mean_improvement']:.3f}s</td>")
            html_parts.append(f"<td>{row['std_improvement']:.3f}s</td>")
            html_parts.append(f"<td>{row['q25_improvement']:.3f}s</td>")
            html_parts.append(f"<td>{row['q75_improvement']:.3f}s</td>")
            html_parts.append(f"</tr>")
    
    html_parts.append("</tbody></table>")
    
    # Z-Score Analysis by Transition
    if zscore_df is not None:
        html_parts.append("<h2>3. Improvement Analysis by Performance Level (Z-Score)</h2>")
        
        for age_from, age_to in transitions:
            trans_key = f"{age_from}->{age_to}"
            if trans_key in zscore_data and len(zscore_data[trans_key]) > 0:
                zdf = zscore_data[trans_key].sort_values('mean_zscore', ascending=False)
                
                html_parts.append(f"<h3>{age_from}→{age_to} Transition: Improvement by Performance Level</h3>")
                html_parts.append("<table>")
                html_parts.append("<thead><tr><th>Performance Level (Z-Score Range)</th><th>Number of Athletes</th><th>Median Improvement</th><th>% Improving</th><th>% Getting Slower</th></tr></thead><tbody>")
                
                # Highlight 1.5-2.0 range if it's the only positive one
                all_positive = zdf[zdf['median_improvement'] > 0]
                highlight_range = "Top 6.7% (1.5 ≤ z < 2.0)"
                should_highlight = (
                    len(all_positive) > 0 and 
                    highlight_range in zdf['zscore_range'].values and
                    zdf[zdf['zscore_range'] == highlight_range]['median_improvement'].values[0] > 0
                )
                
                for _, zrow in zdf.iterrows():
                    range_name = zrow['zscore_range']
                    median_imp = zrow['median_improvement']
                    is_highlight = should_highlight and range_name == highlight_range
                    row_class = 'class="highlight"' if is_highlight else ''
                    
                    median_class = 'delta-positive' if median_imp > 0 else 'delta-negative'
                    
                    html_parts.append(f"<tr {row_class}>")
                    html_parts.append(f"<td>{range_name}</td>")
                    html_parts.append(f"<td>{int(zrow['n_athletes'])}</td>")
                    html_parts.append(f"<td class='{median_class}'>{median_imp:.3f}s</td>")
                    html_parts.append(f"<td>{zrow['pct_improving']:.1f}%</td>")
                    html_parts.append(f"<td>{zrow['pct_getting_slower']:.1f}%</td>")
                    html_parts.append("</tr>")
                
                html_parts.append("</tbody></table>")
                
                # Add note if 1.5-2.0 is noteworthy
                zscore_1520 = zdf[zdf['zscore_range'] == highlight_range]
                if len(zscore_1520) > 0:
                    z1520 = zscore_1520.iloc[0]
                    positive_ranges = zdf[zdf['median_improvement'] > 0]
                    if z1520['median_improvement'] > 0 and len(positive_ranges) == 1:
                        html_parts.append(f"""
                        <div class='zscore-box'>
                        <h4 style='margin-top:0'>Key Finding for {age_from}→{age_to}</h4>
                        <p><strong>The 1.5-2.0 z-score range (top 6.7%) is the ONLY performance level showing positive improvement!</strong></p>
                        <ul>
                        <li>All other performance levels show negative medians (swimmers getting slower on average)</li>
                        <li>{z1520['pct_improving']:.1f}% of swimmers in this elite range improved</li>
                        <li>This validates targeting elite performers for "on track" identification</li>
                        </ul>
                        </div>
                        """)
    
    # Swimmer Reappearance Analysis
    if reappearance_df is not None:
        reappear_event = reappearance_df[
            (reappearance_df['gender'] == gender) & 
            (reappearance_df['event'] == event)
        ]
        
        if len(reappear_event) > 0:
            html_parts.append("<h2>4. Swimmer Reappearance Analysis</h2>")
            html_parts.append("<div class='summary-box'>")
            html_parts.append("<p><strong>Understanding attrition and recovery patterns in elite swimming</strong></p>")
            
            row = reappear_event.iloc[0]
            
            html_parts.append("<h3>Dropout and Reappearance Statistics</h3>")
            html_parts.append("<table>")
            html_parts.append("<thead><tr><th>Metric</th><th>Value</th></tr></thead><tbody>")
            
            # 15→16 dropout and reappearance
            dropped_15_16 = int(row['dropped_15_to_16']) if pd.notna(row['dropped_15_to_16']) else 0
            reappeared_17_or_18 = int(row['reappeared_at_17_or_18_after_dropout']) if pd.notna(row['reappeared_at_17_or_18_after_dropout']) else 0
            pct_reappeared_15_16 = float(row['pct_reappeared_17_or_18']) if pd.notna(row['pct_reappeared_17_or_18']) else 0
            
            html_parts.append(f"<tr><td><strong>Swimmers who dropped out 15→16</strong></td><td>{dropped_15_16}</td></tr>")
            html_parts.append(f"<tr><td>Reappeared at age 17 or 18</td><td>{reappeared_17_or_18} ({pct_reappeared_15_16:.1f}%)</td></tr>")
            
            # 16→17 dropout and reappearance
            dropped_16_17 = int(row['dropped_16_to_17']) if pd.notna(row['dropped_16_to_17']) else 0
            reappeared_18 = int(row['reappeared_at_18_after_dropout_16_17']) if pd.notna(row['reappeared_at_18_after_dropout_16_17']) else 0
            pct_reappeared_16_17 = float(row['pct_reappeared_18_after_dropout_16_17']) if pd.notna(row['pct_reappeared_18_after_dropout_16_17']) else 0
            
            html_parts.append(f"<tr><td><strong>Swimmers who dropped out 16→17</strong></td><td>{dropped_16_17}</td></tr>")
            html_parts.append(f"<tr><td>Reappeared at age 18</td><td>{reappeared_18} ({pct_reappeared_16_17:.1f}%)</td></tr>")
            
            html_parts.append("</tbody></table>")
            
            html_parts.append("<h3>Interpretation</h3>")
            html_parts.append("<ul>")
            html_parts.append(f"<li><strong>{pct_reappeared_15_16:.1f}% of 15→16 dropouts reappear</strong>: Nearly one-third of swimmers who fall out of the top 500 at age 16 regain elite status by age 17 or 18.</li>")
            html_parts.append(f"<li><strong>{pct_reappeared_16_17:.1f}% of 16→17 dropouts reappear</strong>: About one-fifth of swimmers who drop out at 17 return by 18.</li>")
            html_parts.append("<li><strong>Implications:</strong> Temporary setbacks (injury, training changes, motivation) are common, but most dropouts (~70%) do not return to top-500 status.</li>")
            html_parts.append("<li><strong>MOT Consideration:</strong> Delta calculations may reflect 'survivor bias' - swimmers who maintain top-500 status consistently show different improvement patterns than those who drop out.</li>")
            html_parts.append("</ul>")
            
            html_parts.append("</div>")
    
    # Z-Score Pattern Analysis (1.5-2.0 plateau)
    if zscore_patterns_df is not None:
        pattern_event = zscore_patterns_df[
            (zscore_patterns_df['gender'] == gender) & 
            (zscore_patterns_df['event'] == event) &
            (zscore_patterns_df['median_improvement'] <= 0.02)  # Negative or near-zero
        ]
        
        if len(pattern_event) > 0:
            html_parts.append("<h2>5. Z-Score Pattern Analysis: The 1.5-2.0 Plateau</h2>")
            html_parts.append("<div class='zscore-box'>")
            html_parts.append("<p><strong>Identifying unique challenges for high-performing swimmers (93rd-98th percentile)</strong></p>")
            
            html_parts.append("<table>")
            html_parts.append("<thead><tr><th>Transition</th><th>1.5-2.0 Z Median</th><th>Other Ranges Avg</th><th>Difference</th><th>% Improving</th></tr></thead><tbody>")
            
            for _, pattern_row in pattern_event.iterrows():
                age_from = int(pattern_row['age_from'])
                age_to = int(pattern_row['age_to'])
                median_imp = float(pattern_row['median_improvement'])
                avg_other = float(pattern_row['avg_other_ranges_median'])
                diff = float(pattern_row['difference_from_avg'])
                pct_improving = float(pattern_row['pct_improving'])
                
                median_class = 'delta-positive' if median_imp > 0 else 'delta-negative'
                
                html_parts.append(f"<tr>")
                html_parts.append(f"<td><strong>{age_from}→{age_to}</strong></td>")
                html_parts.append(f"<td class='{median_class}'>{median_imp:.3f}s</td>")
                html_parts.append(f"<td>{avg_other:.3f}s</td>")
                html_parts.append(f"<td class='delta-negative'>{diff:.3f}s</td>")
                html_parts.append(f"<td>{pct_improving:.1f}%</td>")
                html_parts.append("</tr>")
            
            html_parts.append("</tbody></table>")
            
            html_parts.append("<h3>What This Means</h3>")
            html_parts.append("<ul>")
            html_parts.append("<li><strong>The 'Good But Not Great' Dilemma:</strong> Swimmers in the 1.5-2.0 z-score range (top 6.7%) face unique challenges - they're faster than most, but may be hitting their genetic/training ceiling.</li>")
            html_parts.append("<li><strong>Diminishing Returns:</strong> These swimmers may have already extracted most available improvement from training. Further gains require exceptional dedication or genetic advantages.</li>")
            html_parts.append("<li><strong>MOT Implication:</strong> Consider tiered MOT standards - swimmers in this range may need more modest improvement targets than those at lower performance levels.</li>")
            html_parts.append("</ul>")
            
            html_parts.append("</div>")
    
    # USA vs Canada Comparison
    html_parts.append("<h2>6. Comparison: USA vs Canada</h2>")
    html_parts.append("<table class='comparison-table'>")
    html_parts.append("<thead><tr><th>Transition</th><th>USA Median</th>")
    for track in sorted(canada_tracks.keys()):
        html_parts.append(f"<th>Canada {track_labels.get(track, f'Track {track}')}</th>")
    html_parts.append("</tr></thead><tbody>")
    
    for age_from, age_to in transitions:
        trans_key = f"{age_from}->{age_to}"
        usa_row = usa_event[
            (usa_event['age_from'] == age_from) & 
            (usa_event['age_to'] == age_to)
        ]
        
        if len(usa_row) > 0:
            usa_median = usa_row.iloc[0]['median_improvement']
            usa_class = 'delta-positive' if usa_median > 0 else 'delta-negative'
            
            html_parts.append(f"<tr>")
            html_parts.append(f"<td><strong>{age_from}→{age_to}</strong></td>")
            html_parts.append(f"<td class='{usa_class}'>{usa_median:.3f}s</td>")
            
            for track in sorted(canada_tracks.keys()):
                canada_delta = canada_tracks[track]['deltas'].get(trans_key, None)
                if canada_delta is not None:
                    diff = usa_median - canada_delta
                    diff_class = 'delta-negative' if diff < 0 else ''
                    html_parts.append(f"<td>{canada_delta:.3f}s <span class='{diff_class}'>(diff: {diff:+.3f}s)</span></td>")
                else:
                    html_parts.append("<td>—</td>")
            
            html_parts.append("</tr>")
    
    html_parts.append("</tbody></table>")
    
    # Analysis & Recommendations
    html_parts.append("<h2>7. Analysis & Recommendations for MOT Deltas</h2>")
    
    for age_from, age_to in transitions:
        html_parts.append(f"<h3>{age_from}→{age_to} Transition</h3>")
        html_parts.append("<div class='summary-box'>")
        
        usa_row = usa_event[
            (usa_event['age_from'] == age_from) & 
            (usa_event['age_to'] == age_to)
        ]
        
        if len(usa_row) > 0:
            usa_median = usa_row.iloc[0]['median_improvement']
            usa_n = usa_row.iloc[0]['sample_size']
            
            html_parts.append(f"<ul>")
            html_parts.append(f"<li><strong>USA Median:</strong> {usa_median:.3f}s improvement ({usa_n:.0f} athletes)</li>")
            
            canada_deltas_list = []
            for track in sorted(canada_tracks.keys()):
                trans_key = f"{age_from}->{age_to}"
                canada_delta = canada_tracks[track]['deltas'].get(trans_key, None)
                if canada_delta is not None:
                    canada_deltas_list.append((track, canada_delta))
                    html_parts.append(f"<li><strong>Canada {track_labels.get(track, f'Track {track}')}:</strong> {canada_delta:.3f}s improvement</li>")
            
            if canada_deltas_list:
                avg_canada = sum(d for _, d in canada_deltas_list) / len(canada_deltas_list)
                diff = usa_median - avg_canada
                html_parts.append(f"<li><strong>Difference:</strong> USA median is {diff:+.3f}s compared to Canada average</li>")
            
            html_parts.append("</ul>")
            
        html_parts.append("</div>")
    
    # Section 8: Event-Specific Insights & MOT Recommendations
    html_parts.append("<h2>8. Event-Specific Insights & MOT Recommendations</h2>")
    html_parts.append("<div class='summary-box'>")
    
    # Get event-specific statistics
    event_negatives = 0
    if zscore_patterns_df is not None:
        event_patterns = zscore_patterns_df[
            (zscore_patterns_df['gender'] == gender) & 
            (zscore_patterns_df['event'] == event)
        ]
        event_negatives = len(event_patterns[event_patterns['median_improvement'] <= 0.02])
    
    # Calculate how this event compares to overall patterns
    html_parts.append("<h3>How This Event Compares to Overall Patterns</h3>")
    html_parts.append("<ul>")
    
    if event_negatives > 0:
        html_parts.append(f"<li><strong>Negative Improvements:</strong> This event shows {event_negatives} negative/zero improvements across z-score ranges, representing {event_negatives/172*100:.1f}% of all negative improvements in the dataset.</li>")
    
    # Gender context
    if gender == 'F':
        html_parts.append(f"<li><strong>Gender Pattern:</strong> As a female event, this contributes to the overall pattern where 72.1% of negative improvements occur in female events (vs 27.9% in male events).</li>")
    else:
        html_parts.append(f"<li><strong>Gender Pattern:</strong> As a male event, this contributes to the overall pattern where male events show fewer but sometimes more severe negative improvements (average -0.944s vs female -0.803s).</li>")
    
    # Transition-specific insights
    transitions_with_issues = []
    for age_from, age_to in transitions:
        usa_row = usa_event[
            (usa_event['age_from'] == age_from) & 
            (usa_event['age_to'] == age_to)
        ]
        if len(usa_row) > 0:
            usa_median = usa_row.iloc[0]['median_improvement']
            if usa_median <= 0.02:
                transitions_with_issues.append(f"{age_from}→{age_to}")
    
    if transitions_with_issues:
        html_parts.append(f"<li><strong>Problematic Transitions:</strong> This event shows negative median improvements at: {', '.join(transitions_with_issues)}. This aligns with the universal pattern where 75.6% of all negative improvements occur at 17→18.</li>")
    
    html_parts.append("</ul>")
    
    # Direct MOT Recommendations
    html_parts.append("<h3>Direct MOT Delta Recommendations</h3>")
    html_parts.append("<table class='recommendation-table'>")
    html_parts.append("<thead><tr><th>Transition</th><th>Recommended Delta</th><th>Confidence</th><th>Rationale</th></tr></thead><tbody>")
    
    for age_from, age_to in transitions:
        usa_row = usa_event[
            (usa_event['age_from'] == age_from) & 
            (usa_event['age_to'] == age_to)
        ]
        
        if len(usa_row) > 0:
            usa_median = usa_row.iloc[0]['median_improvement']
            usa_n = usa_row.iloc[0]['sample_size']
            
            # Determine recommended delta
            if usa_median <= 0:
                recommended_delta = max(0, usa_median * 0.5)  # Conservative for negative
                confidence = "Low - Regression observed"
                rationale = f"Negative median ({usa_median:.3f}s) indicates regression. Recommend conservative expectation of {recommended_delta:.3f}s or maintenance."
            elif usa_median <= 0.1:
                recommended_delta = usa_median * 0.7  # Slightly conservative for very small improvements
                confidence = "Medium - Minimal improvement"
                rationale = f"Minimal improvement observed ({usa_median:.3f}s). Recommend conservative delta of {recommended_delta:.3f}s."
            elif age_to == 18:
                recommended_delta = usa_median * 0.8  # Conservative for 17→18
                confidence = "Medium - 17→18 transition"
                rationale = f"17→18 transition shows {usa_median:.3f}s improvement, but 75.6% of all negative improvements occur at this transition. Recommend conservative delta of {recommended_delta:.3f}s."
            else:
                recommended_delta = usa_median  # Use median for earlier transitions
                confidence = "High - Stable transition"
                rationale = f"Healthy improvement pattern ({usa_median:.3f}s, n={usa_n:.0f}). Recommend delta of {recommended_delta:.3f}s."
            
            # Check Canada comparison
            canada_deltas_list = []
            for track in sorted(canada_tracks.keys()):
                trans_key = f"{age_from}->{age_to}"
                canada_delta = canada_tracks[track]['deltas'].get(trans_key, None)
                if canada_delta is not None:
                    canada_deltas_list.append(canada_delta)
            
            if canada_deltas_list:
                avg_canada = sum(canada_deltas_list) / len(canada_deltas_list)
                if abs(usa_median - avg_canada) > 0.5:
                    rationale += f" Note: USA median ({usa_median:.3f}s) differs significantly from Canada average ({avg_canada:.3f}s)."
            
            html_parts.append(f"<tr>")
            html_parts.append(f"<td><strong>{age_from}→{age_to}</strong></td>")
            html_parts.append(f"<td>{recommended_delta:.3f}s</td>")
            html_parts.append(f"<td>{confidence}</td>")
            html_parts.append(f"<td>{rationale}</td>")
            html_parts.append("</tr>")
    
    html_parts.append("</tbody></table>")
    
    # Event-specific considerations
    html_parts.append("<h3>Event-Specific Considerations</h3>")
    html_parts.append("<ul>")
    
    # Distance-based insights
    if '1500' in event or '800' in event:
        html_parts.append("<li><strong>Distance Event:</strong> Distance events show large absolute improvements in raw seconds (e.g., 4-18 seconds per transition) but can show more extreme negative patterns in specific z-score ranges, especially 1.5-2.0. While world-class distance swimmers often peak at younger ages, our 15-18 data shows that distance events generally maintain positive median deltas even at 17→18, though improvement rates decline. However, when distance events do show negative improvements, the regression can be severe (multiple seconds), requiring attention to training volume and recovery at older ages.</li>")
    elif '50' in event or '100' in event:
        html_parts.append("<li><strong>Sprint Event:</strong> Sprint events show more frequent negative median deltas at the 17→18 transition than distance events (e.g., F 50 Free: -0.11s, F 100 Free: -0.15s at 17→18). This suggests sprint performance is less maintainable in the 15-18 age range, with swimmers often experiencing slight regression in the development phase even while world-class sprinters peak at older ages in their careers.</li>")
    
    # Stroke-based insights
    if 'IM' in event:
        html_parts.append("<li><strong>Individual Medley:</strong> Technical events like IM may show different improvement patterns due to the multi-stroke nature. Form refinements can lead to significant time drops even at older ages.</li>")
    elif 'Fly' in event or 'Back' in event or 'Breast' in event:
        html_parts.append("<li><strong>Stroke Event:</strong> Technical stroke events may show different progression patterns than freestyle due to form refinement opportunities. Consider technical improvements separate from physical development.</li>")
    
    html_parts.append("</ul>")
    
    html_parts.append("</div>")
    
    # Footer
    html_parts.append("<hr style='margin:40px 0;border:none;border-top:2px solid #ddd'>")
    html_parts.append("""
    <p style='color:#666;font-size:12px'><em>
    Generated from statistical analysis database.<br>
    Data sources: Canada On Track reference times from April 2025, and USA Swimming season rankings 
    (top 500 per age/event/gender) from 2021-2022, 2022-2023, 2023-2024, and 2024-2025 seasons.<br>
    USA Swimming ages are the age of the swimmer on the first day of competition, not their birth year age.
    </em></p>
    """)
    
    html_parts.append("</body></html>")
    
    return '\n'.join(html_parts)


def main():
    """Generate reports for all events"""
    
    print("Loading data from database...")
    canada_df = load_canada_data()
    usa_df = load_usa_deltas()
    zscore_df = load_zscore_data()
    reappearance_df = load_reappearance_data()
    zscore_patterns_df = load_zscore_patterns()
    
    # Get all unique gender/event combinations
    events = usa_df[['gender', 'event']].drop_duplicates()
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if 'statistical_analysis' in script_dir.lower():
        reports_dir = os.path.join(script_dir, '..', 'reports')
    else:
        reports_dir = 'reports'
    
    os.makedirs(reports_dir, exist_ok=True)
    
    generated = 0
    for _, row in events.iterrows():
        gender = row['gender']
        event = row['event']
        
        print(f"Generating report for {gender} {event}...")
        
        html_content = generate_event_report(gender, event, canada_df, usa_df, zscore_df, reappearance_df, zscore_patterns_df)
        
        if html_content:
            # Clean event name for filename
            safe_event = event.replace(' ', '_')
            filename = f"{gender}_{safe_event}_MOT_Delta_Analysis.html"
            filepath = os.path.join(reports_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            print(f"  ✅ Saved: {filename}")
            generated += 1
        else:
            print(f"  ⚠️  Skipped: No data available")
    
    print(f"\n✅ Generated {generated} event-specific reports in {reports_dir}/")


if __name__ == '__main__':
    main()

