#!/usr/bin/env python3
"""
Analyze the distribution shape of swim times in period data
This helps understand:
1. Is the distribution normal or skewed?
2. What portion of all swimmers do the top 500 represent?
3. How does truncation affect our analysis?
"""

import os
import pandas as pd
import numpy as np
from scipy import stats
from pathlib import Path

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

def load_period_data(gender, event, age, period):
    """Load data from a specific period file"""
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
            encoding='utf-8',
            dtype={'Name': str}
        )
        return df
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return None

def analyze_distribution(times, event_name):
    """Analyze the distribution shape of swim times"""
    times = np.array(times)
    n = len(times)
    
    # Basic statistics
    mean_time = np.mean(times)
    median_time = np.median(times)
    std_time = np.std(times)
    skewness = stats.skew(times)
    kurtosis = stats.kurtosis(times)
    
    # Test for normality (Shapiro-Wilk - good for n < 5000)
    if n <= 5000:
        try:
            shapiro_stat, shapiro_p = stats.shapiro(times)
            is_normal = shapiro_p > 0.05
        except:
            shapiro_stat, shapiro_p = None, None
            is_normal = None
    else:
        # For large samples, use Anderson-Darling or just check skew/kurtosis
        shapiro_stat, shapiro_p = None, None
        is_normal = abs(skewness) < 0.5 and abs(kurtosis) < 0.5
    
    # Check skewness interpretation
    if skewness > 1:
        skew_interpretation = "Highly right-skewed (long tail of slow times)"
    elif skewness > 0.5:
        skew_interpretation = "Moderately right-skewed"
    elif skewness > -0.5:
        skew_interpretation = "Approximately symmetric"
    elif skewness > -1:
        skew_interpretation = "Moderately left-skewed"
    else:
        skew_interpretation = "Highly left-skewed"
    
    # Coefficient of variation
    cv = (std_time / mean_time) * 100 if mean_time > 0 else 0
    
    # Range
    min_time = np.min(times)
    max_time = np.max(times)
    range_time = max_time - min_time
    
    # IQR
    q25 = np.percentile(times, 25)
    q75 = np.percentile(times, 75)
    iqr = q75 - q25
    
    return {
        'n': n,
        'mean': mean_time,
        'median': median_time,
        'std': std_time,
        'min': min_time,
        'max': max_time,
        'range': range_time,
        'q25': q25,
        'q75': q75,
        'iqr': iqr,
        'skewness': skewness,
        'kurtosis': kurtosis,
        'cv': cv,
        'shapiro_stat': shapiro_stat,
        'shapiro_p': shapiro_p,
        'is_normal': is_normal,
        'skew_interpretation': skew_interpretation,
        'mean_median_diff': mean_time - median_time,
        'mean_median_ratio': mean_time / median_time if median_time > 0 else None
    }

def estimate_total_participation(gender, event, age, period):
    """
    Estimate total participation based on:
    - USA Swimming registration numbers
    - Active competitive swimmers
    - Event participation rates
    """
    # USA Swimming has ~400,000 registered members
    # But many are recreational, masters, etc.
    # Competitive age group (15-18): maybe 100,000-150,000 active?
    
    # Rough estimates:
    # - Total registered: 400,000
    # - Competitive age group (15-18): ~30-40% = 120,000-160,000
    # - Active in meets: ~50-70% = 60,000-112,000
    # - Swim a specific event in a season: ~20-40% = 12,000-45,000
    # - By gender: divide by 2 = 6,000-22,500
    
    # But this varies by event:
    # - 50 Free: Very popular, maybe 40-50% participation
    # - 1500 Free: Less popular, maybe 5-10% participation
    # - IMs: Moderate, maybe 15-25% participation
    
    event_popularity = {
        '50 Free': 0.45,
        '100 Free': 0.40,
        '200 Free': 0.30,
        '400 Free': 0.25,
        '800 Free': 0.15,
        '1500 Free': 0.08,
        '100 Back': 0.25,
        '200 Back': 0.20,
        '100 Breast': 0.25,
        '200 Breast': 0.18,
        '100 Fly': 0.22,
        '200 Fly': 0.15,
        '200 IM': 0.20,
        '400 IM': 0.10
    }
    
    # Conservative estimate
    active_competitive_15_18 = 80000  # conservative
    per_gender = active_competitive_15_18 / 2  # ~40,000
    per_age = per_gender / 4  # 15, 16, 17, 18 = ~10,000 per age
    
    participation_rate = event_popularity.get(event, 0.20)
    estimated_total = int(per_age * participation_rate)
    
    return estimated_total

