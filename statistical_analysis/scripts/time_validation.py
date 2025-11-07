#!/usr/bin/env python3
"""
Shared time validation functions for all analysis scripts
"""

# Event time ranges (min, max in seconds) - adjusted based on actual elite performance
# These ranges accommodate the fastest legitimate times we've verified
EVENT_TIME_RANGES = {
    '50 Free': (18, 65),
    '100 Free': (45, 120),
    '200 Free': (105, 300),  # Adjusted: 105 instead of 110 (1:45 is realistic for elite)
    '400 Free': (230, 600),   # Adjusted: 230 instead of 240 (3:50 verified real)
    '800 Free': (480, 1200),  # Adjusted: 480 instead of 540 (8:00 verified real)
    '1500 Free': (900, 2400), # Adjusted: 900 instead of 960 (15:00 verified real)
    '100 Back': (50, 130),
    '200 Back': (105, 300),   # Adjusted: 105 instead of 110
    '100 Breast': (55, 140),
    '200 Breast': (120, 320),
    '100 Fly': (50, 130),
    '200 Fly': (110, 300),
    '200 IM': (115, 320),     # Adjusted: 115 instead of 120
    '400 IM': (250, 720)      # Adjusted: 250 instead of 280 (4:10 is realistic)
}

def validate_times(df, event, verbose=False):
    """
    Validate swim times in a dataframe against expected ranges for the event.
    
    Args:
        df: DataFrame with 'time_seconds' column
        event: Event name (e.g., '50 Free')
        verbose: If True, print warnings about invalid times
    
    Returns:
        DataFrame with invalid times filtered out
    """
    if 'time_seconds' not in df.columns:
        if verbose:
            print(f"Warning: No 'time_seconds' column found")
        return df
    
    min_time, max_time = EVENT_TIME_RANGES.get(event, (10, 1000))
    invalid_times = df[(df['time_seconds'] < min_time) | (df['time_seconds'] > max_time)]
    
    if len(invalid_times) > 0 and verbose:
        print(f"⚠️  WARNING: Found {len(invalid_times)} invalid times for {event} outside range [{min_time}, {max_time}] seconds")
        print(f"   Invalid times: {invalid_times['time_seconds'].tolist()[:10]}")
        if len(invalid_times) > 10:
            print(f"   ... and {len(invalid_times) - 10} more")
    
    # Filter out invalid times
    df_valid = df[(df['time_seconds'] >= min_time) & (df['time_seconds'] <= max_time)].copy()
    
    return df_valid

