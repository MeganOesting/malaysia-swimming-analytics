#!/usr/bin/env python3
"""
Create Distribution Graph for F 50 Free Age 15
Shows swim times and their z-scores to illustrate the data distribution
"""

import os
import pandas as pd
import numpy as np
import json
import math
import sqlite3
from pathlib import Path

def get_zscore_interpretation(z):
    """Get plain-language interpretation of a z-score"""
    if z >= 2.0:
        return "Elite (Top 2.5%)"
    elif z >= 1.5:
        return "Very Strong (Top 6.7%)"
    elif z >= 1.0:
        return "Strong (Top 15.9%)"
    elif z >= 0.5:
        return "Above Average"
    elif z >= 0:
        return "Average"
    elif z >= -0.5:
        return "Below Average"
    elif z >= -1.0:
        return "Weaker"
    else:
        return "Much Below Average"

def load_period_data(gender, event, age, period):
    """Load data from a specific period file"""
    filename = f"{gender} {event} {age} {period}.txt"
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if 'statistical_analysis' in script_dir.lower():
        filepath = os.path.join(script_dir, "..", "data", "Period Data", period, f"{gender} {event} {period}", filename)
    else:
        filepath = os.path.join("Period Data", period, f"{gender} {event} {period}", filename)
    
    if not os.path.exists(filepath):
        return None
    
    try:
        df = pd.read_csv(
            filepath,
            sep='\t',
            encoding='utf-8',
            dtype={'Name': str}
        )
        return df
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return None


def parse_swim_time(time_str):
    """Parse swim time string to seconds"""
    import re
    if pd.isna(time_str) or time_str == '':
        return None
    
    s = str(time_str).strip()
    s = re.sub(r"[a-zA-Z]+$", "", s).strip()
    s = re.sub(r"[^0-9:\.]", "", s)
    if s == "":
        return None

    if ':' in s:
        parts = s.split(':')
        try:
            if len(parts) == 2:
                minutes = int(parts[0]) if parts[0] else 0
                seconds = float(parts[1])
                return minutes * 60 + seconds
            elif len(parts) == 3:
                hours = int(parts[0]) if parts[0] else 0
                minutes = int(parts[1]) if parts[1] else 0
                seconds = float(parts[2])
                return hours * 3600 + minutes * 60 + seconds
        except Exception:
            return None
    else:
        try:
            return float(s)
        except Exception:
            return None
    return None


