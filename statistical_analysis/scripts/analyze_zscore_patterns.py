#!/usr/bin/env python3
"""
Analyze Z-Score Range Patterns Across All Events
Finds which events/transitions show negative improvements in specific z-score ranges
"""

import os
import pandas as pd

script_dir = os.path.dirname(os.path.abspath(__file__))
if 'statistical_analysis' in script_dir.lower():
    ZSCORE_CSV = os.path.join(script_dir, '..', 'reports', 'Improvement_by_ZScore_Range.csv')
    OUTPUT_CSV = os.path.join(script_dir, '..', 'reports', 'ZScore_Pattern_Analysis.csv')
else:
    ZSCORE_CSV = os.path.join('reports', 'Improvement_by_ZScore_Range.csv')
    OUTPUT_CSV = os.path.join('reports', 'ZScore_Pattern_Analysis.csv')

ZSCORE_CSV = os.path.abspath(ZSCORE_CSV)
OUTPUT_CSV = os.path.abspath(OUTPUT_CSV)


def analyze_zscore_patterns():
    """Analyze which z-score ranges show negative improvements."""
    if not os.path.exists(ZSCORE_CSV):
        print(f"Z-score CSV not found: {ZSCORE_CSV}")
        return
    
    df = pd.read_csv(ZSCORE_CSV, encoding='utf-8')
    
    # Focus on the 1.5-2.0 z-score range (Top 6.7%)
    zscore_15_20 = df[df['zscore_range'] == 'Top 6.7% (1.5 ≤ z < 2.0)'].copy()
    
    # Find where median improvement is negative or near-zero
    negative_improvements = zscore_15_20[zscore_15_20['median_improvement'] <= 0.02].copy()
    
    # Sort by median improvement (most negative first)
    negative_improvements = negative_improvements.sort_values('median_improvement')
    
    # Compare to other z-score ranges for same event/transition
    results = []
    
    for _, row in negative_improvements.iterrows():
        gender = row['gender']
        event = row['event']
        age_from = row['age_from']
        age_to = row['age_to']
        median_imp = row['median_improvement']
        
        # Get all z-score ranges for this event/transition
        event_trans = df[
            (df['gender'] == gender) &
            (df['event'] == event) &
            (df['age_from'] == age_from) &
            (df['age_to'] == age_to)
        ]
        
        # Count how many other ranges have positive improvements
        positive_ranges = event_trans[event_trans['median_improvement'] > 0]
        all_ranges = len(event_trans) - 1  # Exclude the 1.5-2.0 range itself
        
        # Get comparison to other ranges
        other_medians = event_trans[event_trans['zscore_range'] != 'Top 6.7% (1.5 ≤ z < 2.0)']['median_improvement'].tolist()
        avg_other_median = sum(other_medians) / len(other_medians) if other_medians else 0
        
        results.append({
            'gender': gender,
            'event': event,
            'age_from': age_from,
            'age_to': age_to,
            'zscore_range': '1.5-2.0',
            'median_improvement': median_imp,
            'n_athletes': row['n_athletes'],
            'pct_improving': row['pct_improving'],
            'pct_getting_slower': row['pct_getting_slower'],
            'num_other_ranges': all_ranges,
            'num_other_ranges_positive': len(positive_ranges),
            'avg_other_ranges_median': avg_other_median,
            'difference_from_avg': median_imp - avg_other_median
        })
    
    result_df = pd.DataFrame(results)
    result_df.to_csv(OUTPUT_CSV, index=False, encoding='utf-8')
    
    print(f"\n✅ Z-Score Pattern Analysis complete!")
    print(f"Results saved to: {OUTPUT_CSV}")
    print(f"\n=== SUMMARY ===")
    print(f"Events/transitions with negative/zero improvement in 1.5-2.0 z-score range: {len(result_df)}")
    
    if len(result_df) > 0:
        print(f"\nTop 10 most negative (worse performers in 1.5-2.0 range):")
        top_negative = result_df.nsmallest(10, 'median_improvement')
        for _, row in top_negative.iterrows():
            print(f"  {row['gender']} {row['event']} {row['age_from']}→{row['age_to']}: "
                  f"median={row['median_improvement']:.3f}s, "
                  f"avg_other_ranges={row['avg_other_ranges_median']:.3f}s, "
                  f"difference={row['difference_from_avg']:.3f}s")
    
    return result_df


if __name__ == '__main__':
    analyze_zscore_patterns()














