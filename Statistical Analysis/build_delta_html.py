# -*- coding: utf-8 -*-
import os
import pandas as pd

CSV = 'MOT_Delta_Index.csv'
HTML = 'MOT_Delta_Index.html'
COMPARE_CSV = os.path.join('reports','Delta_Comparison_USA_vs_Canada.csv')
COMPARE_HTML = os.path.join('reports','Delta_Comparison_USA_vs_Canada.html')


def to_file_url(path: str) -> str:
    """Convert relative or absolute path to file:// URL. Uses script location as base for relative paths."""
    # If path is relative, make it relative to script directory
    if not os.path.isabs(path):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(script_dir, path)
    abspath = os.path.abspath(path)
    return 'file:///' + abspath.replace('\\', '/')

TEMPLATE_HEAD = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<title>MOT Delta Index</title>
<style>
body{font-family:system-ui,Segoe UI,Arial,sans-serif;margin:24px;color:#111}
h1{margin:0 0 16px}
summary{font-weight:600;margin:12px 0}
table{border-collapse:collapse;width:100%;table-layout:fixed}
th,td{border:1px solid #ddd;padding:8px;font-size:14px}
th{background:#f5f5f5;text-align:left}
tr:nth-child(even){background:#fafafa}
code{font-family:ui-monospace,Consolas,monospace}
a{color:#c00;text-decoration:none}
a:hover{text-decoration:underline}
.small{font-size:12px;color:#555}
.box{background:#f9f9f9;border:1px solid #e5e5e5;padding:12px;margin:12px 0}
ul{margin:6px 0 0 18px}
</style>
</head>
<body>
<h1>MOT Delta Analysis Index</h1>
<p class="small">Auto-generated from MOT_Delta_Index.csv</p>
"""

LINK_BLOCK = """
<div class="box">
<strong>Related report:</strong>
 <a href="{compare_path}" target="_blank">USA Median Deltas vs Canada On Track (Track 1–3)</a>
</div>
"""

HIGHLIGHTS_BLOCK_HEAD = """
<div class="box">
<strong>Top 5 USA–Canada delta differences (|USA median − Canada track|):</strong>
<ul>
"""

HIGHLIGHTS_BLOCK_FOOT = """
</ul>
</div>
"""

TABLE_HEAD = """
<table>
<thead>
<tr>
  <th>Gender</th>
  <th>Event</th>
  <th>Age From</th>
  <th>Age To</th>
  <th>Period From</th>
  <th>Period To</th>
  <th>n</th>
  <th>Median Δ (s)</th>
  <th>Mean Δ (s)</th>
  <th>Std (s)</th>
  <th>Q25</th>
  <th>Q75</th>
  <th>Folder</th>
  <th>CSV</th>
  <th>Report</th>
</tr>
</thead>
<tbody>
"""

TEMPLATE_FOOT = """
</tbody>
</table>
</body>
</html>
"""


def main() -> None:
    if not os.path.exists(CSV):
        print(f"Index CSV not found: {CSV}")
        return

    df = pd.read_csv(CSV, encoding='utf-8')
    for col in ['gender','event','age_from','age_to','period_from','period_to','delta_folder_path','csv_path','report_path']:
        if col in df.columns:
            df[col] = df[col].astype(str)

    # Optional: load comparison CSV to build highlights
    highlights_html = ''
    if os.path.exists(COMPARE_CSV):
        comp = pd.read_csv(COMPARE_CSV, encoding='utf-8')
        for c in ['median_improvement','can_delta','delta_diff_seconds','sample_size']:
            if c in comp.columns:
                comp[c] = pd.to_numeric(comp[c], errors='coerce')
        comp['abs_diff'] = (comp['median_improvement'] - comp['can_delta']).abs()
        comp = comp.dropna(subset=['abs_diff'])
        if not comp.empty:
            top5 = comp.sort_values('abs_diff', ascending=False).head(5)
            items = []
            for _, r in top5.iterrows():
                items.append(
                    f"<li>{r.get('gender','')} {r.get('event','')} {r.get('age_from','')}→{r.get('age_to','')} — "
                    f"USA median Δ: {'' if pd.isna(r.get('median_improvement')) else f'{float(r.get('median_improvement')):.3f}s'}, "
                    f"Canada ({'' if pd.isna(r.get('can_track')) else r.get('can_track')}): {'' if pd.isna(r.get('can_delta')) else f'{float(r.get('can_delta')):.3f}s'}, "
                    f"diff: {float(r.get('abs_diff')):.3f}s</li>"
                )
            highlights_html = HIGHLIGHTS_BLOCK_HEAD + "\n".join(items) + HIGHLIGHTS_BLOCK_FOOT

    rows = []
    for _, r in df.iterrows():
        folder_url = to_file_url(r.get('delta_folder_path',''))
        csv_url = to_file_url(r.get('csv_path',''))
        report_url = to_file_url(r.get('report_path',''))
        rows.append(
            f"<tr>"
            f"<td>{r.get('gender','')}</td>"
            f"<td>{r.get('event','')}</td>"
            f"<td>{r.get('age_from','')}</td>"
            f"<td>{r.get('age_to','')}</td>"
            f"<td>{r.get('period_from','')}</td>"
            f"<td>{r.get('period_to','')}</td>"
            f"<td>{int(float(r.get('sample_size',0) or 0))}</td>"
            f"<td>{float(r.get('median_improvement',0.0)):.3f}</td>"
            f"<td>{float(r.get('mean_improvement',0.0)):.3f}</td>"
            f"<td>{float(r.get('std_improvement',0.0)):.3f}</td>"
            f"<td>{float(r.get('q25_improvement',0.0)):.3f}</td>"
            f"<td>{float(r.get('q75_improvement',0.0)):.3f}</td>"
            f"<td><a href='{folder_url}' target='_blank'>folder</a></td>"
            f"<td><a href='{csv_url}' target='_blank'>csv</a></td>"
            f"<td><a href='{report_url}' target='_blank'>report</a></td>"
            f"</tr>"
        )

    link_html = ''
    if os.path.exists(COMPARE_HTML):
        link_html = LINK_BLOCK.format(compare_path=to_file_url(COMPARE_HTML))

    html = TEMPLATE_HEAD + link_html + highlights_html + TABLE_HEAD + "\n".join(rows) + TEMPLATE_FOOT
    with open(HTML, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"Wrote HTML index: {HTML}")


if __name__ == '__main__':
    main()
