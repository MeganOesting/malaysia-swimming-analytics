#!/usr/bin/env python3
"""
Show flagged times with athlete names for manual verification
This helps distinguish between real elite times and data errors
"""

import os
import pandas as pd
import re
from pathlib import Path

def parse_swim_time(time_str):
    """Parse swim time string to seconds"""
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

# Adjusted ranges - more realistic based on elite performance
EVENT_TIME_RANGES = {
    '50 Free': (18, 65),
    '100 Free': (45, 120),
    '200 Free': (110, 300),
    '400 Free': (230, 600),  # Adjusted: 230 instead of 240 (3:50 is real)
    '800 Free': (480, 1200),  # Adjusted: 480 instead of 540 (8:00 is real)
    '1500 Free': (900, 2400),  # Adjusted: 900 instead of 960 (15:00 is real)
    '100 Back': (50, 130),
    '200 Back': (110, 300),
    '100 Breast': (55, 140),
    '200 Breast': (120, 320),
    '100 Fly': (50, 130),
    '200 Fly': (110, 300),
    '200 IM': (115, 320),  # Adjusted: 115 instead of 120
    '400 IM': (250, 720)  # Adjusted: 250 instead of 280 (4:10 is real)
}

def check_file(filepath, gender, event, age, period):
    """Check a file and return flagged records with names"""
    if not os.path.exists(filepath):
        return None
    
    try:
        df = pd.read_csv(
            filepath,
            sep='\t',
            encoding='utf-8',
            dtype={'Name': str},
            on_bad_lines='skip'
        )
    except Exception as e:
        return {'error': f"Could not read file: {e}"}
    
    # Find time column
    time_col = None
    name_col = None
    for col in ['Swim Time', 'Time', 'time']:
        if col in df.columns:
            time_col = col
            break
    
    for col in ['Name', 'name', 'Athlete']:
        if col in df.columns:
            name_col = col
            break
    
    if time_col is None:
        return {'error': f"No time column found. Columns: {list(df.columns)}"}
    
    # Parse times
    df['time_seconds'] = df[time_col].apply(parse_swim_time)
    df = df.dropna(subset=['time_seconds'])
    
    # Check time ranges
    min_time, max_time = EVENT_TIME_RANGES.get(event, (10, 1000))
    invalid_times = df[(df['time_seconds'] < min_time) | (df['time_seconds'] > max_time)]
    
    if len(invalid_times) == 0:
        return None
    
    # Get names and times for flagged records
    flagged = []
    for idx, row in invalid_times.iterrows():
        name = row.get(name_col, 'Unknown') if name_col else 'Unknown'
        time_sec = row['time_seconds']
        time_str = row.get(time_col, str(time_sec))
        flagged.append({
            'name': str(name),
            'time_text': str(time_str),
            'time_seconds': time_sec,
            'issue': 'too_fast' if time_sec < min_time else 'too_slow'
        })
    
    return {
        'gender': gender,
        'event': event,
        'age': age,
        'period': period,
        'min_threshold': min_time,
        'max_threshold': max_time,
        'flagged_count': len(flagged),
        'flagged_records': flagged
    }

def main():
    """Check specific files that were flagged"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if 'statistical_analysis' in script_dir.lower():
        data_dir = os.path.join(script_dir, "..", "data", "Period Data")
    else:
        data_dir = os.path.join("data", "Period Data")
    
    # Files to check - focusing on ones with many flagged times or suspicious patterns
    files_to_check = [
        ('F', '1500 Free', '16', '9.1.21-8.31.22'),
        ('F', '400 Free', '15', '9.1.21-8.31.22'),
        ('F', '200 Back', '15', '9.1.22-8.31.23'),  # All 500 times flagged - likely data error
        ('M', '800 Free', '15', '9.1.21-8.31.22'),  # Many flagged
        ('M', '400 IM', '15', '9.1.21-8.31.22'),  # Many flagged
    ]
    
    print("=" * 80)
    print("FLAGGED TIMES WITH ATHLETE NAMES FOR VERIFICATION")
    print("=" * 80)
    print()
    
    for gender, event, age, period in files_to_check:
        filename = f"{gender} {event} {age} {period}.txt"
        folder_name = f"{gender} {event} {period}"
        filepath = os.path.join(data_dir, period, folder_name, filename)
        
        print(f"\n{'='*80}")
        print(f"Checking: {gender} {event} Age {age} Period {period}")
        print(f"{'='*80}")
        
        result = check_file(filepath, gender, event, age, period)
        
        if result is None:
            print("✅ No flagged times (all within adjusted ranges)")
            continue
        
        if 'error' in result:
            print(f"❌ ERROR: {result['error']}")
            continue
        
        print(f"\nThresholds: Min = {result['min_threshold']}s, Max = {result['max_threshold']}s")
        print(f"Flagged: {result['flagged_count']} records")
        print()
        
        # Group by issue type
        too_fast = [r for r in result['flagged_records'] if r['issue'] == 'too_fast']
        too_slow = [r for r in result['flagged_records'] if r['issue'] == 'too_slow']
        
        if too_fast:
            print(f"⚠️  TIMES TOO FAST (below {result['min_threshold']}s):")
            print(f"   Showing first 20 of {len(too_fast)}:")
            for i, r in enumerate(too_fast[:20], 1):
                print(f"   {i}. {r['name']:<30} {r['time_text']:<15} ({r['time_seconds']:.2f}s)")
            if len(too_fast) > 20:
                print(f"   ... and {len(too_fast) - 20} more")
        
        if too_slow:
            print(f"\n⚠️  TIMES TOO SLOW (above {result['max_threshold']}s):")
            print(f"   Showing first 20 of {len(too_slow)}:")
            for i, r in enumerate(too_slow[:20], 1):
                print(f"   {i}. {r['name']:<30} {r['time_text']:<15} ({r['time_seconds']:.2f}s)")
            if len(too_slow) > 20:
                print(f"   ... and {len(too_slow) - 20} more")
        
        # Save detailed report
        report_file = os.path.join(script_dir, "..", "reports", f"flagged_times_{gender}_{event}_{age}_{period.replace('.', '_').replace('-', '_')}.txt")
        os.makedirs(os.path.dirname(report_file), exist_ok=True)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(f"FLAGGED TIMES FOR VERIFICATION\n")
            f.write(f"=" * 80 + "\n\n")
            f.write(f"Event: {gender} {event} Age {age} Period {period}\n")
            f.write(f"Thresholds: Min = {result['min_threshold']}s, Max = {result['max_threshold']}s\n")
            f.write(f"Total flagged: {result['flagged_count']}\n\n")
            
            if too_fast:
                f.write(f"TIMES TOO FAST (below {result['min_threshold']}s):\n")
                f.write("-" * 80 + "\n")
                for r in too_fast:
                    f.write(f"{r['name']:<40} {r['time_text']:<20} ({r['time_seconds']:.2f}s)\n")
                f.write("\n")
            
            if too_slow:
                f.write(f"TIMES TOO SLOW (above {result['max_threshold']}s):\n")
                f.write("-" * 80 + "\n")
                for r in too_slow:
                    f.write(f"{r['name']:<40} {r['time_text']:<20} ({r['time_seconds']:.2f}s)\n")
        
        print(f"\n✅ Detailed report saved: {os.path.basename(report_file)}")

if __name__ == "__main__":
    main()




