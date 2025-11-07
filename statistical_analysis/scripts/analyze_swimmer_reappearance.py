#!/usr/bin/env python3
"""
Analyze Swimmer Reappearance Patterns
Tracks swimmers who drop out of top 500 and whether they reappear later
"""

import os
import pandas as pd
from collections import defaultdict

script_dir = os.path.dirname(os.path.abspath(__file__))
if 'statistical_analysis' in script_dir.lower():
    PERIOD_DATA_BASE = os.path.join(script_dir, '..', 'data', 'Period Data')
    OUTPUT_CSV = os.path.join(script_dir, '..', 'reports', 'Swimmer_Reappearance_Analysis.csv')
else:
    PERIOD_DATA_BASE = os.path.join('data', 'Period Data')
    OUTPUT_CSV = 'reports/Swimmer_Reappearance_Analysis.csv'

PERIOD_DATA_BASE = os.path.abspath(PERIOD_DATA_BASE)
OUTPUT_CSV = os.path.abspath(OUTPUT_CSV)


def load_swimmers_from_file(file_path):
    """Load set of swimmer names from a period data file using same logic as improvement analysis."""
    if not os.path.exists(file_path):
        return set()
    
    swimmers = set()
    try:
        import pandas as pd
        # Use pandas to read tab-separated file (same as improvement analysis)
        df = pd.read_csv(
            file_path,
            sep='\t',
            engine='python',
            on_bad_lines='skip'
        )
        
        if 'Name' in df.columns:
            # Match the exact logic from improvement analysis: case-insensitive, stripped
            df['name_lower'] = df['Name'].astype(str).str.lower().str.strip()
            swimmers = set(df['name_lower'].unique())
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    
    return swimmers


def find_period_data_file(gender, event, age, period):
    """Find the data file for a specific period (using same logic as improvement analysis)."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if 'statistical_analysis' in script_dir.lower():
        filepath = os.path.join(PERIOD_DATA_BASE, period, f"{gender} {event} {period}", f"{gender} {event} {age} {period}.txt")
    else:
        filepath = os.path.join(PERIOD_DATA_BASE, period, f"{gender} {event} {period}", f"{gender} {event} {age} {period}.txt")
    
    if os.path.exists(filepath):
        return filepath
    return None


def analyze_reappearance_patterns():
    """Analyze reappearance patterns across all events using same period logic as improvement analysis."""
    if not os.path.exists(PERIOD_DATA_BASE):
        print(f"Period data directory not found: {PERIOD_DATA_BASE}")
        return
    
    # Use the same period combinations as improvement analysis
    # 15->16: age 15 in 2021-2022, age 16 in 2022-2023
    # 16->17: age 16 in 2022-2023, age 17 in 2023-2024  
    # 17->18: age 17 in 2023-2024, age 18 in 2024-2025
    
    period_15 = "9.1.21-8.31.22"  # Age 15 period
    period_16 = "9.1.22-8.31.23"  # Age 16 period
    period_17 = "9.1.23-8.31.24"  # Age 17 period
    period_18 = "9.1.24-8.31.25"  # Age 18 period
    
    events = [
        '50 Free', '100 Free', '200 Free', '400 Free', '800 Free', '1500 Free',
        '100 Back', '200 Back',
        '100 Breast', '200 Breast',
        '100 Fly', '200 Fly',
        '200 IM', '400 IM'
    ]
    
    results = []
    
    for gender in ['F', 'M']:
        for event in events:
            print(f"Analyzing {gender} {event}...")
            
            # Load swimmers for each age from correct periods
            age_15_file = find_period_data_file(gender, event, 15, period_15)
            age_16_file = find_period_data_file(gender, event, 16, period_16)
            age_17_file = find_period_data_file(gender, event, 17, period_17)
            age_18_file = find_period_data_file(gender, event, 18, period_18)
            
            swimmers_15 = load_swimmers_from_file(age_15_file) if age_15_file else set()
            swimmers_16 = load_swimmers_from_file(age_16_file) if age_16_file else set()
            swimmers_17 = load_swimmers_from_file(age_17_file) if age_17_file else set()
            swimmers_18 = load_swimmers_from_file(age_18_file) if age_18_file else set()
            
            # Pattern 1: In 15, dropped out at 16, reappeared at 17
            dropped_15_to_16 = swimmers_15 - swimmers_16
            reappeared_at_17 = dropped_15_to_16 & swimmers_17
            reappeared_at_18 = dropped_15_to_16 & swimmers_18
            
            # Pattern 2: In 15 and 16, dropped out at 17, reappeared at 18
            in_15_and_16 = swimmers_15 & swimmers_16
            dropped_16_to_17 = in_15_and_16 - swimmers_17
            reappeared_at_18_from_16 = dropped_16_to_17 & swimmers_18
            
            # Pattern 3: In 15, not in 16, but back at 17 and/or 18
            reappeared_at_17_or_18 = dropped_15_to_16 & (swimmers_17 | swimmers_18)
            
            # Pattern 4: In 15 and 16, not in 17, but back at 18
            reappeared_at_18_from_17 = dropped_16_to_17 & swimmers_18
            
            results.append({
                'gender': gender,
                'event': event,
                'in_top500_age15': len(swimmers_15),
                'in_top500_age16': len(swimmers_16),
                'in_top500_age17': len(swimmers_17),
                'in_top500_age18': len(swimmers_18),
                'dropped_15_to_16': len(dropped_15_to_16),
                'reappeared_at_17_after_dropout': len(reappeared_at_17),
                'reappeared_at_18_after_dropout_15_16': len(reappeared_at_18),
                'reappeared_at_17_or_18_after_dropout': len(reappeared_at_17_or_18),
                'pct_reappeared_17_or_18': (len(reappeared_at_17_or_18) / len(dropped_15_to_16) * 100) if dropped_15_to_16 else 0,
                'in_15_and_16': len(in_15_and_16),
                'dropped_16_to_17': len(dropped_16_to_17),
                'reappeared_at_18_after_dropout_16_17': len(reappeared_at_18_from_17),
                'pct_reappeared_18_after_dropout_16_17': (len(reappeared_at_18_from_17) / len(dropped_16_to_17) * 100) if dropped_16_to_17 else 0,
            })
    
    df = pd.DataFrame(results)
    df.to_csv(OUTPUT_CSV, index=False, encoding='utf-8')
    print(f"\n✅ Analysis complete! Results saved to: {OUTPUT_CSV}")
    
    # Print summary statistics
    print("\n=== SUMMARY STATISTICS ===")
    print(f"\nAverage % of swimmers who drop out 15→16 and reappear at 17 or 18: {df['pct_reappeared_17_or_18'].mean():.1f}%")
    print(f"Average % of swimmers who drop out 16→17 and reappear at 18: {df['pct_reappeared_18_after_dropout_16_17'].mean():.1f}%")
    print(f"\nTotal events analyzed: {len(df)}")
    
    return df


if __name__ == '__main__':
    analyze_reappearance_patterns()

