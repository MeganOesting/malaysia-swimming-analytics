#!/usr/bin/env python3
"""
MOT Delta Analysis Project - Complete Analysis Script
====================================================

This script executes all 84 improvement analyses for the MOT Delta Analysis Project.
It analyzes improvement deltas between age transitions (15->16, 16->17, 17->18)
for all swimming events to create evidence-based Malaysia On Track times.

Project Scope:
- 14 Events: 50 Free, 100 Free, 200 Free, 400 Free, 800 Free, 1500 Free, 100 Back, 200 Back, 
  100 Breast, 200 Breast, 100 Fly, 200 Fly, 200 IM, 400 IM
- 2 Genders: Male (M), Female (F)
- 3 Age Transitions: 15->16, 16->17, 17->18
- Total Analyses: 84 (14 × 2 × 3)

Methodology:
1. Load data from Period Data folders
2. Match athletes between consecutive ages
3. Calculate improvement deltas (time differences)
4. Generate statistical analysis (median, mean, std dev, IQR)
5. Create Delta Data folders with results
6. Update MOT Delta Tracking Master.xlsx
"""

import os
import re
import pandas as pd
import numpy as np
from datetime import datetime
import glob

# Define project parameters - INCLUDING 50 FREE
EVENTS = [
    "50 Free", "100 Free", "200 Free", "400 Free", "800 Free", "1500 Free",
    "100 Back", "200 Back", "100 Breast", "200 Breast", 
    "100 Fly", "200 Fly", "200 IM", "400 IM"
]

GENDERS = ["F", "M"]
AGE_TRANSITIONS = [
    ("15", "16", "9.1.21-8.31.22", "9.1.22-8.31.23"),  # 15->16: 2021-2022 to 2022-2023
    ("16", "17", "9.1.22-8.31.23", "9.1.23-8.31.24"),  # 16->17: 2022-2023 to 2023-2024
    ("17", "18", "9.1.23-8.31.24", "9.1.24-8.31.25")   # 17->18: 2023-2024 to 2024-2025
]

def load_period_data(gender, event, age, period):
    """Load data from a specific period file"""
    filename = f"{gender} {event} {age} {period}.txt"
    # Handle both old and new folder structures
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if 'statistical_analysis' in script_dir.lower():
        # New structure: statistical_analysis/data/Period Data/
        filepath = os.path.join(script_dir, "..", "data", "Period Data", period, f"{gender} {event} {period}", filename)
    else:
        # Old structure: Period Data/
        filepath = os.path.join("Period Data", period, f"{gender} {event} {period}", filename)
    
    if not os.path.exists(filepath):
        print(f"Warning: File not found: {filepath}")
        return None
    
    try:
        # Be tolerant of irregular lines and encoding
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
    """Parse swim time string to seconds. Strips trailing letters like 'r' and any non-time chars."""
    if pd.isna(time_str) or time_str == '':
        return None
    
    s = str(time_str).strip()
    # Remove any trailing letters (e.g., '1:00.08r' -> '1:00.08') and spaces
    s = re.sub(r"[a-zA-Z]+$", "", s).strip()
    # Remove any stray characters except digits, colon, dot
    s = re.sub(r"[^0-9:\.]", "", s)
    if s == "":
        return None

    # Handle time formats
    if ':' in s:
        parts = s.split(':')
        try:
            if len(parts) == 2:  # MM:SS.ss
                minutes = int(parts[0]) if parts[0] else 0
                seconds = float(parts[1])
                return minutes * 60 + seconds
            elif len(parts) == 3:  # HH:MM:SS.ss
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

