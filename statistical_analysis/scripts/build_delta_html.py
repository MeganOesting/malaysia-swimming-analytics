# -*- coding: utf-8 -*-
"""
Build MOT Delta Analysis Landing Page HTML
Generates an interactive index page with links to all delta analyses and raw data.
"""

import os
import pandas as pd
import glob
from pathlib import Path

# Handle both old and new folder structures
script_dir = os.path.dirname(os.path.abspath(__file__))
if 'statistical_analysis' in script_dir.lower():
    # New structure: files in statistical_analysis/ directory
    CSV = os.path.join(script_dir, '..', 'MOT_Delta_Index.csv')
    HTML = os.path.join(script_dir, '..', 'MOT_Delta_Analysis_Index.html')
    PERIOD_DATA_BASE = os.path.join(script_dir, '..', 'data', 'Period Data')
    DELTA_DATA_BASE = os.path.join(script_dir, '..', 'data', 'Delta Data')
    REPORTS_BASE = os.path.join(script_dir, '..', 'reports')
else:
    # Old structure: files in same directory as script
    CSV = "MOT_Delta_Index.csv"
    HTML = 'MOT_Delta_Analysis_Index.html'
    PERIOD_DATA_BASE = os.path.join('data', 'Period Data')
    DELTA_DATA_BASE = os.path.join('data', 'Delta Data')
    REPORTS_BASE = 'reports'

# Normalize to absolute paths
CSV = os.path.abspath(CSV)
HTML = os.path.abspath(HTML)
PERIOD_DATA_BASE = os.path.abspath(PERIOD_DATA_BASE)
DELTA_DATA_BASE = os.path.abspath(DELTA_DATA_BASE)
REPORTS_BASE = os.path.abspath(REPORTS_BASE)

# Canonical event order
EVENT_ORDER = [
    '50 Free', '100 Free', '200 Free', '400 Free', '800 Free', '1500 Free',
    '100 Back', '200 Back',
    '100 Breast', '200 Breast',
    '100 Fly', '200 Fly',
    '200 IM', '400 IM'
]


def find_raw_data_file(gender: str, event: str, age: int) -> str:
    """Find the most recent raw data file for a given gender/event/age."""
    if not os.path.exists(PERIOD_DATA_BASE):
        return None
    
    # Look for period folders (most recent first)
    period_folders = sorted(
        [d for d in os.listdir(PERIOD_DATA_BASE) if os.path.isdir(os.path.join(PERIOD_DATA_BASE, d))],
        reverse=True
    )
    
    for period in period_folders:
        # Look for event folder: {Gender} {Event} {period}
        event_folder_pattern = f"{gender} {event} {period}"
        event_folder_path = os.path.join(PERIOD_DATA_BASE, period, event_folder_pattern)
        
        if os.path.exists(event_folder_path):
            # Look for age-specific file: {Gender} {Event} {Age} {period}.txt
            file_pattern = f"{gender} {event} {age} {period}.txt"
            file_path = os.path.join(event_folder_path, file_pattern)
            
            if os.path.exists(file_path):
                return file_path
    
    return None


def build_raw_data_links(gender: str, event: str) -> str:
    """Build HTML links for raw data files (ages 15-18)."""
    links = []
    for age in [15, 16, 17, 18]:
        file_path = find_raw_data_file(gender, event, age)
        if file_path:
            url = Path(file_path).as_uri()
            links.append(f'<a href="{url}" target="_blank" title="Raw data for age {age}">{age}</a>')
        else:
            links.append(f'<span style="color:#999;">{age}</span>')
    
    return ' | '.join(links)


