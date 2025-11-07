#!/usr/bin/env python3
"""
Analyze if 1.5-2.0 z-score range consistently shows improvement across all events
"""

import pandas as pd
import os

def analyze_zscore_pattern():
    """Check if 1.5-2.0 z-score range consistently improves"""
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if 'statistical_analysis' in script_dir.lower():
        csv_path = os.path.join(script_dir, '..', 'reports', 'Improvement_by_ZScore_Range.csv')
    else:
        csv_path = 'reports/Improvement_by_ZScore_Range.csv'
    
    df = pd.read_csv(csv_path)
    
    # Filter to 1.5-2.0 range
    zscore_range = "Top 6.7% (1.5 ≤ z < 2.0)"
    df_15to20 = df[df['zscore_range'] == zscore_range].copy()
    
    # Count positive vs negative median improvements
    positive_improvements = df_15to20[df_15to20['median_improvement'] > 0]
    negative_improvements = df_15to20[df_15to20['median_improvement'] <= 0]
    
    print(f"Analysis of {zscore_range} across all transitions:")
    print(f"=" * 60)
    print(f"Total transitions with this z-score range: {len(df_15to20)}")
    print(f"Positive median improvement: {len(positive_improvements)} ({len(positive_improvements)/len(df_15to20)*100:.1f}%)")
    print(f"Negative/zero median improvement: {len(negative_improvements)} ({len(negative_improvements)/len(df_15to20)*100:.1f}%)")
    print()
    
    print("Transitions with POSITIVE improvement (> 0):")
    print("-" * 60)
    for _, row in positive_improvements.sort_values('median_improvement', ascending=False).iterrows():
        print(f"{row['gender']} {row['event']} {row['age_from']}->{row['age_to']}: "
              f"Median Δ = {row['median_improvement']:.3f}s (n={row['n_athletes']}, "
              f"{row['pct_improving']:.1f}% improved)")
    print()
    
    print("Transitions with NEGATIVE improvement (≤ 0):")
    print("-" * 60)
    for _, row in negative_improvements.sort_values('median_improvement').iterrows():
        print(f"{row['gender']} {row['event']} {row['age_from']}->{row['age_to']}: "
              f"Median Δ = {row['median_improvement']:.3f}s (n={row['n_athletes']}, "
              f"{row['pct_improving']:.1f}% improved)")
    print()
    
    # Check if pattern varies by age transition
    print("Breakdown by age transition:")
    print("-" * 60)
    for age_trans in ['15->16', '16->17', '17->18']:
        subset = df_15to20[
            (df_15to20['age_from'].astype(str) + '->' + df_15to20['age_to'].astype(str)) == age_trans
        ]
        pos = len(subset[subset['median_improvement'] > 0])
        neg = len(subset[subset['median_improvement'] <= 0])
        print(f"{age_trans}: {pos} positive, {neg} negative/zero (total: {len(subset)})")
    
    return df_15to20

if __name__ == "__main__":
    analyze_zscore_pattern()




