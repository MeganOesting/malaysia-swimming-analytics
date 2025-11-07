#!/usr/bin/env python3
"""
Analyze Gender Patterns in Negative Improvements
Identifies if negative improvements are more common in male or female events
"""

import os
import pandas as pd

script_dir = os.path.dirname(os.path.abspath(__file__))
if 'statistical_analysis' in script_dir.lower():
    CSV_PATH = os.path.join(script_dir, '..', 'reports', 'Negative_Improvement_Patterns.csv')
else:
    CSV_PATH = os.path.join('reports', 'Negative_Improvement_Patterns.csv')

CSV_PATH = os.path.abspath(CSV_PATH)


def analyze_gender_patterns():
    """Analyze gender patterns in negative improvements."""
    if not os.path.exists(CSV_PATH):
        print(f"CSV not found: {CSV_PATH}")
        return
    
    df = pd.read_csv(CSV_PATH, encoding='utf-8')
    
    # Overall gender breakdown
    gender_counts = df['gender'].value_counts()
    total = len(df)
    
    print(f"\n=== GENDER PATTERNS IN NEGATIVE IMPROVEMENTS ===\n")
    print(f"Total negative improvements: {total}")
    print(f"\nBy Gender:")
    for gender in ['F', 'M']:
        count = gender_counts.get(gender, 0)
        pct = (count / total * 100) if total > 0 else 0
        print(f"  {gender}: {count} ({pct:.1f}%)")
    
    # By transition and gender
    print(f"\n=== BY TRANSITION AND GENDER ===\n")
    for trans in sorted(df['transition'].unique()):
        trans_df = df[df['transition'] == trans]
        print(f"{trans}:")
        for gender in ['F', 'M']:
            gender_df = trans_df[trans_df['gender'] == gender]
            count = len(gender_df)
            pct_trans = (count / len(trans_df) * 100) if len(trans_df) > 0 else 0
            avg_median = gender_df['median_improvement'].mean() if len(gender_df) > 0 else 0
            print(f"  {gender}: {count} ({pct_trans:.1f}% of {trans}), avg median: {avg_median:.3f}s")
    
    # By z-score range and gender
    print(f"\n=== BY Z-SCORE RANGE AND GENDER ===\n")
    for zrange in sorted(df['zscore_range'].unique()):
        range_df = df[df['zscore_range'] == zrange]
        print(f"{zrange}:")
        for gender in ['F', 'M']:
            gender_df = range_df[range_df['gender'] == zrange]
            # Fix: should be filtering by gender, not zscore_range
            gender_df = range_df[range_df['gender'] == gender]
            count = len(gender_df)
            pct_range = (count / len(range_df) * 100) if len(range_df) > 0 else 0
            avg_median = gender_df['median_improvement'].mean() if len(gender_df) > 0 else 0
            print(f"  {gender}: {count} ({pct_range:.1f}% of range), avg median: {avg_median:.3f}s")
    
    # Events with most negatives by gender
    print(f"\n=== TOP EVENTS WITH NEGATIVE IMPROVEMENTS (BY GENDER) ===\n")
    for gender in ['F', 'M']:
        gender_df = df[df['gender'] == gender]
        event_counts = gender_df.groupby('event').size().sort_values(ascending=False)
        print(f"{gender} Events:")
        for event, count in event_counts.head(10).items():
            avg_median = gender_df[gender_df['event'] == event]['median_improvement'].mean()
            print(f"  {event}: {count} negative improvements, avg median: {avg_median:.3f}s")
    
    # Check if any events have ONLY female or ONLY male negative improvements
    print(f"\n=== EVENTS WITH GENDER-SPECIFIC PATTERNS ===\n")
    all_events = df['event'].unique()
    
    female_only = []
    male_only = []
    both_genders = []
    
    for event in sorted(all_events):
        event_df = df[df['event'] == event]
        genders = event_df['gender'].unique()
        
        if 'F' in genders and 'M' not in genders:
            female_only.append((event, len(event_df)))
        elif 'M' in genders and 'F' not in genders:
            male_only.append((event, len(event_df)))
        else:
            both_genders.append((event, len(event_df), len(event_df[event_df['gender'] == 'F']), len(event_df[event_df['gender'] == 'M'])))
    
    if female_only:
        print(f"Events with ONLY Female negative improvements ({len(female_only)}):")
        for event, count in female_only:
            print(f"  {event}: {count} occurrences")
    
    if male_only:
        print(f"\nEvents with ONLY Male negative improvements ({len(male_only)}):")
        for event, count in male_only:
            print(f"  {event}: {count} occurrences")
    
    print(f"\nEvents with negative improvements in BOTH genders ({len(both_genders)}):")
    for event, total, f_count, m_count in sorted(both_genders, key=lambda x: x[1], reverse=True)[:15]:
        print(f"  {event}: {total} total (F: {f_count}, M: {m_count})")
    
    # Severity by gender
    print(f"\n=== SEVERITY BY GENDER ===\n")
    for gender in ['F', 'M']:
        gender_df = df[df['gender'] == gender]
        print(f"{gender}:")
        print(f"  Count: {len(gender_df)}")
        print(f"  Average median improvement: {gender_df['median_improvement'].mean():.3f}s")
        print(f"  Most severe: {gender_df['median_improvement'].min():.3f}s")
        print(f"  Least severe: {gender_df['median_improvement'].max():.3f}s")
        print(f"  % improving: {gender_df['pct_improving'].mean():.1f}%")
        print(f"  % getting slower: {gender_df['pct_getting_slower'].mean():.1f}%")
    
    return df


if __name__ == '__main__':
    analyze_gender_patterns()