def build_improvement_links(gender: str, event: str, df_index: pd.DataFrame) -> str:
    """Build HTML links for improvement analyses."""
    # MOT Analysis report link
    mot_report_name = f"{gender}_{event.replace(' ', '_')}_MOT_Delta_Analysis.html"
    mot_report_path = os.path.join(REPORTS_BASE, mot_report_name)
    if os.path.exists(mot_report_path):
        mot_url = Path(mot_report_path).as_uri()
        links = [f'<a href="{mot_url}" target="_blank" title="Comprehensive MOT Delta Analysis Report" style="font-weight:600;">MOT Analysis</a>']
    else:
        links = []
    
    # Age transition links (15→16, 16→17, 17→18)
    for age_from, age_to in [(15, 16), (16, 17), (17, 18)]:
        folder_name = f"{gender} {event} {age_from} to {age_to}"
        delta_folder = os.path.join(DELTA_DATA_BASE, folder_name)
        
        if os.path.exists(delta_folder):
            # Find stats from CSV
            row = df_index[
                (df_index['gender'] == gender) &
                (df_index['event'] == event) &
                (df_index['age_from'] == age_from) &
                (df_index['age_to'] == age_to)
            ]
            
            if not row.empty:
                sample_size = int(row.iloc[0].get('sample_size', 0))
                median_delta = row.iloc[0].get('median_improvement', 0)
                delta_str = f"{median_delta:.3f}s" if median_delta >= 0 else f"{median_delta:.3f}s"
                title = f"Report (n={sample_size}, Δ={delta_str})"
            else:
                title = "Report"
            
            report_file = os.path.join(delta_folder, f"{folder_name} Improvement Analysis Report.txt")
            csv_file = os.path.join(delta_folder, f"{folder_name} Athlete_Improvement_Data.csv")
            
            transition_links = []
            if os.path.exists(report_file):
                report_url = Path(report_file).as_uri()
                transition_links.append(f'<a href="{report_url}" target="_blank" title="{title}">{age_from}→{age_to}</a>')
            
            folder_url = Path(delta_folder).as_uri()
            transition_links.append(f'<a href="{folder_url}" target="_blank" title="Folder">Folder</a>')
            
            if os.path.exists(csv_file):
                csv_url = Path(csv_file).as_uri()
                transition_links.append(f'<a href="{csv_url}" target="_blank" title="CSV">CSV</a>')
            
            if transition_links:
                links.append(' | '.join(transition_links))
        else:
            links.append(f'<span style="color:#999;">{age_from}→{age_to} N/A</span>')
    
    return '<br>'.join(links)  # Use <br> instead of ' | ' for better spacing


def validate_html_structure(html_content: str) -> tuple[bool, list[str]]:
    """Validate basic HTML structure and return (is_valid, error_messages)."""
    errors = []
    
    # Check for required tags
    required_tags = {
        '<html': '</html>',
        '<head': '</head>',
        '<body': '</body>',
    }
    
    for open_tag, close_tag in required_tags.items():
        if open_tag not in html_content.lower():
            errors.append(f"Missing opening tag: {open_tag}")
        if close_tag not in html_content.lower():
            errors.append(f"Missing closing tag: {close_tag}")
    
    # Check for style tag closure if style tag exists
    if '<style>' in html_content or '<style ' in html_content.lower():
        if '</style>' not in html_content:
            errors.append("Missing closing </style> tag")
    
    # Check for script tag closure if script tag exists
    if '<script>' in html_content or '<script ' in html_content.lower():
        if '</script>' not in html_content:
            errors.append("Missing closing </script> tag")
    
    return len(errors) == 0, errors


def main():
    """Generate the HTML landing page."""
    # Read index CSV
    if not os.path.exists(CSV):
        print(f"Index CSV not found: {CSV}")
        return
    
    df_index = pd.read_csv(CSV, encoding='utf-8')
    
    # Build consolidated table rows
    consolidated_rows = []
    for event in EVENT_ORDER:
        row_parts = []
        
        # Event name
        row_parts.append(f"<td style='font-weight:600;font-size:0.95em;white-space:nowrap;color:#000;'>{event}</td>")
        
        # Female raw data and improvements
        f_raw = build_raw_data_links('F', event)
        f_improve = build_improvement_links('F', event, df_index)
        row_parts.append(f"<td style='white-space:nowrap;font-size:0.9em;color:#000;'>{f_raw}</td>")
        row_parts.append(f"<td style='font-size:0.85em;white-space:normal;color:#000;'>{f_improve}</td>")
        
        # Male raw data and improvements
        m_raw = build_raw_data_links('M', event)
        m_improve = build_improvement_links('M', event, df_index)
        row_parts.append(f"<td style='white-space:nowrap;font-size:0.9em;color:#000;'>{m_raw}</td>")
        row_parts.append(f"<td style='font-size:0.85em;white-space:normal;color:#000;'>{m_improve}</td>")
        
        consolidated_rows.append('<tr>' + ''.join(row_parts) + '</tr>')
    
    # Build HTML
    html_content = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate" />