def analyze_age_transition(gender, event, age_from, age_to, period_from, period_to):
    """Analyze improvement between two consecutive ages"""
    print(f"Analyzing {gender} {event} {age_from}->{age_to} ({period_from} to {period_to})")
    
    # Load data for both ages
    df_from = load_period_data(gender, event, age_from, period_from)
    df_to = load_period_data(gender, event, age_to, period_to)
    
    if df_from is None or df_to is None:
        print(f"  Skipping - missing data files")
        return None
    
    # Parse swim times
    df_from['time_seconds'] = df_from['Swim Time'].apply(parse_swim_time)
    df_to['time_seconds'] = df_to['Swim Time'].apply(parse_swim_time)
    
    # Remove rows with invalid times
    df_from = df_from.dropna(subset=['time_seconds'])
    df_to = df_to.dropna(subset=['time_seconds'])
    
    # Match athletes by name (case-insensitive)
    df_from['name_lower'] = df_from['Name'].astype(str).str.lower().str.strip()
    df_to['name_lower'] = df_to['Name'].astype(str).str.lower().str.strip()
    
    # Find common athletes
    common_names = set(df_from['name_lower']) & set(df_to['name_lower'])
    
    if len(common_names) < 10:  # Need minimum sample size
        print(f"  Skipping - insufficient matched athletes ({len(common_names)})")
        return None
    
    # Create matched dataset
    matched_data = []
    for name in common_names:
        from_row = df_from[df_from['name_lower'] == name].iloc[0]
        to_row = df_to[df_to['name_lower'] == name].iloc[0]
        
        improvement = from_row['time_seconds'] - to_row['time_seconds']  # Positive = improvement
        improvement_pct = (improvement / from_row['time_seconds']) * 100 if from_row['time_seconds'] else None
        
        matched_data.append({
            'name': from_row.get('Name', name),
            'age_from': age_from,
            'age_to': age_to,
            'time_from': from_row['time_seconds'],
            'time_to': to_row['time_seconds'],
            'improvement_seconds': improvement,
            'improvement_percentage': improvement_pct,
            'rank_from': from_row.get('Rank'),
            'rank_to': to_row.get('Rank'),
            'foreign': from_row.get('Foreign', 'No')
        })
    
    matched_df = pd.DataFrame(matched_data)
    
    # Calculate statistics
    improvements = matched_df['improvement_seconds'].dropna()
    
    if len(improvements) < 5:
        print(f"  Skipping - insufficient valid improvements ({len(improvements)})")
        return None
    
    stats = {
        'event': event,
        'gender': gender,
        'age_from': age_from,
        'age_to': age_to,
        'period_from': period_from,
        'period_to': period_to,
        'sample_size': len(improvements),
        'median_improvement': float(np.median(improvements)),
        'mean_improvement': float(np.mean(improvements)),
        'std_improvement': float(np.std(improvements)),
        'min_improvement': float(np.min(improvements)),
        'max_improvement': float(np.max(improvements)),
        'q25_improvement': float(np.percentile(improvements, 25)),
        'q75_improvement': float(np.percentile(improvements, 75)),
        'iqr_lower': float(np.percentile(improvements, 25)),
        'iqr_upper': float(np.percentile(improvements, 75)),
        'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'status': 'Complete'
    }
    
    # Create Delta Data folder
    folder_name = f"{gender} {event} {age_from} to {age_to}"
    # Handle both old and new folder structures
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if 'statistical_analysis' in script_dir.lower():
        # New structure: statistical_analysis/data/Delta Data/
        delta_folder = os.path.join(script_dir, "..", "data", "Delta Data", folder_name)
    else:
        # Old structure: Delta Data/
        delta_folder = os.path.join("Delta Data", folder_name)
    os.makedirs(delta_folder, exist_ok=True)
    
    # Save detailed data
    csv_filename = f"{folder_name} Athlete_Improvement_Data.csv"
    matched_df.to_csv(os.path.join(delta_folder, csv_filename), index=False, encoding='utf-8')
    
    # Generate analysis report
    report_filename = f"{folder_name} Improvement Analysis Report.txt"
    with open(os.path.join(delta_folder, report_filename), 'w', encoding='utf-8') as f:
        f.write(f"MOT DELTA ANALYSIS REPORT\n")
        f.write(f"========================\n\n")
        f.write(f"Event: {event}\n")
        f.write(f"Gender: {gender}\n")
        f.write(f"Age Transition: {age_from}->{age_to}\n")
        f.write(f"Periods: {period_from} to {period_to}\n")
        f.write(f"Analysis Date: {stats['analysis_date']}\n\n")
        
        f.write(f"SAMPLE STATISTICS\n")
        f.write(f"=================\n")
        f.write(f"Sample Size: {stats['sample_size']} athletes\n")
        f.write(f"Median Improvement: {stats['median_improvement']:.3f} seconds\n")
        f.write(f"Mean Improvement: {stats['mean_improvement']:.3f} seconds\n")
        f.write(f"Standard Deviation: {stats['std_improvement']:.3f} seconds\n")
        f.write(f"Min Improvement: {stats['min_improvement']:.3f} seconds\n")
        f.write(f"Max Improvement: {stats['max_improvement']:.3f} seconds\n")
        f.write(f"Q25 (IQR Lower): {stats['q25_improvement']:.3f} seconds\n")
        f.write(f"Q75 (IQR Upper): {stats['q75_improvement']:.3f} seconds\n")
        f.write(f"IQR Range: {stats['iqr_upper'] - stats['q25_improvement']:.3f} seconds\n\n")
        
        f.write(f"IMPROVEMENT DISTRIBUTION\n")
        f.write(f"=======================\n")
        f.write(f"Positive Improvements: {int((improvements > 0).sum())} athletes\n")
        f.write(f"Negative Changes: {int((improvements < 0).sum())} athletes\n")
        f.write(f"No Change: {int((improvements == 0).sum())} athletes\n\n")
        
        f.write(f"STATISTICAL SIGNIFICANCE\n")
        f.write(f"=======================\n")
        if stats['sample_size'] >= 30:
            f.write(f"Sample size is adequate for statistical analysis (n>=30)\n")
        else:
            f.write(f"Sample size is small but acceptable for preliminary analysis (n<30)\n")
        
        f.write(f"Median improvement of {stats['median_improvement']:.3f}s represents ")
        f.write(f"the typical improvement for this age transition.\n")
        
        if stats['median_improvement'] > 0:
            f.write(f"This suggests consistent improvement from age {age_from} to {age_to}.\n")
        else:
            f.write(f"This suggests minimal or no improvement from age {age_from} to {age_to}.\n")
    
    print(f"  ✓ Analysis complete: {stats['sample_size']} athletes, median improvement: {stats['median_improvement']:.3f}s")
    return stats

