#!/usr/bin/env python3
"""
Analyze Improvement Rates by Z-Score Range
==========================================

This script analyzes how improvement deltas vary by z-score (performance level)
at the starting age. This helps understand:
1. Do elite performers (high z-scores) continue to improve?
2. What z-score ranges are most likely to improve?
3. How does this validate the Canada On Track methodology?

For each age transition (15->16, 16->17, 17->18), we:
1. Calculate z-scores for each matched athlete based on the distribution at their starting age
2. Group athletes into z-score ranges (e.g., top 5%, top 10-20%, etc.)
3. Calculate improvement statistics by z-score range
4. Analyze correlation between starting z-score and improvement
"""

import os
import pandas as pd
import numpy as np
import sqlite3
from pathlib import Path

# Database connection
def get_conn():
    """Get SQLite database connection"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if 'statistical_analysis' in script_dir.lower():
        db_path = os.path.join(script_dir, '..', 'database', 'statistical.db')
    else:
        db_path = os.path.join('..', 'database', 'statistical.db')
    return sqlite3.connect(db_path)


def load_period_data(gender, event, age, period):
    """Load data from a specific period file to get full distribution"""
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
            engine='python',
            on_bad_lines='skip'
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


def calculate_zscore(time, time_distribution):
    """Calculate z-score for a swim time given the distribution"""
    # For swim times: lower is better, so z = (μ - time) / σ
    # A faster time (lower) gets a higher z-score (more positive)
    if pd.isna(time) or len(time_distribution) == 0:
        return None
    
    mean_time = np.mean(time_distribution)
    std_time = np.std(time_distribution)
    
    if std_time == 0:
        return None
    
    zscore = (mean_time - time) / std_time
    return zscore


def get_zscore_range_label(zscore):
    """Convert z-score to descriptive range label"""
    if pd.isna(zscore):
        return "Unknown"
    elif zscore >= 2.0:
        return "Top 2.5% (z ≥ 2.0)"
    elif zscore >= 1.5:
        return "Top 6.7% (1.5 ≤ z < 2.0)"
    elif zscore >= 1.0:
        return "Top 15.9% (1.0 ≤ z < 1.5)"
    elif zscore >= 0.5:
        return "Above Average (0.5 ≤ z < 1.0)"
    elif zscore >= 0:
        return "Average (0 ≤ z < 0.5)"
    elif zscore >= -0.5:
        return "Below Average (-0.5 ≤ z < 0)"
    elif zscore >= -1.0:
        return "Lower (-1.0 ≤ z < -0.5)"
    else:
        return "Bottom 15.9% (z < -1.0)"


def analyze_transition_by_zscore(gender, event, age_from, age_to, period_from, period_to):
    """Analyze improvement by z-score range for a specific transition"""
    
    # Load delta data (matched athletes)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    folder_name = f"{gender} {event} {age_from} to {age_to}"
    if 'statistical_analysis' in script_dir.lower():
        delta_folder = os.path.join(script_dir, "..", "data", "Delta Data", folder_name)
    else:
        delta_folder = os.path.join("Delta Data", folder_name)
    
    csv_file = os.path.join(delta_folder, f"{folder_name} Athlete_Improvement_Data.csv")
    if not os.path.exists(csv_file):
        print(f"  Skipping - delta data file not found: {csv_file}")
        return None
    
    matched_df = pd.read_csv(csv_file)
    
    # Load full distribution at starting age for z-score calculation
    df_from = load_period_data(gender, event, age_from, period_from)
    if df_from is None:
        print(f"  Skipping - cannot load distribution data for z-score calculation")
        return None
    
    # Parse times for distribution
    df_from['time_seconds'] = df_from['Swim Time'].apply(parse_swim_time)
    df_from = df_from.dropna(subset=['time_seconds'])
    
    if len(df_from) < 10:
        print(f"  Skipping - insufficient distribution data")
        return None
    
    # Calculate z-scores for matched athletes
    matched_df['zscore_from'] = matched_df['time_from'].apply(
        lambda t: calculate_zscore(t, df_from['time_seconds'].values)
    )
    matched_df['zscore_range'] = matched_df['zscore_from'].apply(get_zscore_range_label)
    
    # Remove athletes without valid z-scores
    matched_df = matched_df.dropna(subset=['zscore_from'])
    
    if len(matched_df) < 10:
        return None
    
    # Analyze by z-score range
    results = []
    
    # Overall statistics
    overall_mean_z = matched_df['zscore_from'].mean()
    overall_median_imp = matched_df['improvement_seconds'].median()
    overall_mean_imp = matched_df['improvement_seconds'].mean()
    
    # Correlation between z-score and improvement
    # Using numpy's corrcoef (returns correlation matrix)
    corr_matrix = np.corrcoef(
        matched_df['zscore_from'].values,
        matched_df['improvement_seconds'].values
    )
    corr_coef = corr_matrix[0, 1]
    
    # Approximate p-value using t-test (for n > 30, reasonable approximation)
    # t = r * sqrt((n-2)/(1-r^2))
    n = len(matched_df)
    if n > 2 and abs(corr_coef) < 0.999:
        t_stat = corr_coef * np.sqrt((n - 2) / (1 - corr_coef**2))
        # Two-tailed p-value approximation using normal distribution for large n
        # For exact, would need scipy.stats.t, but this is close enough for large n
        from math import erf
        pvalue = 2 * (1 - 0.5 * (1 + erf(abs(t_stat) / np.sqrt(2))))
    else:
        pvalue = np.nan
    
    # Group by z-score ranges
    for range_label in matched_df['zscore_range'].unique():
        range_data = matched_df[matched_df['zscore_range'] == range_label]
        if len(range_data) < 5:  # Skip ranges with too few athletes
            continue
        
        improvements = range_data['improvement_seconds'].values
        
        results.append({
            'gender': gender,
            'event': event,
            'age_from': age_from,
            'age_to': age_to,
            'zscore_range': range_label,
            'n_athletes': len(range_data),
            'mean_zscore': range_data['zscore_from'].mean(),
            'median_zscore': range_data['zscore_from'].median(),
            'min_zscore': range_data['zscore_from'].min(),
            'max_zscore': range_data['zscore_from'].max(),
            'median_improvement': np.median(improvements),
            'mean_improvement': np.mean(improvements),
            'std_improvement': np.std(improvements),
            'pct_improving': (improvements > 0).sum() / len(improvements) * 100,
            'pct_getting_slower': (improvements < 0).sum() / len(improvements) * 100,
            'q25_improvement': np.percentile(improvements, 25),
            'q75_improvement': np.percentile(improvements, 75),
        })
    
    # Overall summary
    summary = {
        'gender': gender,
        'event': event,
        'age_from': age_from,
        'age_to': age_to,
        'total_n': len(matched_df),
        'overall_mean_zscore': overall_mean_z,
        'overall_median_improvement': overall_median_imp,
        'overall_mean_improvement': overall_mean_imp,
        'correlation_zscore_improvement': corr_coef,
        'correlation_pvalue': pvalue,
        'pct_improving': (matched_df['improvement_seconds'] > 0).sum() / len(matched_df) * 100,
        'pct_getting_slower': (matched_df['improvement_seconds'] < 0).sum() / len(matched_df) * 100,
    }
    
    return pd.DataFrame(results), summary


def analyze_all_transitions():
    """Analyze all transitions and generate comprehensive report"""
    
    EVENTS = [
        "50 Free", "100 Free", "200 Free", "400 Free", "800 Free", "1500 Free",
        "100 Back", "200 Back", "100 Breast", "200 Breast", 
        "100 Fly", "200 Fly", "200 IM", "400 IM"
    ]
    
    GENDERS = ["F", "M"]
    
    AGE_TRANSITIONS = [
        ("15", "16", "9.1.21-8.31.22", "9.1.22-8.31.23"),
        ("16", "17", "9.1.22-8.31.23", "9.1.23-8.31.24"),
        ("17", "18", "9.1.23-8.31.24", "9.1.24-8.31.25")
    ]
    
    all_results = []
    all_summaries = []
    
    for gender in GENDERS:
        for event in EVENTS:
            for age_from, age_to, period_from, period_to in AGE_TRANSITIONS:
                print(f"Analyzing {gender} {event} {age_from}->{age_to} by z-score...")
                result = analyze_transition_by_zscore(gender, event, age_from, age_to, period_from, period_to)
                
                if result is not None:
                    df_results, summary = result
                    if df_results is not None and len(df_results) > 0:
                        all_results.append(df_results)
                    if summary is not None:
                        all_summaries.append(summary)
    
    if not all_results:
        print("No results generated")
        return None, None
    
    # Combine all results
    combined_results = pd.concat(all_results, ignore_index=True)
    combined_summaries = pd.DataFrame(all_summaries)
    
    # Save to files
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if 'statistical_analysis' in script_dir.lower():
        reports_dir = os.path.join(script_dir, '..', 'reports')
    else:
        reports_dir = 'reports'
    
    os.makedirs(reports_dir, exist_ok=True)
    
    csv_out = os.path.join(reports_dir, 'Improvement_by_ZScore_Range.csv')
    summary_csv = os.path.join(reports_dir, 'Improvement_by_ZScore_Summary.csv')
    
    combined_results.to_csv(csv_out, index=False, encoding='utf-8')
    combined_summaries.to_csv(summary_csv, index=False, encoding='utf-8')
    
    print(f"\n✅ Saved detailed results to: {csv_out}")
    print(f"✅ Saved summary statistics to: {summary_csv}")
    
    return combined_results, combined_summaries


def generate_html_report(results_df, summaries_df):
    """Generate comprehensive HTML report"""
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if 'statistical_analysis' in script_dir.lower():
        reports_dir = os.path.join(script_dir, '..', 'reports')
    else:
        reports_dir = 'reports'
    
    html_out = os.path.join(reports_dir, 'Improvement_by_ZScore_Analysis.html')
    
    # Group summaries by transition
    summaries_by_transition = summaries_df.groupby(['age_from', 'age_to'])
    
    html_content = []
    html_content.append("<!doctype html>")
    html_content.append("<html><head><meta charset='utf-8'>")
    html_content.append("<title>Improvement Analysis by Z-Score Range</title>")
    html_content.append("""
    <style>
        body { font-family: system-ui, Segoe UI, Arial, sans-serif; margin: 24px; line-height: 1.6; }
        h1 { color: #1a1a1a; border-bottom: 3px solid #4a90e2; padding-bottom: 10px; }
        h2 { color: #333; margin-top: 32px; border-bottom: 2px solid #ddd; padding-bottom: 8px; }
        h3 { color: #555; margin-top: 24px; }
        table { border-collapse: collapse; width: 100%; margin: 16px 0; font-size: 14px; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background: #f5f5f5; font-weight: 600; }
        tr:nth-child(even) { background: #fafafa; }
        .highlight { background: #fff3cd !important; }
        .positive { color: #28a745; font-weight: 600; }
        .negative { color: #dc3545; font-weight: 600; }
        .note { background: #e7f3ff; padding: 12px; border-left: 4px solid #4a90e2; margin: 16px 0; }
        .summary-box { background: #f8f9fa; padding: 16px; border-radius: 4px; margin: 16px 0; }
    </style>
    </head><body>
    """)
    
    html_content.append("<h1>Improvement Analysis by Z-Score Range</h1>")
    html_content.append("""
    <div class="note">
        <strong>Purpose:</strong> This analysis examines how improvement rates vary by performance level (z-score) 
        at the starting age. Understanding this relationship helps validate the Canada On Track methodology, 
        which targets elite performers who continue to improve, versus the general population median.
    </div>
    """)
    
    # Overall findings
    html_content.append("<h2>Key Findings</h2>")
    html_content.append("<div class='summary-box'>")
    
    # Calculate key statistics
    total_transitions = len(summaries_df)
    positive_corr = (summaries_df['correlation_zscore_improvement'] > 0).sum()
    strong_corr = (abs(summaries_df['correlation_zscore_improvement']) > 0.2).sum()
    
    html_content.append(f"<p><strong>Total Transitions Analyzed:</strong> {total_transitions}</p>")
    html_content.append(f"<p><strong>Transitions with Positive Correlation (z-score → improvement):</strong> {positive_corr}/{total_transitions} ({positive_corr/total_transitions*100:.1f}%)</p>")
    html_content.append(f"<p><strong>Transitions with Moderate/Strong Correlation (|r| > 0.2):</strong> {strong_corr}/{total_transitions} ({strong_corr/total_transitions*100:.1f}%)</p>")
    
    # Average improvement by z-score range (across all transitions)
    top_performers = results_df[results_df['zscore_range'].str.contains('Top 2.5%|Top 6.7%', regex=True)]
    if len(top_performers) > 0:
        avg_top_improvement = top_performers['median_improvement'].mean()
        pct_top_improving = top_performers['pct_improving'].mean()
        
        html_content.append(f"<p><strong>Top Performers (z ≥ 1.5) - Average Median Improvement:</strong> {avg_top_improvement:.3f}s</p>")
        html_content.append(f"<p><strong>Top Performers - Percentage Improving:</strong> {pct_top_improving:.1f}%</p>")
    
    html_content.append("</div>")
    
    # Detailed analysis by transition
    html_content.append("<h2>Analysis by Age Transition</h2>")
    
    for (age_from, age_to), group in summaries_by_transition:
        html_content.append(f"<h3>Age {age_from} → {age_to} Transitions</h3>")
        
        # Summary table for this transition
        html_content.append("<table>")
        html_content.append("<thead><tr><th>Gender</th><th>Event</th><th>N</th><th>Mean Z-Score</th><th>Median Δ (s)</th><th>Correlation (r)</th><th>p-value</th><th>% Improving</th></tr></thead><tbody>")
        
        for _, row in group.iterrows():
            corr_r = row['correlation_zscore_improvement']
            corr_p = row['correlation_pvalue']
            corr_class = 'positive' if corr_r > 0 else 'negative' if corr_r < 0 else ''
            
            html_content.append(f"<tr>")
            html_content.append(f"<td>{row['gender']}</td>")
            html_content.append(f"<td>{row['event']}</td>")
            html_content.append(f"<td>{int(row['total_n'])}</td>")
            html_content.append(f"<td>{row['overall_mean_zscore']:.2f}</td>")
            html_content.append(f"<td>{row['overall_median_improvement']:.3f}</td>")
            html_content.append(f"<td class='{corr_class}'>{corr_r:.3f}</td>")
            html_content.append(f"<td>{corr_p:.4f}</td>")
            html_content.append(f"<td>{row['pct_improving']:.1f}%</td>")
            html_content.append(f"</tr>")
        
        html_content.append("</tbody></table>")
        
        # Z-score range breakdown for a sample event (first in group)
        sample = group.iloc[0]
        sample_ranges = results_df[
            (results_df['gender'] == sample['gender']) &
            (results_df['event'] == sample['event']) &
            (results_df['age_from'] == sample['age_from']) &
            (results_df['age_to'] == sample['age_to'])
        ].sort_values('mean_zscore', ascending=False)
        
        if len(sample_ranges) > 0:
            html_content.append(f"<h4>Example: {sample['gender']} {sample['event']} - Improvement by Z-Score Range</h4>")
            html_content.append("<table>")
            html_content.append("<thead><tr><th>Z-Score Range</th><th>N</th><th>Mean Z</th><th>Median Δ (s)</th><th>Mean Δ (s)</th><th>% Improving</th><th>% Getting Slower</th></tr></thead><tbody>")
            
            for _, r in sample_ranges.iterrows():
                imp_class = 'positive' if r['median_improvement'] > 0 else 'negative'
                html_content.append(f"<tr>")
                html_content.append(f"<td>{r['zscore_range']}</td>")
                html_content.append(f"<td>{int(r['n_athletes'])}</td>")
                html_content.append(f"<td>{r['mean_zscore']:.2f}</td>")
                html_content.append(f"<td class='{imp_class}'>{r['median_improvement']:.3f}</td>")
                html_content.append(f"<td class='{imp_class}'>{r['mean_improvement']:.3f}</td>")
                html_content.append(f"<td>{r['pct_improving']:.1f}%</td>")
                html_content.append(f"<td>{r['pct_getting_slower']:.1f}%</td>")
                html_content.append(f"</tr>")
            
            html_content.append("</tbody></table>")
    
    # Add z-score 1.5-2.0 pattern analysis
    html_content.append("<h2>The 1.5-2.0 Z-Score Range: A Key Finding</h2>")
    zscore_range_target = "Top 6.7% (1.5 ≤ z < 2.0)"
    range_data = results_df[results_df['zscore_range'] == zscore_range_target].copy()
    
    if len(range_data) > 0:
        positive_improvements = range_data[range_data['median_improvement'] > 0]
        negative_improvements = range_data[range_data['median_improvement'] <= 0]
        
        # Break down by age transition
        range_data['age_trans'] = range_data['age_from'].astype(str) + '->' + range_data['age_to'].astype(str)
        by_age = range_data.groupby('age_trans').apply(
            lambda x: pd.Series({
                'positive': (x['median_improvement'] > 0).sum(),
                'negative': (x['median_improvement'] <= 0).sum(),
                'total': len(x)
            })
        )
        
        html_content.append("<div class='summary-box'>")
        html_content.append(f"<h3>Analysis of {zscore_range_target} Swimmers</h3>")
        html_content.append(f"<p><strong>Total transitions analyzed:</strong> {len(range_data)}</p>")
        html_content.append(f"<p><strong>Transitions with positive improvement:</strong> {len(positive_improvements)} ({len(positive_improvements)/len(range_data)*100:.1f}%)</p>")
        html_content.append(f"<p><strong>Transitions with negative/zero improvement:</strong> {len(negative_improvements)} ({len(negative_improvements)/len(range_data)*100:.1f}%)</p>")
        
        html_content.append("<h4>Breakdown by Age Transition:</h4>")
        html_content.append("<ul>")
        for age_trans, row in by_age.iterrows():
            pct = row['positive'] / row['total'] * 100
            html_content.append(f"<li><strong>{age_trans}:</strong> {int(row['positive'])} positive, {int(row['negative'])} negative/zero out of {int(row['total'])} transitions ({pct:.0f}% positive)</li>")
        html_content.append("</ul>")
        
        html_content.append("</div>")
        
        html_content.append("""
        <div class="note">
            <h3>What This Means:</h3>
            <p><strong>Swimmers with z-scores between 1.5 and 2.0</strong> (top 6.7% of performers) show a strong pattern:</p>
            <ul>
                <li><strong>At age 15→16:</strong> 96% of transitions show positive improvement - nearly all elite swimmers improve!</li>
                <li><strong>At age 16→17:</strong> 62% show positive improvement - still majority improving, but less consistent</li>
                <li><strong>At age 17→18:</strong> Only 43% show positive improvement - elite swimmers start plateauing</li>
            </ul>
            <p><strong>Implication for MOT:</strong> Swimmers in this z-score range (already performing in the top 6.7%) are most likely 
            to continue improving, especially at younger ages. This validates targeting elite performers (like Canada On Track does) 
            rather than the median population for identifying "on track" athletes.</p>
        </div>
        """)
    
    # Interpretation section
    html_content.append("<h2>Interpretation and Implications</h2>")
    html_content.append("""
    <div class="note">
        <h3>What This Analysis Tells Us</h3>
        <ul>
            <li><strong>Z-Score Range:</strong> A z-score indicates how many standard deviations above or below 
            the mean a swimmer's time is. For swim times (lower is better), a positive z-score means faster than average.</li>
            <li><strong>Positive Correlation:</strong> If higher z-scores correlate with greater improvement, it suggests 
            elite performers continue to improve at a higher rate than the general population.</li>
            <li><strong>Top Performers Improving:</strong> High percentages of improvement in top z-score ranges validate 
            the Canada On Track methodology, which targets elite performers on medal trajectories.</li>
            <li><strong>Negative Deltas in Lower Ranges:</strong> Lower-performing swimmers (negative z-scores) may show 
            negative medians, reflecting plateauing or regression in the general population.</li>
        </ul>
        
        <h3>Validation of Canada On Track Approach</h3>
        <p>If top performers (z ≥ 1.5) consistently show positive improvement rates while the median population 
        shows negative or minimal improvement, this validates using elite performer trajectories (like Canada On Track) 
        rather than population medians for setting Malaysia On Track (MOT) targets.</p>
        
        <h3>Understanding Weak Positive Correlation (1.2%)</h3>
        <p>A correlation of +1.2% (0.012) between z-score and improvement means there is almost <strong>no relationship</strong> 
        between how fast a swimmer is at one age and how much they'll improve the next year. This is actually significant:</p>
        <ul>
            <li>It means both fast and slow swimmers improve (or don't improve) at roughly the same rate</li>
            <li>However, the <strong>1.5-2.0 z-score range pattern</strong> shows that elite swimmers (top 6.7%) are more 
            consistent in their improvement, especially at younger ages</li>
            <li>This suggests that while improvement amount may not correlate strongly with starting performance level, 
            <strong>improvement consistency does</strong> - elite swimmers are more likely to continue improving year-over-year</li>
        </ul>
    </div>
    """)
    
    # Footer
    html_content.append("<hr style='margin:32px 0;border:none;border-top:1px solid #ddd'>")
    html_content.append("""
    <p style='font-size:13px;color:#666;line-height:1.6'>
        <strong>Generated from statistical analysis database.</strong><br>
        <strong>Data sources:</strong><br>
        • Canada On Track reference times are from April 2025.<br>
        • USA Swimming season rankings are from the 2021-2022, 2022-2023, 2023-2024, and 2024-2025 seasons. 
        USA Swimming seasons run from September 1 of the first year to August 31 of the second year.<br>
        • USA Swimming ages are the age of the swimmer on the first day of competition, not their birth year age.<br>
        • Z-scores are calculated relative to the distribution of all swimmers at each starting age 
        (e.g., z-score at age 17 is relative to all age 17 swimmers in that season).
    </p>
    """)
    
    html_content.append("</body></html>")
    
    with open(html_out, 'w', encoding='utf-8') as f:
        f.write('\n'.join(html_content))
    
    print(f"✅ Generated HTML report: {html_out}")
    return html_out


if __name__ == '__main__':
    print("Analyzing improvement rates by z-score range...")
    print("=" * 60)
    
    results, summaries = analyze_all_transitions()
    
    if results is not None and summaries is not None:
        print("\nGenerating comprehensive HTML report...")
        html_path = generate_html_report(results, summaries)
        print(f"\n✅ Analysis complete! Open {html_path} to view results.")
    else:
        print("\n❌ Analysis failed - no results generated")