<meta http-equiv="Pragma" content="no-cache" />
<meta http-equiv="Expires" content="0" />
<title>MOT Delta Analysis - Landing Page</title>
<style>
body{{font-family:system-ui,Segoe UI,Arial,sans-serif;margin:24px;color:#000;max-width:1200px;background:white}}
h1{{margin:0 0 16px;color:#CE1126;border-bottom:3px solid #CE1126;padding-bottom:10px}}
h2{{color:#000;margin-top:30px;margin-bottom:15px;border-bottom:2px solid #00247D;padding-bottom:6px}}
summary{{font-weight:600;margin:12px 0}}
table{{border-collapse:collapse;width:100%;table-layout:fixed}}
th,td{{border:1px solid #ccc;padding:8px;font-size:14px;color:#000}}
th{{background:#CE1126;color:#fff;text-align:left;font-weight:600}}
tr:nth-child(even){{background:#fafafa}}
tr:hover{{background:#f5f5f5}}
code{{font-family:ui-monospace,Consolas,monospace}}
a{{color:#CE1126;text-decoration:none;font-weight:500}}
a:hover{{color:#000!important;text-decoration:underline}}
.small{{font-size:12px;color:#000}}
.box{{background:white;border:1px solid #ccc;padding:12px;margin:12px 0}}
.methodology-box{{background:white;border-left:5px solid #CE1126;padding:12px;margin:15px 0}}
.methodology-box h2{{margin-top:0;color:#CE1126;font-size:1.3em;margin-bottom:8px;border:none;padding:0;display:flex;align-items:center;gap:8px}}
.icon-bars{{display:inline-flex;gap:3px;align-items:flex-end;height:20px}}
.icon-bar{{width:6px;background:#00247D;height:16px}}
.icon-bar:nth-child(1){{background:#00247D;height:16px}}
.icon-bar:nth-child(2){{background:#CE1126;height:20px}}
.icon-bar:nth-child(3){{background:#000;height:14px}}
.methodology-box p{{line-height:1.6;margin:6px 0;font-size:0.95em}}
.methodology-box ul{{margin:6px 0;padding-left:25px}}
.methodology-box li{{margin:5px 0;font-size:0.95em}}
.methodology-box h3{{margin:8px 0 4px 0;font-size:1.1em;color:#000;font-weight:600}}
.methodology-box ul li{{color:#000}}
.methodology-box ul li strong{{color:#000}}
.stats-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:10px;margin:10px 0}}
.stat-card{{background:white;border:1px solid #ccc;padding:6px;text-align:center;border-radius:4px;height:45px;display:flex;flex-direction:column;justify-content:center}}
.stat-value{{font-size:1.3em;font-weight:bold;color:#CE1126;margin:2px 0}}
.stat-label{{color:#000;font-size:0.75em}}
.methodology-button{{background:#CE1126;color:white;padding:6px 16px;border-radius:4px;text-decoration:none;font-weight:500;height:45px;display:flex;align-items:center;justify-content:center;width:fit-content;min-width:120px;box-sizing:border-box}}
.methodology-button:hover{{background:#a00d1e;text-decoration:none}}
.nav-section{{background:white;border:1px solid #ccc;padding:20px;margin:20px 0;border-radius:6px}}
.nav-section h3{{margin-top:0;color:#CE1126}}
.nav-links{{display:flex;flex-wrap:wrap;gap:15px;margin-top:15px}}
.nav-links a{{background:#CE1126;color:white;padding:10px 20px;border-radius:4px;display:inline-block}}
.nav-links a:hover{{background:#a00d1e;text-decoration:none}}
ul{{margin:6px 0 0 18px}}
.key-point{{font-weight:600;color:#CE1126}}
.consolidated-table a{{color:#000}}
.consolidated-table a:hover{{color:#CE1126;text-decoration:underline}}
</style>
</head>
<body>
<h1>Malaysia On Track (MOT) Delta Analysis</h1>

<div class="methodology-box">
<h2><span class="icon-bars"><span class="icon-bar"></span><span class="icon-bar"></span><span class="icon-bar"></span></span> Understanding the Data</h2>
<p style="color:#000;font-size:0.9em;margin-bottom:10px;">Comprehensive analysis of improvement patterns for competitive swimmers ages 15-18</p>
<p>Understanding our data's characteristics is essential for correctly interpreting the results.</p>

<div class="stats-grid">
    <div class="stat-card">
        <div class="stat-value">500</div>
        <div class="stat-label">Top Swimmers per Dataset</div>
    </div>
    <div class="stat-card">
        <div class="stat-value">84</div>
        <div class="stat-label">Improvement Analyses</div>
    </div>
    <div class="stat-card">
        <div class="stat-value">~112,000</div>
        <div class="stat-label">Raw Data Records</div>
    </div>
    <div class="stat-card">
        <div class="stat-value">4</div>
        <div class="stat-label">Seasons (2021-2025)</div>
    </div>
</div>
<h3>Key Assumptions & Characteristics:</h3>
<ul>
    <li><span class="key-point">Elite Sample Only:</span> We have the top 500 swimmers per event/gender/age, representing approximately <strong>7-12%</strong> of all competitive swimmers for popular events.</li>
    <li><span class="key-point">Distribution Shape:</span> The full population would be <strong>highly right-skewed</strong> (many slower swimmers, few elite swimmers). Our sample is <strong>left-truncated</strong> (top 500 US Swimmers only), which is appropriate for setting the MOT times designed to identify swimmers on track for elite performance.</li>
</ul>

<p style="margin-top:15px;">
    <strong>📖 For complete methodology details, see:</strong> <a href="file:///{REPORTS_BASE.replace(os.sep, '/')}/MOT_Data_Methodology_and_Assumptions.html" target="_blank">Full Methodology Report</a> | 
    <strong>📊 For overarching insights and patterns across all events, see:</strong> <a href="file:///{REPORTS_BASE.replace(os.sep, '/')}/DATA_INTERPRETATION_GUIDE.md" target="_blank">Data Interpretation Guide</a> |
    <strong>📈 For gender pattern analysis, see:</strong> <a href="file:///{REPORTS_BASE.replace(os.sep, '/')}/Gender_Patterns_Summary.md" target="_blank">Gender Patterns Summary</a>
</p>
</div>

<div class="nav-section">
<h3>🔍 Navigate to Specific Events</h3>
<p>Click on any event below to jump directly to its analysis results in the main table, or use the links in the table below to view raw data and improvement analyses.</p>

<table class="consolidated-table" style="margin-top:15px;font-size:0.9em;width:100%;table-layout:auto;">
<colgroup>
  <col style="width:100px;">
  <col style="width:100px;">
  <col style="width:auto;">
  <col style="width:100px;">
  <col style="width:auto;">
</colgroup>
<thead>
<tr style="background:#CE1126;color:#fff;">
  <th style="padding:8px;">Event</th>
  <th style="padding:8px;">Raw Data (Female)</th>
  <th style="padding:8px;">Improvements (Female)</th>
  <th style="padding:8px;">Raw Data (Male)</th>
  <th style="padding:8px;">Improvements (Male)</th>
</tr>
</thead>
<tbody>
{''.join(consolidated_rows)}
</tbody>
</table>

</div>

<div style="margin-top:40px;padding-top:20px;border-top:2px solid #ccc;color:#000;font-size:0.9em;line-height:1.5;">
    <p><strong>Report Generated:</strong> November 2025</p>
    <p><strong>Data Sources:</strong> USA Swimming season rankings (2021-2025), Canada On Track reference times (April 2025)</p>
    <p><strong>Project:</strong> Malaysia On Track (MOT) Delta Analysis</p>
</div>

</body>
</html>"""
    
    # Fix path separators in HTML
    html_content = html_content.replace('\\', '/')
    
    # Validate HTML
    is_valid, errors = validate_html_structure(html_content)
    if not is_valid:
        print("HTML validation errors:")
        for error in errors:
            print(f"  - {error}")
        return

    # Write HTML file
    with open(HTML, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"Wrote HTML index: {HTML}")


if __name__ == '__main__':
    main()