def main():
    """Execute all 84 MOT Delta analyses"""
    print("MOT DELTA ANALYSIS PROJECT")
    print("==========================")
    print(f"Starting analysis of {len(EVENTS)} events x {len(GENDERS)} genders x {len(AGE_TRANSITIONS)} transitions")
    print(f"Total analyses: {len(EVENTS) * len(GENDERS) * len(AGE_TRANSITIONS)}")
    print(f"Events included: {', '.join(EVENTS)}")
    print()
    
    all_results = []
    completed_analyses = 0
    skipped_analyses = 0
    
    for event in EVENTS:
        for gender in GENDERS:
            for age_from, age_to, period_from, period_to in AGE_TRANSITIONS:
                try:
                    result = analyze_age_transition(gender, event, age_from, age_to, period_from, period_to)
                    if result:
                        all_results.append(result)
                        completed_analyses += 1
                    else:
                        skipped_analyses += 1
                except Exception as e:
                    print(f"  Error analyzing {gender} {event} {age_from}->{age_to}: {e}")
                    skipped_analyses += 1
    
    print()
    print("ANALYSIS SUMMARY")
    print("================")
    print(f"Completed analyses: {completed_analyses}")
    print(f"Skipped analyses: {skipped_analyses}")
    print(f"Total attempted: {completed_analyses + skipped_analyses}")
    
    if all_results:
        # Create summary DataFrame
        results_df = pd.DataFrame(all_results)
        
        # Save to CSV
        results_df.to_csv("MOT_Delta_Analysis_Results.csv", index=False, encoding='utf-8')
        
        print(f"\nResults saved to: MOT_Delta_Analysis_Results.csv")
        print(f"Delta Data folders created in: Delta Data/")
        
        # Print summary statistics
        print(f"\nOVERALL STATISTICS")
        print(f"==================")
        print(f"Total athletes analyzed: {int(results_df['sample_size'].sum())}")
        print(f"Average sample size per analysis: {results_df['sample_size'].mean():.1f}")
        print(f"Median improvement across all analyses: {results_df['median_improvement'].median():.3f}s")
        print(f"Mean improvement across all analyses: {results_df['mean_improvement'].mean():.3f}s")
    
    print("\nMOT Delta Analysis Project - Complete!")
    print("Ready for MOT table reconstruction and curriculum integration.")

if __name__ == "__main__":
    main()