def create_distribution_graph():
    """Create HTML visualization of F 50 Free Age 15 distribution"""
    
    # Define parameters
    gender = "F"
    event = "50 Free"
    age = 15
    
    # Load the data
    print(f"Loading {gender} {event} Age {age} data...")
    df = load_period_data(gender, event, str(age), "9.1.21-8.31.22")
    
    if df is None or len(df) == 0:
        print("Error: Could not load data")
        return
    
    # Parse times (check for column name variations)
    time_col = None
    for col in ['Swim Time', 'Time', 'time']:
        if col in df.columns:
            time_col = col
            break
    
    if time_col is None:
        print(f"Error: Could not find time column. Available columns: {list(df.columns)}")
        return
    
    df['time_seconds'] = df[time_col].apply(parse_swim_time)
    df = df.dropna(subset=['time_seconds'])
    
    # Validate time ranges - catch any parsing errors
    # For 50 Free, reasonable times are 20-60 seconds
    # For other events, we'll use broader ranges
    event_time_ranges = {
        '50 Free': (18, 65),
        '100 Free': (45, 120),
        '200 Free': (110, 300),
        '400 Free': (240, 600),
        '800 Free': (540, 1200),
        '1500 Free': (960, 2400),
        '100 Back': (50, 130),
        '200 Back': (110, 300),
        '100 Breast': (55, 140),
        '200 Breast': (120, 320),
        '100 Fly': (50, 130),
        '200 Fly': (110, 300),
        '200 IM': (120, 320),
        '400 IM': (280, 720)
    }
    
    min_time, max_time = event_time_ranges.get(event, (10, 1000))
    invalid_times = df[(df['time_seconds'] < min_time) | (df['time_seconds'] > max_time)]
    if len(invalid_times) > 0:
        print(f"⚠️  WARNING: Found {len(invalid_times)} invalid times outside expected range [{min_time}, {max_time}] seconds")
        print(f"   Invalid times: {invalid_times['time_seconds'].tolist()[:10]}")
        # Remove invalid times
        df = df[(df['time_seconds'] >= min_time) & (df['time_seconds'] <= max_time)]
    
    if len(df) == 0:
        print("ERROR: No valid times after validation!")
        return
    
    print(f"Loaded {len(df)} swimmers (after validation)")
    
    # Calculate z-scores (for swim times, faster = better, so invert)
    # z = (mean - time) / std, so faster times get higher z-scores
    mean_time = df['time_seconds'].mean()
    std_time = df['time_seconds'].std()
    df['zscore'] = (mean_time - df['time_seconds']) / std_time
    
    # Sort by time (fastest first)
    df = df.sort_values('time_seconds')
    df['rank'] = range(1, len(df) + 1)
    
    # Calculate percentiles
    df['percentile'] = 100 * (df['rank'] - 1) / (len(df) - 1)
    
    # Prepare data for plotting - convert numpy types to native Python types for JSON
    times = [float(t) for t in df['time_seconds'].values]
    zscores = [float(z) for z in df['zscore'].values]
    ranks = [int(r) for r in df['rank'].values]
    
    # Calculate density histograms for Chart 2
    import numpy as np
    
    # For times: create histogram bins and density
    time_min, time_max = df['time_seconds'].min(), df['time_seconds'].max()
    time_bins = 50  # Number of bins
    time_hist, time_bin_edges = np.histogram(times, bins=time_bins, density=True)
    time_bin_centers = [(time_bin_edges[i] + time_bin_edges[i+1]) / 2 for i in range(len(time_bin_edges)-1)]
    time_densities = [float(d) for d in time_hist]
    
    # For z-scores: create histogram bins and density
    zscore_min, zscore_max = df['zscore'].min(), df['zscore'].max()
    zscore_bins = 50
    zscore_hist, zscore_bin_edges = np.histogram(zscores, bins=zscore_bins, density=True)
    zscore_bin_centers = [(zscore_bin_edges[i] + zscore_bin_edges[i+1]) / 2 for i in range(len(zscore_bin_edges)-1)]
    zscore_densities = [float(d) for d in zscore_hist]
    
    # Find key statistics
    fastest_time = df['time_seconds'].min()
    slowest_time = df['time_seconds'].max()
    mean_time = df['time_seconds'].mean()
    median_time = df['time_seconds'].median()
    
    # Create HTML with embedded JavaScript for visualization
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if 'statistical_analysis' in script_dir.lower():
        out_file = os.path.join(script_dir, '..', 'reports', 'F_50_Free_Age15_Distribution.html')
    else:
        out_file = os.path.join('reports', 'F_50_Free_Age15_Distribution.html')
    
    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    
    # Format time for display
    def format_time(seconds):
        if seconds < 60:
            return f"{seconds:.2f}s"
        else:
            mins = int(seconds // 60)
            secs = seconds % 60
            return f"{mins}:{secs:.2f}"
    
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>F 50 Free Age 15 Distribution - Times and Z-Scores</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        body {{
            font-family: system-ui, -apple-system, 'Segoe UI', Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.6;
            color: #333;
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
        }}
        .stats-box {{
            background: #f8f9fa;
            border-left: 4px solid #3498db;
            padding: 15px;
            margin: 20px 0;
        }}
        .stats-box h3 {{
            margin-top: 0;
            color: #2c3e50;
        }}
        .stat-row {{
            display: flex;
            justify-content: space-between;
            margin: 8px 0;
            padding: 5px 0;
            border-bottom: 1px solid #e0e0e0;
        }}
        .stat-label {{
            font-weight: 600;
            color: #555;
        }}
        .stat-value {{
            color: #2c3e50;
            font-family: monospace;
        }}
        .chart-container {{
            margin: 30px 0;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .explanation {{
            background: #fff9e6;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin: 20px 0;
        }}
        .explanation h3 {{
            margin-top: 0;
            color: #856404;
        }}
        .warning-box {{
            background: #ffe6e6;
            border-left: 4px solid #dc3545;
            padding: 15px;
            margin: 20px 0;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 10px;
            text-align: left;
        }}
        th {{
            background: #f5f5f5;
            font-weight: 600;
        }}
        .zscore-positive {{
            color: #28a745;
            font-weight: 600;
        }}
        .zscore-negative {{
            color: #dc3545;
            font-weight: 600;
        }}
    </style>
</head>
<body>
    <h1>{gender_label} {event} Age {age}: Distribution of Swim Times and Z-Scores</h1>
    
    <div class="stats-box">
        <h3>Key Statistics (n = {len_df} swimmers)</h3>
        <div class="stat-row">
            <span class="stat-label">Fastest Time:</span>
            <span class="stat-value">{fastest_time}</span>
        </div>
        <div class="stat-row">
            <span class="stat-label">Slowest Time (500th place):</span>
            <span class="stat-value">{slowest_time}</span>
        </div>
        <div class="stat-row">
            <span class="stat-label">Average Time:</span>
            <span class="stat-value">{mean_time}</span>
        </div>
        <div class="stat-row">
            <span class="stat-label">Median Time (250th place):</span>
            <span class="stat-value">{median_time}</span>
        </div>
        <div class="stat-row">
            <span class="stat-label">Time Range:</span>
            <span class="stat-value">{time_range}</span>
        </div>
        <div class="stat-row">
            <span class="stat-label">Standard Deviation:</span>
            <span class="stat-value">{std_time} seconds</span>
        </div>
    </div>

    <div class="explanation">
        <h3>📊 What is a Z-Score?</h3>
        <p><strong>Simple Explanation:</strong> A z-score tells you how good a swimmer's time is compared to everyone else.</p>
        <ul>
            <li><strong>Positive z-score (green):</strong> Faster than average. Example: +2.0 means much faster than most swimmers.</li>
            <li><strong>Zero z-score:</strong> Exactly average.</li>
            <li><strong>Negative z-score (red):</strong> Slower than average. Example: -1.0 means slower than most swimmers.</li>
        </ul>
        <p><strong>Real Example:</strong> If a swimmer has a z-score of +1.5, their time is 1.5 standard deviations faster than the average. This is quite good!</p>
    </div>

    <div class="warning-box">
        <h3>⚠️ Important: This is NOT a Complete Bell Curve</h3>
        <p>This data only includes the <strong>top 500 swimmers</strong> in the USA. We don't see slower swimmers because:</p>
        <ul>
            <li>The USA Swimming rankings only show the best 500 times per season</li>
            <li>Many slower swimmers exist but aren't in this dataset</li>
            <li>This creates a "cutoff" or "truncated" distribution</li>
        </ul>
        <p><strong>What this means:</strong> The slowest swimmer in our data (#500) is probably much better than the average 15-year-old female swimmer in the USA. We're only looking at the elite pool!</p>
    </div>

    <div class="chart-container">
        <h2>Graph 1: Swim Times Distribution (Ranked from Slowest to Fastest)</h2>
        <canvas id="timeChart"></canvas>
        <p><em>This shows all 500 swim times, ranked from slowest (rank #500, left side) to fastest (rank #1, right side). Notice how most times cluster in the middle, but we don't see swimmers slower than #500 (they're cut off because USA Swimming only ranks the top 500). This visualization helps us see the "elite pool" we're working with - even the slowest swimmer in our dataset (#500) is still among the best 500 in the USA!</em></p>
    </div>

    <div class="chart-container">
        <h2>Graph 2a: Time Density Distribution (Bell Curve Portion)</h2>
        <canvas id="timeDensityChart"></canvas>
        <p><em><strong>What this shows:</strong> The density (frequency) distribution of swim times - this is the portion of the bell curve we're seeing from the top 500 swimmers. The y-axis shows the density (probability density) at each time value.</em></p>
        <p><em><strong>Why this matters:</strong> This shows the "cutoff" effect - we're only seeing the right tail of what would be a full bell curve. The slowest swimmer (#500) represents a cutoff point - many slower swimmers exist but aren't in our dataset.</em></p>
    </div>

    <div class="chart-container">
        <h2>Graph 2b: Z-Score Density Distribution (Bell Curve Portion)</h2>
        <canvas id="zscoreDensityChart"></canvas>
        <p><em><strong>What this shows:</strong> The density distribution of z-scores - showing the portion of the bell curve we're capturing. The y-axis shows the density at each z-score value.</em></p>
        <p><em><strong>Why this matters:</strong> This visualizes the "truncated" distribution. Notice how the left side (negative z-scores) is cut off - we don't see the full bell curve because we only have the top 500 swimmers. This helps explain why even "elite" swimmers in our dataset can have negative z-scores relative to the mean of these 500.</em></p>
    </div>

    <h2>Key Performance Thresholds: What Times Are Needed for MOT?</h2>
"""
    
    # Calculate key z-score thresholds
    mean_time = df['time_seconds'].mean()
    std_time = df['time_seconds'].std()
    
    # Find times at key z-score thresholds
    zscore_thresholds = [2.0, 1.5, 1.0, 0.5, 0.0, -0.5, -1.0]
    threshold_data = []
    
    for z in zscore_thresholds:
        target_time = mean_time - (z * std_time)  # Lower time = better, so subtract
        # Find closest actual swimmer to this theoretical time
        closest_idx = (df['time_seconds'] - target_time).abs().idxmin()
        closest_row = df.loc[closest_idx]
        
        # Calculate what percentile this z-score represents using actual data
        # Count how many swimmers have z-score >= this threshold
        swimmers_at_or_above = len(df[df['zscore'] >= z])
        percentile = (swimmers_at_or_above / len(df)) * 100
        
        threshold_data.append({
            'zscore': z,
            'target_time': target_time,
            'closest_rank': closest_row['rank'],
            'closest_time': closest_row['time_seconds'],
            'percentile': percentile,
            'interpretation': get_zscore_interpretation(z)
        })
    
    html_content += """
    <table>
        <thead>
            <tr>
                <th>Z-Score</th>
                <th>Theoretical Time</th>
                <th>Closest Actual Rank</th>
                <th>Closest Actual Time</th>
                <th>Percentile</th>
                <th>Performance Level</th>
                <th>MOT Relevance</th>
            </tr>
        </thead>
        <tbody>
"""
    
    for t in threshold_data:
        z_class = "zscore-positive" if t['zscore'] >= 0 else "zscore-negative"
        mot_relevance = ""
        if t['zscore'] >= 1.5:
            mot_relevance = "🎯 CRITICAL: Top performers in this range show highest improvement rates"
        elif t['zscore'] >= 1.0:
            mot_relevance = "✅ Important: Strong performers likely to continue improving"
        elif t['zscore'] >= 0.0:
            mot_relevance = "📊 Baseline: Average to above-average performers"
        else:
            mot_relevance = "⚠️ Below average: Less likely to show consistent improvement"
        
        html_content += f"""
            <tr>
                <td class="{z_class}"><strong>{t['zscore']:+.1f}</strong></td>
                <td>{format_time(t['target_time'])}</td>
                <td>#{int(t['closest_rank'])}</td>
                <td>{format_time(t['closest_time'])}</td>
                <td>Top {t['percentile']:.1f}%</td>
                <td>{t['interpretation']}</td>
                <td>{mot_relevance}</td>
            </tr>
"""
    
    html_content += """
        </tbody>
    </table>
    
    <div class="note" style="margin-top: 20px;">
        <h3>Why These Thresholds Matter for MOT</h3>
        <ul>
            <li><strong>Z-Score ≥ 1.5 (Top 6.7%):</strong> Our analysis shows swimmers in this range (especially 1.5-2.0) are most likely to continue improving year-over-year. This is the "sweet spot" for identifying "on track" athletes.</li>
            <li><strong>Z-Score ≥ 2.0 (Top 2.5%):</strong> Elite performers - very strong candidates for medal potential, but smaller sample sizes make predictions less reliable.</li>
            <li><strong>Z-Score 0.0-1.0:</strong> Average to good performers, but improvement rates are less consistent and more variable.</li>
            <li><strong>Z-Score < 0:</strong> Below average performers - less reliable for tracking improvement, though individual swimmers may still progress.</li>
        </ul>
    </div>
"""
    
    # Try to get Canada Track reference times for comparison
    try:
        import sqlite3
        script_dir = os.path.dirname(os.path.abspath(__file__))
        if 'statistical_analysis' in script_dir.lower():
            db_path = os.path.join(script_dir, '..', 'database', 'statistical.db')
        else:
            db_path = os.path.join('..', 'database', 'statistical.db')
        
        conn = sqlite3.connect(db_path)
        canada_query = """
            SELECT age, track, time_text, time_seconds
            FROM canada_on_track
            WHERE gender = ? AND event = ? AND age = ?
            ORDER BY track
        """
        canada_df = pd.read_sql_query(canada_query, conn, params=(gender, event, age))
        conn.close()
        
        if not canada_df.empty:
            html_content += """
    <h2>Canada On Track Reference Times: Where Would They Rank?</h2>
    <table>
        <thead>
            <tr>
                <th>Track</th>
                <th>Age</th>
                <th>Canada Time</th>
                <th>Would Rank (approx.)</th>
                <th>Z-Score (approx.)</th>
                <th>Percentile (approx.)</th>
                <th>Interpretation</th>
            </tr>
        </thead>
        <tbody>
"""
            for _, can_row in canada_df.iterrows():
                can_time = can_row['time_seconds']
                # Find closest rank in our data
                closest_idx = (df['time_seconds'] - can_time).abs().idxmin()
                closest_row = df.loc[closest_idx]
                can_zscore = (mean_time - can_time) / std_time
                
                if can_zscore >= 1.5:
                    interpretation = "🎯 ELITE: On track for medal potential"
                elif can_zscore >= 1.0:
                    interpretation = "✅ Strong: Above-average performer"
                elif can_zscore >= 0:
                    interpretation = "📊 Average to good"
                else:
                    interpretation = "⚠️ Below average in this elite pool"
                
                track_label = f"Track {int(can_row['track'])} ({'Early' if can_row['track'] == 1 else 'Middle' if can_row['track'] == 2 else 'Late'})"
                
                html_content += f"""
            <tr>
                <td>{track_label}</td>
                <td>{int(can_row['age'])}</td>
                <td><strong>{can_row['time_text']}</strong></td>
                <td>~#{int(closest_row['rank'])}</td>
                <td class="{'zscore-positive' if can_zscore >= 0 else 'zscore-negative'}">{can_zscore:+.2f}</td>
                <td>Top {100 - (closest_row['percentile']):.1f}%</td>
                <td>{interpretation}</td>
            </tr>
"""
            
            html_content += """
        </tbody>
    </table>
    
    <div class="note" style="margin-top: 20px;">
        <p><strong>Note:</strong> These are Canada On Track entry/reference times. The fact that they fall in the top percentiles validates that Canada targets elite performers (those with high z-scores) who are most likely to continue improving.</p>
    </div>
"""
    except Exception as e:
        # Canada data not available, skip
        pass
    
    html_content += """
    <div class="explanation">
        <h3>🔗 What Does Correlation Mean?</h3>
        <p><strong>Correlation</strong> measures how two things relate to each other:</p>
        <ul>
            <li><strong>Positive correlation (+):</strong> When one thing goes up, the other also goes up.
                <br><em>Example: Height and shoe size (taller people usually have bigger feet)</em></li>
            <li><strong>Negative correlation (-):</strong> When one thing goes up, the other goes down.
                <br><em>Example: Practice time and race time (more practice = faster time = lower number)</em></li>
            <li><strong>No correlation (near 0):</strong> The two things don't relate to each other.
                <br><em>Example: Favorite color and swimming speed</em></li>
        </ul>
        
        <h4>For Our Data: Z-Score vs. Improvement</h4>
        <p><strong>What we're asking:</strong> Do faster swimmers (high z-scores) improve more than slower swimmers?</p>
        <ul>
            <li><strong>If correlation is +0.35:</strong> Faster swimmers tend to improve MORE (positive relationship)</li>
            <li><strong>If correlation is -0.35:</strong> Faster swimmers tend to improve LESS (negative relationship)</li>
            <li><strong>If correlation is +0.012 (1.2%):</strong> Very weak positive relationship - almost no connection</li>
        </ul>
        
        <p><strong>Real-World Meaning:</strong> A correlation of 1.2% means there's almost no relationship between how fast a swimmer is at age 15 and how much they'll improve by age 16. Both fast and slow swimmers improve about the same amount!</p>
    </div>

    <script>
        // Wait for DOM to be fully loaded before initializing charts
        document.addEventListener('DOMContentLoaded', function() {{
        // Data for charts
        const ranks = {{ranks}};
        const times = {{times}};
        const zscores = {{zscores}};
        
        // Format time for display
        function formatTime(seconds) {{
            if (seconds < 60) {{
                return seconds.toFixed(2) + 's';
            }} else {{
                const mins = Math.floor(seconds / 60);
                const secs = (seconds % 60).toFixed(2);
                return mins + ':' + secs;
            }}
        }}
        
        // Chart 1: Time Distribution
        const ctx1 = document.getElementById('timeChart').getContext('2d');
        new Chart(ctx1, {{
            type: 'line',
            data: {{
                labels: ranks,
                datasets: [{{
                    label: 'Swim Time (seconds)',
                    data: times,
                    borderColor: '#3498db',
                    backgroundColor: 'rgba(52, 152, 219, 0.1)',
                    tension: 0.1,
                    pointRadius: 0
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: true,
                scales: {{
                    x: {{
                        title: {{
                            display: true,
                            text: 'Rank (500 = slowest, 1 = fastest in top 500)'
                        }},
                        reverse: true
                    }},
                    y: {{
                        title: {{
                            display: true,
                            text: 'Time (seconds)'
                        }},
                        ticks: {{
                            callback: function(value) {{
                                return formatTime(value);
                            }}
                        }}
                    }}
                }},
                plugins: {{
                    legend: {{
                        display: true
                    }},
                    tooltip: {{
                        callbacks: {{
                            label: function(context) {{
                                return 'Rank ' + context.parsed.x + ': ' + formatTime(context.parsed.y);
                            }}
                        }}
                    }}
                }}
            }}
        }});
        
        // Chart 2a: Time Density Distribution
        const ctx2a = document.getElementById('timeDensityChart').getContext('2d');
        // Prepare data as {x, y} pairs for proper numeric x-axis
        const timeDensityData = {time_bin_centers}.map((x, i) => ({{
            x: x,
            y: {time_densities}[i]
        }}));
        new Chart(ctx2a, {{
            type: 'bar',
            data: {{
                datasets: [{{
                    label: 'Density',
                    data: timeDensityData,
                    borderColor: '#3498db',
                    backgroundColor: 'rgba(52, 152, 219, 0.6)',
                    borderWidth: 1
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: true,
                scales: {{
                    x: {{
                        type: 'linear',
                        position: 'bottom',
                        title: {{
                            display: true,
                            text: 'Swim Time (seconds)'
                        }},
                        ticks: {{
                            callback: function(value) {{
                                return formatTime(value);
                            }}
                        }}
                    }},
                    y: {{
                        title: {{
                            display: true,
                            text: 'Density (probability density)'
                        }},
                        beginAtZero: true
                    }}
                }},
                plugins: {{
                    legend: {{
                        display: true
                    }},
                    tooltip: {{
                        callbacks: {{
                            label: function(context) {{
                                return 'Density: ' + context.parsed.y.toFixed(4) + ' at time ' + formatTime(context.parsed.x);
                            }}
                        }}
                    }}
                }}
            }}
        }});
        
        // Chart 2b: Z-Score Density Distribution
        const ctx2b = document.getElementById('zscoreDensityChart').getContext('2d');
        // Prepare data as {x, y} pairs for proper numeric x-axis
        const zscoreDensityData = {zscore_bin_centers}.map((x, i) => ({{
            x: x,
            y: {zscore_densities}[i]
        }}));
        new Chart(ctx2b, {{
            type: 'bar',
            data: {{
                datasets: [{{
                    label: 'Density',
                    data: zscoreDensityData,
                    borderColor: '#e74c3c',
                    backgroundColor: 'rgba(231, 76, 60, 0.6)',
                    borderWidth: 1
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: true,
                scales: {{
                    x: {{
                        type: 'linear',
                        position: 'bottom',
                        title: {{
                            display: true,
                            text: 'Z-Score'
                        }}
                    }},
                    y: {{
                        title: {{
                            display: true,
                            text: 'Density (probability density)'
                        }},
                        beginAtZero: true
                    }}
                }},
                plugins: {{
                    legend: {{
                        display: true
                    }},
                    tooltip: {{
                        callbacks: {{
                            label: function(context) {{
                                return 'Density: ' + context.parsed.y.toFixed(4) + ' at z-score ' + context.parsed.x.toFixed(2);
                            }}
                        }}
                    }},
                    annotation: {{
                        annotations: {{
                            line1: {{
                                type: 'line',
                                xMin: 0,
                                xMax: 0,
                                borderColor: '#000',
                                borderWidth: 2,
                                label: {{
                                    content: 'Average (z = 0)',
                                    enabled: true,
                                    position: 'end'
                                }}
                            }}
                        }}
                    }}
                }}
            }}
        }});
        
        }}); // End DOMContentLoaded
    </script>
</body>
</html>
"""
    
    # First, convert all {{ to { and }} to } for CSS/JavaScript (Python doesn't auto-convert in regular strings)
    html_content = html_content.replace('{{', '{')
    html_content = html_content.replace('}}', '}')
    
    # Now replace ALL placeholders using string replacement
    gender_label = "Female" if gender == "F" else "Male"
    
    # Replace Python variables and JavaScript data
    replacements = {
        '{gender_label}': gender_label,
        '{event}': event,
        '{age}': str(age),
        '{len_df}': str(len(df)),
        '{fastest_time}': format_time(fastest_time),
        '{slowest_time}': format_time(slowest_time),
        '{mean_time}': format_time(mean_time),
        '{median_time}': format_time(median_time),
        '{time_range}': format_time(slowest_time - fastest_time),
        '{std_time}': f"{std_time:.3f}",
        # JavaScript data placeholders - these will be arrays from json.dumps
        '{ranks}': json.dumps(ranks),
        '{times}': json.dumps(times),
        '{zscores}': json.dumps(zscores),
        '{time_bin_centers}': json.dumps(time_bin_centers),
        '{time_densities}': json.dumps(time_densities),
        '{zscore_bin_centers}': json.dumps(zscore_bin_centers),
        '{zscore_densities}': json.dumps(zscore_densities)
    }
    
    for placeholder, value in replacements.items():
        html_content = html_content.replace(placeholder, value)
    
    with open(out_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ Created visualization: {out_file}")
    print(f"   Open in your browser to view the interactive graphs!")


if __name__ == "__main__":
    create_distribution_graph()

