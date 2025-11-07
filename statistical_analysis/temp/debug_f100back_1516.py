# -*- coding: utf-8 -*-
import os
import pandas as pd
import sys
sys.path.insert(0, os.path.dirname(__file__))
from run_mot_delta_analysis import load_period_data, parse_swim_time

def main():
    gender = 'F'
    event = '100 Back'
    age_from = '15'
    age_to = '16'
    period_from = '9.1.21-8.31.22'
    period_to = '9.1.22-8.31.23'
    
    print(f"Debugging {gender} {event} {age_from}→{age_to}")
    print("=" * 60)
    
    df_from = load_period_data(gender, event, age_from, period_from)
    df_to = load_period_data(gender, event, age_to, period_to)
    
    if df_from is None:
        print(f"ERROR: Could not load {age_from} data")
        return
    if df_to is None:
        print(f"ERROR: Could not load {age_to} data")
        return
    
    print(f"\n{age_from} period: {len(df_from)} total rows")
    print(f"{age_to} period: {len(df_to)} total rows")
    
    # Parse times
    df_from['time_seconds'] = df_from['Swim Time'].apply(parse_swim_time)
    df_to['time_seconds'] = df_to['Swim Time'].apply(parse_swim_time)
    
    valid_from = df_from.dropna(subset=['time_seconds'])
    valid_to = df_to.dropna(subset=['time_seconds'])
    
    print(f"\n{age_from} with valid times: {len(valid_from)}")
    print(f"{age_to} with valid times: {len(valid_to)}")
    
    # Match names
    df_from['name_lower'] = df_from['Name'].astype(str).str.lower().str.strip()
    df_to['name_lower'] = df_to['Name'].astype(str).str.lower().str.strip()
    
    common_names = set(df_from['name_lower']) & set(df_to['name_lower'])
    print(f"\nCommon athletes found: {len(common_names)}")
    
    if len(common_names) < 10:
        print(f"\nPROBLEM: Only {len(common_names)} matched athletes (need >= 10)")
        print("\nFirst 20 names from each period:")
        print(f"\n{age_from} period names:")
        for i, name in enumerate(list(df_from['name_lower'].unique())[:20]):
            print(f"  {i+1}. {name}")
        print(f"\n{age_to} period names:")
        for i, name in enumerate(list(df_to['name_lower'].unique())[:20]):
            print(f"  {i+1}. {name}")
    else:
        print(f"\n✓ Sufficient matches: {len(common_names)} athletes")
        # Calculate improvements
        matched_data = []
        for name in common_names:
            from_row = df_from[df_from['name_lower'] == name].iloc[0]
            to_row = df_to[df_to['name_lower'] == name].iloc[0]
            improvement = from_row['time_seconds'] - to_row['time_seconds']
            matched_data.append(improvement)
        
        print(f"Improvements calculated: {len(matched_data)}")
        print(f"Median improvement: {pd.Series(matched_data).median():.3f}s")

if __name__ == '__main__':
    main()

