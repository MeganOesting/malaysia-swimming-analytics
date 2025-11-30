"""
Generate MOT Methodology HTML pages for all events.
Uses data from canada_on_track, usa_delta_data, and mot_base_times tables.
"""

import sqlite3
import os

DB_PATH = r'C:\Users\megan\OneDrive\Documents\Malaysia Swimming Analytics\malaysia_swimming.db'
OUTPUT_DIR = r'C:\Users\megan\OneDrive\Documents\Malaysia Swimming Analytics\public\statistical_analysis\reports'

# Event definitions
EVENTS = [
    # Non-50m events (ages 15-23)
    ('Free', 100), ('Free', 200), ('Free', 400), ('Free', 800), ('Free', 1500),
    ('Back', 100), ('Back', 200),
    ('Breast', 100), ('Breast', 200),
    ('Fly', 100), ('Fly', 200),
    ('Medley', 200), ('Medley', 400),
    # 50m events (ages 18+ only)
    ('Free', 50), ('Back', 50), ('Breast', 50), ('Fly', 50),
]

GENDERS = [('F', 'Female'), ('M', 'Male')]

HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang='en'>
<head>
<meta charset='utf-8'>
<title>{gender_code} {distance} {stroke} - MOT Methodology</title>
<style>
body{{font-family:system-ui,Segoe UI,Arial,sans-serif;margin:24px;max-width:900px;color:#000;background:white}}
h1{{color:#CE1126;border-bottom:3px solid #CE1126;padding-bottom:8px;margin-bottom:8px}}
h2{{color:#00247D;margin-top:28px;border-bottom:2px solid #00247D;padding-bottom:6px}}
h3{{color:#000;margin-top:20px}}
table{{border-collapse:collapse;width:100%;margin:16px 0}}
th,td{{border:1px solid #ccc;padding:10px;font-size:14px;text-align:left;color:#000}}
th{{background:#CE1126;color:#fff;font-weight:600}}
tr:nth-child(even){{background:#fafafa}}
.summary-box{{background:#f8f9fa;border-left:4px solid #CE1126;padding:16px;margin:20px 0}}
.calculation-box{{background:#fff9e6;border-left:4px solid #ffc107;padding:16px;margin:20px 0}}
.source-box{{background:#e8f4f8;border-left:4px solid #00247D;padding:16px;margin:20px 0}}
.warning-box{{background:#fff0f0;border-left:4px solid #cc0000;padding:16px;margin:20px 0}}
.delta-positive{{color:#008000;font-weight:600}}
.delta-negative{{color:#cc0000;font-weight:600}}
a{{color:#CE1126;text-decoration:none}}
a:hover{{color:#000;text-decoration:underline}}
.back-link{{display:inline-block;margin-bottom:20px;padding:6px 12px;background:#CE1126;color:#fff;border-radius:4px}}
.back-link:hover{{background:#a00d1e;color:#fff;text-decoration:none}}
.step{{background:#f0f0f0;padding:12px;margin:8px 0;border-radius:4px}}
.step-num{{display:inline-block;width:28px;height:28px;background:#CE1126;color:#fff;border-radius:50%;text-align:center;line-height:28px;font-weight:bold;margin-right:10px}}
</style>
</head>
<body>

<a href="/mot/index.html" class="back-link">Back to MOT Landing Page</a>

<h1>{gender_full} {distance}m {stroke_full} - MOT Methodology</h1>

{warning_box}

<div class="summary-box">
<h3 style="margin-top:0">Overview</h3>
<p>Malaysia On Track (MOT) times are calculated by working backwards from Canada On Track elite performance targets using age-specific improvement deltas.</p>
<p><strong>Delta Sources:</strong></p>
<ul>
<li><strong>Ages 15 to 18 transitions:</strong> USA Swimming median deltas (fallback to Canada average delta if USA median is negative)</li>
<li><strong>Ages 18+ transitions:</strong> Canada On Track average deltas (averaged across all available tracks)</li>
</ul>
</div>

<h2>1. Canada On Track Reference</h2>

<p>Canada On Track provides developmental tracks for {gender_code} {distance} {stroke}:</p>

{canada_tracks_table}

<h2>2. USA Swimming Improvement Data</h2>

<p>Based on analysis of USA Swimming's top 500 swimmers per age group (2021-2025 seasons):</p>

{usa_delta_table}

{usa_note}

<h2>3. Canada Average Deltas</h2>

<p>Canada deltas are calculated by averaging improvement across all tracks that have data for each transition:</p>

{canada_deltas_table}

<h2>4. MOT Calculation Method</h2>

<div class="calculation-box">
<h3 style="margin-top:0">Approach: Backward Calculation from Canada Track 1 Final Time</h3>
<p>We anchor at the final Track 1 time and work backwards applying the appropriate deltas:</p>

{calculation_steps}
</div>

<h2>5. Final MOT Times for {gender_code} {distance} {stroke}</h2>

{mot_times_table}

<h2>6. Data Sources</h2>

<ul>
<li><strong>Canada On Track Times:</strong> <a href="https://www.swimming.ca/on-track-times/" target="_blank">Swimming Canada On Track Times</a> (April 2025)</li>
<li><strong>Canada On Track Methodology:</strong> <a href="https://www.swimming.ca/wp-content/uploads/2025/04/On-Track-Times-for-SNC-Website-APRIL-2025.pdf" target="_blank">2025 Canada On Track Times PDF</a></li>
<li><strong>USA Improvement Data:</strong> USA Swimming season rankings (top 500 per age/event/gender) from 2021-2025 seasons.</li>
{raw_data_links}
</ul>

<hr style="margin:40px 0;border:none;border-top:2px solid #ddd">

<p style="color:#666;font-size:12px"><em>
Malaysia On Track (MOT) Methodology Document<br>
Last updated: November 2025
</em></p>

</body>
</html>
'''

def format_time(seconds):
    """Format time in seconds to MM:SS.ss or SS.ss format"""
    if seconds is None:
        return "-"
    if seconds >= 60:
        mins = int(seconds // 60)
        secs = seconds % 60
        return f"{mins}:{secs:05.2f}"
    return f"{seconds:.2f}"

def get_canada_tracks(conn, event_id):
    """Get Canada On Track data for an event"""
    cursor = conn.cursor()
    cursor.execute('''
        SELECT canada_track, canada_track_age, canada_track_time_seconds
        FROM canada_on_track
        WHERE event_id = ?
        ORDER BY canada_track, canada_track_age
    ''', (event_id,))
    rows = cursor.fetchall()

    # Organize by track
    tracks = {1: {}, 2: {}, 3: {}}
    for track, age, time_sec in rows:
        tracks[track][age] = time_sec

    return tracks

def get_usa_deltas(conn, event_id):
    """Get USA delta data for an event"""
    cursor = conn.cursor()
    # Get aggregated stats per age transition
    cursor.execute('''
        SELECT usa_delta_age_start, usa_delta_age_end,
               COUNT(*) as sample_size,
               AVG(usa_delta_improvement_seconds) as mean_improvement,
               usa_delta_median
        FROM usa_delta_data
        WHERE usa_delta_event_id = ?
        GROUP BY usa_delta_age_start, usa_delta_age_end
        ORDER BY usa_delta_age_start
    ''', (event_id,))
    rows = cursor.fetchall()

    deltas = {}
    for age_start, age_end, sample_size, mean_imp, median_imp in rows:
        deltas[f"{age_start}_to_{age_end}"] = {
            'sample_size': sample_size,
            'mean': mean_imp,
            'median': median_imp
        }

    return deltas

def get_mot_times(conn, event_id):
    """Get MOT base times for an event"""
    cursor = conn.cursor()
    cursor.execute('''
        SELECT mot_age, mot_time_seconds
        FROM mot_base_times
        WHERE mot_event_id = ?
        ORDER BY mot_age
    ''', (event_id,))
    return {age: time_sec for age, time_sec in cursor.fetchall()}

def calculate_canada_deltas(tracks):
    """Calculate average deltas from Canada track data"""
    deltas = {}
    ages = set()
    for track_data in tracks.values():
        ages.update(track_data.keys())

    ages = sorted(ages)
    for i in range(len(ages) - 1):
        age_start, age_end = ages[i], ages[i + 1]
        track_deltas = []
        for track_num, track_data in tracks.items():
            if age_start in track_data and age_end in track_data:
                delta = track_data[age_start] - track_data[age_end]
                track_deltas.append((track_num, delta))

        if track_deltas:
            avg_delta = sum(d for _, d in track_deltas) / len(track_deltas)
            deltas[f"{age_start}_to_{age_end}"] = {
                'tracks': track_deltas,
                'average': avg_delta
            }

    return deltas

def generate_html(gender_code, gender_full, stroke, distance, conn):
    """Generate HTML for a specific event"""

    # Build event_id
    event_id = f"LCM_{stroke}_{distance}_{gender_code}"
    is_50m = distance == 50

    # Stroke display names
    stroke_display = {
        'Free': 'Freestyle',
        'Back': 'Backstroke',
        'Breast': 'Breaststroke',
        'Fly': 'Butterfly',
        'Medley': 'Individual Medley'
    }
    stroke_full = stroke_display.get(stroke, stroke)

    # Get data
    canada_tracks = get_canada_tracks(conn, event_id)
    usa_deltas = get_usa_deltas(conn, event_id)
    mot_times = get_mot_times(conn, event_id)
    canada_deltas = calculate_canada_deltas(canada_tracks)

    # Warning box for 50m events
    warning_box = ""
    if is_50m:
        warning_box = '''<div class="warning-box">
<h3 style="margin-top:0">Important: 50m Event Limitation</h3>
<p><strong>MOT times for 50m events begin at age 18 only.</strong> Sprint events (50m) are not reliable predictors of elite potential at younger ages because:</p>
<ul>
<li>Sprint performance at ages 15-17 does not correlate strongly with senior elite potential</li>
<li>Physical maturation plays a larger role in sprint events, making early predictions less reliable</li>
</ul>
<p style="margin-top:12px;font-size:0.9em;color:#666;"><em>Note: USA Swimming does not commonly contest 50m events at younger age groups, resulting in insufficient data for 15-17 year olds.</em></p>
</div>'''

    # Canada tracks table
    canada_rows = []
    track_names = ['Track 1 (Early Developers)', 'Track 2 (Middle Developers)', 'Track 3 (Late Developers)']
    for track_num in [1, 2, 3]:
        track_data = canada_tracks.get(track_num, {})
        if track_data:
            ages = sorted(track_data.keys())
            entry_age = min(ages)
            final_age = max(ages)
            target_time = format_time(track_data[final_age])
            canada_rows.append(f"<tr><td>{track_names[track_num-1]}</td><td>{entry_age}</td><td>{final_age}</td><td>{target_time}</td></tr>")

    if canada_rows:
        canada_tracks_table = f'''<table>
<thead><tr><th>Track</th><th>Entry Age</th><th>Final Age</th><th>Target Time</th></tr></thead>
<tbody>
{''.join(canada_rows)}
</tbody>
</table>'''
    else:
        canada_tracks_table = "<p><em>No Canada On Track data available for this event.</em></p>"

    # USA delta table
    usa_rows = []
    usa_note_needed = False
    for transition in ['15_to_16', '16_to_17', '17_to_18']:
        age_start, age_end = transition.split('_to_')
        delta_data = usa_deltas.get(transition, {})

        if delta_data:
            sample = delta_data.get('sample_size', 0)
            median = delta_data.get('median', 0) or 0

            # Calculate percentage (estimate based on typical times)
            pct = abs(median) / 60 * 100 if distance >= 100 else abs(median) / 25 * 100

            delta_class = "delta-positive" if median > 0 else "delta-negative"
            median_str = f"{median:.2f}s" if median else "N/A"
            pct_str = f"{pct:.1f}%"

            if is_50m:
                used = "N/A - MOT starts at 18"
            elif median < 0:
                used = "Fallback to Canada"
                usa_note_needed = True
            else:
                used = "Yes - USA median"

            usa_rows.append(f'<tr><td>{age_start} to {age_end}</td><td>{sample} athletes</td><td class="{delta_class}">{median_str}</td><td class="{delta_class}">{pct_str}</td><td>{used}</td></tr>')
        else:
            usa_rows.append(f'<tr><td>{age_start} to {age_end}</td><td>-</td><td>-</td><td>-</td><td>No data</td></tr>')

    usa_delta_table = f'''<table>
<thead><tr><th>Transition</th><th>Sample Size</th><th>Median Improvement</th><th>% Improvement</th><th>Used in MOT?</th></tr></thead>
<tbody>
{''.join(usa_rows)}
</tbody>
</table>'''

    # USA note
    usa_note = ""
    if usa_note_needed:
        usa_note = '''<div class="source-box">
<strong>Note on Negative Transitions:</strong> When USA median shows regression (negative improvement), we fall back to the Canada On Track average delta for that transition to ensure proper progression.
</div>'''

    # Canada deltas table
    canada_delta_rows = []
    for transition, data in sorted(canada_deltas.items()):
        age_start, age_end = transition.split('_to_')
        track_vals = []
        for track_num in [1, 2, 3]:
            found = [d for t, d in data['tracks'] if t == track_num]
            if found:
                track_vals.append(f"{found[0]:.2f}s")
            else:
                track_vals.append("-")
        avg = f"{data['average']:.2f}s"
        canada_delta_rows.append(f"<tr><td>{age_start} to {age_end}</td><td>{track_vals[0]}</td><td>{track_vals[1]}</td><td>{track_vals[2]}</td><td>{avg}</td></tr>")

    if canada_delta_rows:
        canada_deltas_table = f'''<table>
<thead><tr><th>Transition</th><th>Track 1</th><th>Track 2</th><th>Track 3</th><th>Average</th></tr></thead>
<tbody>
{''.join(canada_delta_rows)}
</tbody>
</table>'''
    else:
        canada_deltas_table = "<p><em>No Canada delta data available.</em></p>"

    # Calculation steps
    steps = []
    step_num = 1

    # Find anchor point (Track 1 final age)
    track1_data = canada_tracks.get(1, {})
    if track1_data:
        anchor_age = max(track1_data.keys())
        anchor_time = track1_data[anchor_age]
        steps.append(f'''<div class="step">
<span class="step-num">{step_num}</span>
<strong>Anchor Point:</strong> Canada Track 1 final time at age {anchor_age} = {format_time(anchor_time)}
</div>''')
        step_num += 1

    # Show backwards calculation
    if mot_times:
        sorted_ages = sorted(mot_times.keys(), reverse=True)
        for i in range(1, min(len(sorted_ages), 6)):
            age = sorted_ages[i]
            time = mot_times[age]
            prev_age = sorted_ages[i-1]
            prev_time = mot_times[prev_age]
            delta = time - prev_time

            # Determine delta source
            transition = f"{age}_to_{prev_age}"
            if transition in usa_deltas and usa_deltas[transition].get('median', 0) > 0 and age < 18:
                source = "USA median"
            else:
                source = "Canada avg delta"

            steps.append(f'''<div class="step">
<span class="step-num">{step_num}</span>
<strong>Age {age}:</strong> {format_time(prev_time)} + {delta:.2f} ({source}) = <strong>{format_time(time)}</strong>
</div>''')
            step_num += 1

    calculation_steps = '\n'.join(steps) if steps else "<p><em>Calculation steps not available.</em></p>"

    # MOT times table
    mot_rows = []
    for age in sorted(mot_times.keys()):
        time = mot_times[age]
        # Determine delta source
        if age == max(mot_times.keys()):
            source = "Canada Track 1 (anchor)"
        elif f"{age}_to_{age+1}" in usa_deltas:
            usa_med = usa_deltas[f"{age}_to_{age+1}"].get('median', 0)
            if usa_med and usa_med > 0 and age < 18:
                source = f"USA median ({age}-{age+1})"
            else:
                source = f"Canada avg ({age}-{age+1})"
        else:
            source = f"Canada avg ({age}-{age+1})"

        mot_rows.append(f"<tr><td>{age}</td><td><strong>{format_time(time)}</strong></td><td>{source}</td></tr>")

    if mot_rows:
        mot_times_table = f'''<table>
<thead><tr><th>Age</th><th>MOT Time</th><th>Delta Source</th></tr></thead>
<tbody>
{''.join(mot_rows)}
</tbody>
</table>'''
    else:
        mot_times_table = "<p><em>No MOT times calculated for this event.</em></p>"

    # Raw data links
    event_name = f"{gender_code} {distance} {stroke}"
    raw_links = f'''<li><strong>Raw Analysis Data:</strong>
<a href="/statistical_analysis/USA%20Data/USA%20Delta%20Data/{event_name.replace(' ', '%20')}%2015%20to%2016/{event_name.replace(' ', '%20')}%2015%20to%2016%20Improvement%20Analysis%20Report.txt" target="_blank">15 to 16 Analysis</a> |
<a href="/statistical_analysis/USA%20Data/USA%20Delta%20Data/{event_name.replace(' ', '%20')}%2016%20to%2017/{event_name.replace(' ', '%20')}%2016%20to%2017%20Improvement%20Analysis%20Report.txt" target="_blank">16 to 17 Analysis</a> |
<a href="/statistical_analysis/USA%20Data/USA%20Delta%20Data/{event_name.replace(' ', '%20')}%2017%20to%2018/{event_name.replace(' ', '%20')}%2017%20to%2018%20Improvement%20Analysis%20Report.txt" target="_blank">17 to 18 Analysis</a></li>'''

    # Generate HTML
    html = HTML_TEMPLATE.format(
        gender_code=gender_code,
        gender_full=gender_full,
        distance=distance,
        stroke=stroke,
        stroke_full=stroke_full,
        warning_box=warning_box,
        canada_tracks_table=canada_tracks_table,
        usa_delta_table=usa_delta_table,
        usa_note=usa_note,
        canada_deltas_table=canada_deltas_table,
        calculation_steps=calculation_steps,
        mot_times_table=mot_times_table,
        raw_data_links=raw_links
    )

    return html

def main():
    conn = sqlite3.connect(DB_PATH)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    generated = 0
    skipped = 0

    for stroke, distance in EVENTS:
        for gender_code, gender_full in GENDERS:
            filename = f"{gender_code}_{distance}_{stroke}_MOT_Methodology.html"
            filepath = os.path.join(OUTPUT_DIR, filename)

            # Skip if already exists (F_50_Free and F_100_Free)
            if os.path.exists(filepath):
                print(f"[SKIP] {filename} already exists")
                skipped += 1
                continue

            try:
                html = generate_html(gender_code, gender_full, stroke, distance, conn)
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(html)
                print(f"[OK] Generated {filename}")
                generated += 1
            except Exception as e:
                print(f"[ERROR] Failed to generate {filename}: {e}")

    conn.close()
    print(f"\nDone! Generated {generated} files, skipped {skipped} existing files.")

if __name__ == '__main__':
    main()
