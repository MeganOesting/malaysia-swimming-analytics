#!/usr/bin/env python3
"""
Analyze Negative Median Improvements Across All Z-Score Ranges
Identifies patterns in which z-score ranges show negative improvements across events
"""

import os
import pandas as pd

script_dir = os.path.dirname(os.path.abspath(__file__))
if 'statistical_analysis' in script_dir.lower():
    ZSCORE_CSV = os.path.join(script_dir, '..', 'reports', 'Improvement_by_ZScore_Range.csv')
    OUTPUT_CSV = os.path.join(script_dir, '..', 'reports', 'Negative_Improvement_Patterns.csv')
else:
    ZSCORE_CSV = os.path.join('reports', 'Improvement_by_ZScore_Range.csv')
    OUTPUT_CSV = os.path.join('reports', 'Negative_Improvement_Patterns.csv')

ZSCORE_CSV = os.path.abspath(ZSCORE_CSV)
OUTPUT_CSV = os.path.abspath(OUTPUT_CSV)


def analyze_negative_patterns():
    """Analyze all negative improvements across z-score ranges."""
    if not os.path.exists(ZSCORE_CSV):
        print(f"Z-score CSV not found: {ZSCORE_CSV}")
        return
    
    df = pd.read_csv(ZSCORE_CSV, encoding='utf-8')
    
    # Filter for negative or near-zero improvements (<= 0.02s)
    negative_df = df[df['median_improvement'] <= 0.02].copy()
    
    # Add transition column for easier analysis
    negative_df['transition'] = negative_df['age_from'].astype(str) + '→' + negative_df['age_to'].astype(str)
    negative_df['gender_event'] = negative_df['gender'] + ' ' + negative_df['event']
    
    # Summary statistics by z-score range
    range_summary = []
    for zrange in negative_df['zscore_range'].unique():
        range_data = negative_df[negative_df['zscore_range'] == zrange]
        range_summary.append({
            'zscore_range': zrange,
            'count_negative': len(range_data),
            'avg_median_improvement': range_data['median_improvement'].mean(),
            'min_median_improvement': range_data['median_improvement'].min(),
            'max_median_improvement': range_data['median_improvement'].max(),
            'avg_pct_improving': range_data['pct_improving'].mean(),
            'avg_pct_getting_slower': range_data['pct_getting_slower'].mean()
        })
    
    range_summary_df = pd.DataFrame(range_summary).sort_values('count_negative', ascending=False)
    
    # Summary by transition
    transition_summary = []
    for trans in negative_df['transition'].unique():
        trans_data = negative_df[negative_df['transition'] == trans]
        transition_summary.append({
            'transition': trans,
            'count_negative': len(trans_data),
            'ranges_affected': ', '.join(sorted(trans_data['zscore_range'].unique())),
            'num_ranges_affected': len(trans_data['zscore_range'].unique())
        })
    
    transition_summary_df = pd.DataFrame(transition_summary).sort_values('transition')
    
    # Summary by event (across all transitions and ranges)
    event_summary = []
    for gender_event in negative_df['gender_event'].unique():
        event_data = negative_df[negative_df['gender_event'] == gender_event]
        event_summary.append({
            'gender_event': gender_event,
            'count_negative': len(event_data),
            'transitions_affected': ', '.join(sorted(event_data['transition'].unique())),
            'ranges_affected': ', '.join(sorted(event_data['zscore_range'].unique())),
            'num_transitions': len(event_data['transition'].unique()),
            'num_ranges': len(event_data['zscore_range'].unique())
        })
    
    event_summary_df = pd.DataFrame(event_summary).sort_values('count_negative', ascending=False)
    
    # Detailed results with all negative improvements
    negative_df_sorted = negative_df.sort_values(['gender', 'event', 'transition', 'zscore_range'])
    
    # Save to CSV with multiple sheets equivalent (we'll use separate files)
    negative_df_sorted.to_csv(OUTPUT_CSV, index=False, encoding='utf-8')
    
    # Save summary files
    range_summary_path = OUTPUT_CSV.replace('.csv', '_By_ZScore_Range.csv')
    transition_summary_path = OUTPUT_CSV.replace('.csv', '_By_Transition.csv')
    event_summary_path = OUTPUT_CSV.replace('.csv', '_By_Event.csv')
    
    range_summary_df.to_csv(range_summary_path, index=False, encoding='utf-8')
    transition_summary_df.to_csv(transition_summary_path, index=False, encoding='utf-8')
    event_summary_df.to_csv(event_summary_path, index=False, encoding='utf-8')
    
    print(f"\n✅ Negative Improvement Pattern Analysis complete!")
    print(f"\nDetailed results: {OUTPUT_CSV}")
    print(f"Summary by Z-Score Range: {range_summary_path}")
    print(f"Summary by Transition: {transition_summary_path}")
    print(f"Summary by Event: {event_summary_path}")
    
    print(f"\n=== KEY FINDINGS ===")
    print(f"\nTotal negative/zero improvements found: {len(negative_df_sorted)}")
    
    print(f"\n1. NEGATIVE IMPROVEMENTS BY Z-SCORE RANGE (most affected):")
    for _, row in range_summary_df.head(10).iterrows():
        print(f"  {row['zscore_range']}:")
        print(f"    - {row['count_negative']} occurrences")
        print(f"    - Average median improvement: {row['avg_median_improvement']:.3f}s")
        print(f"    - Avg % improving: {row['avg_pct_improving']:.1f}%")
        print(f"    - Avg % getting slower: {row['avg_pct_getting_slower']:.1f}%")
    
    print(f"\n2. TRANSITIONS MOST AFFECTED:")
    for _, row in transition_summary_df.iterrows():
        print(f"  {row['transition']}: {row['count_negative']} negative improvements across {row['num_ranges_affected']} z-score range(s)")
        print(f"    Ranges: {row['ranges_affected']}")
    
    print(f"\n3. EVENTS MOST AFFECTED:")
    for _, row in event_summary_df.head(15).iterrows():
        print(f"  {row['gender_event']}:")
        print(f"    - {row['count_negative']} total negative improvements")
        print(f"    - Affects {row['num_transitions']} transition(s): {row['transitions_affected']}")
        print(f"    - Across {row['num_ranges']} z-score range(s)")
    
    # Answer the key question: Are most in 1.5-2.0 range?
    zscore_1520_count = len(negative_df[negative_df['zscore_range'] == 'Top 6.7% (1.5 ≤ z < 2.0)'])
    total_count = len(negative_df)
    pct_1520 = (zscore_1520_count / total_count * 100) if total_count > 0 else 0
    
    print(f"\n4. IS THE MAJORITY IN THE 1.5-2.0 RANGE?")
    print(f"  {zscore_1520_count} out of {total_count} negative improvements are in the 1.5-2.0 z-score range")
    print(f"  That's {pct_1520:.1f}% of all negative improvements")
    
    # What other ranges show negative?
    other_ranges = negative_df[negative_df['zscore_range'] != 'Top 6.7% (1.5 ≤ z < 2.0)']
    print(f"\n5. OTHER Z-SCORE RANGES WITH NEGATIVE IMPROVEMENTS:")
    for zrange in sorted(other_ranges['zscore_range'].unique()):
        range_data = other_ranges[other_ranges['zscore_range'] == zrange]
        print(f"  {zrange}: {len(range_data)} occurrences")
        print(f"    - Avg median: {range_data['median_improvement'].mean():.3f}s")
        print(f"    - Events affected: {', '.join(sorted(range_data['gender_event'].unique())[:5])}" + 
              (f" (and {len(range_data['gender_event'].unique())-5} more)" if len(range_data['gender_event'].unique()) > 5 else ""))
    
    return negative_df_sorted, range_summary_df, transition_summary_df, event_summary_df


if __name__ == '__main__':
    analyze_negative_patterns()




