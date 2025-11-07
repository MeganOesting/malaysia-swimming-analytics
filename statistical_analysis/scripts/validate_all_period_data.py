#!/usr/bin/env python3
"""
Validate ALL period data files to ensure times are parsed correctly
and within reasonable ranges for each event.
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

# Event time ranges (min, max in seconds)
EVENT_TIME_RANGES = {
    '50 Free': (18, 65),
    '100 Free': (45, 120),
    '200 Free': (110, 300),
    '400 Free': (240, 600),
    '800 Free': (540, 1200),
    '1500 Free': (960, 2400),
    '100 Back': (50, 130),
    '200 Back': (110, 300),
    '100 Breast': (55, 140),
    '200 Breast': (120, 320),
    '100 Fly': (50, 130),
    '200 Fly': (110, 300),
    '200 IM': (120, 320),
    '400 IM': (280, 720)
}

def validate_file(filepath, gender, event, age, period):
    """Validate a single period data file"""
    if not os.path.exists(filepath):
        return {'status': 'missing', 'errors': []}
    
    try:
        df = pd.read_csv(
            filepath,
            sep='\t',
            encoding='utf-8',
            dtype={'Name': str}
        )
    except Exception as e:
        return {'status': 'read_error', 'errors': [str(e)]}
    
    # Find time column
    time_col = None
    for col in ['Swim Time', 'Time', 'time']:
        if col in df.columns:
            time_col = col
            break
    
    if time_col is None:
        return {'status': 'no_time_column', 'errors': [f"No time column found. Columns: {list(df.columns)}"]}
    
    # Parse times
    df['time_seconds'] = df[time_col].apply(parse_swim_time)
    original_count = len(df)
    df = df.dropna(subset=['time_seconds'])
    after_parse_count = len(df)
    
    errors = []
    warnings = []
    
    if after_parse_count < original_count:
        warnings.append(f"{original_count - after_parse_count} rows could not be parsed")
    
    # Check time ranges
    min_time, max_time = EVENT_TIME_RANGES.get(event, (10, 1000))
    invalid_times = df[(df['time_seconds'] < min_time) | (df['time_seconds'] > max_time)]
    
    if len(invalid_times) > 0:
        invalid_list = invalid_times['time_seconds'].tolist()[:5]
        errors.append(f"{len(invalid_times)} times outside valid range [{min_time}, {max_time}]: {invalid_list}")
    
    # Check for expected count (should be ~500)
    if len(df) < 400:
        warnings.append(f"Only {len(df)} valid times (expected ~500)")
    
    if len(df) == 0:
        errors.append("No valid times after parsing!")
        return {'status': 'no_valid_times', 'errors': errors, 'warnings': warnings}
    
    # Check statistics
    min_t = df['time_seconds'].min()
    max_t = df['time_seconds'].max()
    mean_t = df['time_seconds'].mean()
    
    if min_t < min_time:
        errors.append(f"Minimum time {min_t:.2f} is below expected minimum {min_time}")
    if max_t > max_time:
        errors.append(f"Maximum time {max_t:.2f} is above expected maximum {max_time}")
    
    status = 'ok' if len(errors) == 0 else 'has_errors'
    
    return {
        'status': status,
        'errors': errors,
        'warnings': warnings,
        'stats': {
            'count': len(df),
            'min': float(min_t),
            'max': float(max_t),
            'mean': float(mean_t)
        }
    }

def main():
    """Validate all period data files"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if 'statistical_analysis' in script_dir.lower():
        data_dir = os.path.join(script_dir, "..", "data", "Period Data")
    else:
        data_dir = os.path.join("data", "Period Data")
    
    if not os.path.exists(data_dir):
        print(f"ERROR: Data directory not found: {data_dir}")
        return
    
    # Find all period directories
    periods = [d for d in os.listdir(data_dir) if os.path.isdir(os.path.join(data_dir, d))]
    
    results = []
    total_files = 0
    files_with_errors = 0
    files_with_warnings = 0
    
    for period in sorted(periods):
        period_path = os.path.join(data_dir, period)
        
        # Find event folders in this period
        for item in os.listdir(period_path):
            event_folder = os.path.join(period_path, item)
            if not os.path.isdir(event_folder):
                continue
            
            # Parse folder name to get gender and event
            # Format: "F 50 Free 9.1.21-8.31.22" or similar
            parts = item.split(' ')
            if len(parts) >= 3:
                gender = parts[0]
                event = ' '.join(parts[1:-1])  # Everything except first and last
                # Last part might be period, but we'll check files
                
                # Find all .txt files in this folder
                for filename in os.listdir(event_folder):
                    if not filename.endswith('.txt'):
                        continue
                    
                    # Parse filename: "F 50 Free 15 9.1.21-8.31.22.txt"
                    file_parts = filename.replace('.txt', '').split(' ')
                    if len(file_parts) >= 4:
                        file_gender = file_parts[0]
                        file_event = ' '.join(file_parts[1:-2])
                        file_age = file_parts[-2]
                        file_period = file_parts[-1]
                        
                        filepath = os.path.join(event_folder, filename)
                        total_files += 1
                        
                        result = validate_file(filepath, file_gender, file_event, file_age, file_period)
                        result['file'] = filename
                        result['path'] = filepath
                        result['gender'] = file_gender
                        result['event'] = file_event
                        result['age'] = file_age
                        result['period'] = file_period
                        
                        results.append(result)
                        
                        if len(result['errors']) > 0:
                            files_with_errors += 1
                        if len(result.get('warnings', [])) > 0:
                            files_with_warnings += 1
    
    # Print summary
    print("=" * 80)
    print("PERIOD DATA VALIDATION REPORT")
    print("=" * 80)
    print(f"Total files checked: {total_files}")
    print(f"Files with errors: {files_with_errors}")
    print(f"Files with warnings: {files_with_warnings}")
    print(f"Files OK: {total_files - files_with_errors - files_with_warnings}")
    print()
    
    # Print files with errors
    if files_with_errors > 0:
        print("=" * 80)
        print("FILES WITH ERRORS:")
        print("=" * 80)
        for r in results:
            if len(r['errors']) > 0:
                print(f"\n{r['file']}")
                print(f"  Path: {r['path']}")
                print(f"  Gender: {r['gender']}, Event: {r['event']}, Age: {r['age']}")
                for error in r['errors']:
                    print(f"  ❌ ERROR: {error}")
                if 'stats' in r:
                    print(f"  Stats: {r['stats']}")
    
    # Print files with warnings
    if files_with_warnings > 0:
        print("\n" + "=" * 80)
        print("FILES WITH WARNINGS:")
        print("=" * 80)
        for r in results:
            if len(r.get('warnings', [])) > 0 and len(r['errors']) == 0:
                print(f"\n{r['file']}")
                for warning in r['warnings']:
                    print(f"  ⚠️  WARNING: {warning}")
    
    # Save detailed report
    report_file = os.path.join(script_dir, "..", "reports", "period_data_validation_report.txt")
    os.makedirs(os.path.dirname(report_file), exist_ok=True)
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("PERIOD DATA VALIDATION REPORT\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Total files checked: {total_files}\n")
        f.write(f"Files with errors: {files_with_errors}\n")
        f.write(f"Files with warnings: {files_with_warnings}\n\n")
        
        if files_with_errors > 0:
            f.write("FILES WITH ERRORS:\n")
            f.write("=" * 80 + "\n")
            for r in results:
                if len(r['errors']) > 0:
                    f.write(f"\n{r['file']}\n")
                    f.write(f"  Path: {r['path']}\n")
                    f.write(f"  Gender: {r['gender']}, Event: {r['event']}, Age: {r['age']}\n")
                    for error in r['errors']:
                        f.write(f"  ERROR: {error}\n")
                    if 'stats' in r:
                        f.write(f"  Stats: {r['stats']}\n")
    
    print(f"\n✅ Detailed report saved to: {report_file}")

if __name__ == "__main__":
    main()