def main():
    """Analyze distribution for a sample event"""
    gender = "F"
    event = "50 Free"
    age = 15
    period = "9.1.21-8.31.22"
    
    print("=" * 80)
    print("DISTRIBUTION SHAPE ANALYSIS")
    print("=" * 80)
    print(f"Analyzing: {gender} {event} Age {age} Period {period}\n")
    
    # Load data
    df = load_period_data(gender, event, str(age), period)
    if df is None:
        print("Error: Could not load data")
        return
    
    # Parse times
    time_col = None
    for col in ['Swim Time', 'Time', 'time']:
        if col in df.columns:
            time_col = col
            break
    
    if time_col is None:
        print(f"Error: Could not find time column. Available: {list(df.columns)}")
        return
    
    df['time_seconds'] = df[time_col].apply(parse_swim_time)
    df = df.dropna(subset=['time_seconds'])
    
    # Validate times
    event_time_ranges = {
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
    min_time, max_time = event_time_ranges.get(event, (10, 1000))
    df = df[(df['time_seconds'] >= min_time) & (df['time_seconds'] <= max_time)]
    
    times = df['time_seconds'].values
    
    print(f"Sample size: {len(times)} swimmers\n")
    
    # Analyze distribution
    stats_dict = analyze_distribution(times, event)
    
    print("BASIC STATISTICS:")
    print(f"  Mean: {stats_dict['mean']:.2f} seconds")
    print(f"  Median: {stats_dict['median']:.2f} seconds")
    print(f"  Std Dev: {stats_dict['std']:.2f} seconds")
    print(f"  Min: {stats_dict['min']:.2f} seconds")
    print(f"  Max: {stats_dict['max']:.2f} seconds")
    print(f"  Range: {stats_dict['range']:.2f} seconds")
    print(f"  IQR: {stats_dict['iqr']:.2f} seconds (Q25: {stats_dict['q25']:.2f}, Q75: {stats_dict['q75']:.2f})")
    print(f"  Coefficient of Variation: {stats_dict['cv']:.2f}%")
    print()
    
    print("DISTRIBUTION SHAPE:")
    print(f"  Skewness: {stats_dict['skewness']:.3f}")
    print(f"  Interpretation: {stats_dict['skew_interpretation']}")
    print(f"  Kurtosis: {stats_dict['kurtosis']:.3f}")
    print(f"  Mean - Median: {stats_dict['mean_median_diff']:.3f} seconds")
    if stats_dict['mean_median_ratio']:
        print(f"  Mean/Median ratio: {stats_dict['mean_median_ratio']:.3f}")
    print()
    
    if stats_dict['shapiro_p'] is not None:
        print("NORMALITY TEST (Shapiro-Wilk):")
        print(f"  Test statistic: {stats_dict['shapiro_stat']:.4f}")
        print(f"  p-value: {stats_dict['shapiro_p']:.6f}")
        if stats_dict['is_normal']:
            print(f"  Result: Distribution is approximately normal (p > 0.05)")
        else:
            print(f"  Result: Distribution is NOT normal (p <= 0.05)")
        print()
    
    # Estimate total participation
    estimated_total = estimate_total_participation(gender, event, age, period)
    sample_size = len(times)
    percentage = (sample_size / estimated_total) * 100 if estimated_total > 0 else None
    
    print("PARTICIPATION ESTIMATES:")
    print(f"  Sample size (top 500): {sample_size}")
    print(f"  Estimated total participants: ~{estimated_total:,} (conservative)")
    print(f"  Percentage captured: ~{percentage:.2f}%" if percentage else "  (Unable to estimate)")
    print(f"  We are capturing the TOP {sample_size} out of ~{estimated_total:,} swimmers")
    print()
    
    print("IMPLICATIONS FOR ANALYSIS:")
    print("=" * 80)
    print("1. DISTRIBUTION SHAPE:")
    if stats_dict['skewness'] > 0.5:
        print("   - The distribution is RIGHT-SKEWED (long tail of slower times)")
        print("   - This means we're looking at the RIGHT TAIL of a larger distribution")
        print("   - The 'true' distribution of ALL swimmers would be even more skewed")
    elif stats_dict['skewness'] < -0.5:
        print("   - The distribution is LEFT-SKEWED (long tail of faster times)")
        print("   - This is unusual for swim times - may indicate truncation effect")
    else:
        print("   - The distribution is approximately symmetric")
        print("   - This may be because we're looking at a truncated elite sample")
    print()
    
    print("2. TRUNCATION EFFECT:")
    print("   - We have the TOP 500 swimmers (fastest times)")
    print("   - This is a CENSORED/TRUNCATED sample from the left")
    print("   - The full distribution would include many slower swimmers")
    print("   - Our sample represents the ELITE portion of competitive swimmers")
    print()
    
    print("3. NORMALITY ASSUMPTION:")
    if stats_dict['is_normal'] is False:
        print("   - The distribution is NOT normal")
        print("   - This is expected: swim times are typically right-skewed")
        print("   - Even within the top 500, we see skewness")
    else:
        print("   - The distribution may be approximately normal within this elite sample")
        print("   - But the full population would NOT be normal")
    print()
    
    print("4. PRACTICAL IMPLICATIONS:")
    print("   - Z-scores are still useful for ranking within this elite group")
    print("   - Percentiles are meaningful relative to the top 500")
    print("   - We CANNOT extrapolate to the full population")
    print("   - MOT standards are based on this elite sample, which is appropriate")
    print("   - The 'bell curve' we see is the RIGHT TAIL of the true distribution")
    print()
    
    print("5. WHAT WE'RE CAPTURING:")
    if percentage:
        print(f"   - We're capturing ~{percentage:.2f}% of competitive swimmers")
        print(f"   - This represents the TOP ~{100-percentage:.2f} percentile")
        print(f"   - For MOT purposes, this is appropriate - we want elite standards")
    else:
        print("   - Exact percentage unknown, but likely 1-5% of competitive swimmers")
    print()
    
    # Save to file
    script_dir = os.path.dirname(os.path.abspath(__file__))
    report_file = os.path.join(script_dir, "..", "reports", "distribution_shape_analysis.txt")
    os.makedirs(os.path.dirname(report_file), exist_ok=True)
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("DISTRIBUTION SHAPE ANALYSIS\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Event: {gender} {event} Age {age} Period {period}\n\n")
        f.write("KEY FINDINGS:\n")
        f.write(f"- Sample size: {sample_size} (top 500)\n")
        f.write(f"- Distribution shape: {stats_dict['skew_interpretation']}\n")
        f.write(f"- Skewness: {stats_dict['skewness']:.3f}\n")
        if stats_dict['is_normal'] is not None:
            f.write(f"- Normal distribution: {'No' if not stats_dict['is_normal'] else 'Yes (within elite sample)'}\n")
        if percentage:
            f.write(f"- Estimated total participants: ~{estimated_total:,}\n")
            f.write(f"- Percentage captured: ~{percentage:.2f}%\n")
        f.write("\nCONCLUSION:\n")
        f.write("The top 500 represents a truncated sample from the right tail of the\n")
        f.write("full distribution. The true distribution of all swimmers would be\n")
        f.write("highly right-skewed. Our sample captures the elite competitive swimmers,\n")
        f.write("which is appropriate for setting MOT standards.\n")
    
    print(f"✅ Full analysis saved to: {report_file}")

if __name__ == "__main__":
    main()




