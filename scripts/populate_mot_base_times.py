"""
Populate mot_base_times table with calculated target times.

Logic:
1. Age 23 = podium_target_time (most recent year)
2. Ages at/above final age = podium_target_time (plateau)
3. Ages 18-22 = calculated from Canada On Track deltas
4. Ages 15-17 = calculated from USA delta medians

See MOT_methodology.md for detailed explanation.
"""

import sqlite3
import os

# Paths
BASE_PATH = r"C:\Users\megan\OneDrive\Documents\Malaysia Swimming Analytics"
DB_PATH = os.path.join(BASE_PATH, "malaysia_swimming.db")

# Event final ages (from Canada On Track data)
FINAL_AGES = {
    # Final age 21
    'LCM_Back_100_F': 21,
    'LCM_Back_200_F': 21,
    'LCM_Medley_400_F': 21,
    # Final age 22
    'LCM_Fly_200_F': 22,
    'LCM_Free_1500_F': 22,
    'LCM_Free_200_F': 22,
    'LCM_Free_400_F': 22,
    'LCM_Free_800_F': 22,
    # Final age 23
    'LCM_Back_200_M': 23,
    'LCM_Back_50_F': 23,
    'LCM_Breast_100_F': 23,
    'LCM_Breast_200_F': 23,
    'LCM_Breast_200_M': 23,
    'LCM_Fly_100_F': 23,
    'LCM_Fly_200_M': 23,
    'LCM_Free_100_F': 23,
    'LCM_Free_100_M': 23,
    'LCM_Free_1500_M': 23,
    'LCM_Free_200_M': 23,
    'LCM_Free_400_M': 23,
    'LCM_Free_800_M': 23,
    'LCM_Medley_200_F': 23,
    'LCM_Medley_400_M': 23,
    # Final age 24
    'LCM_Back_100_M': 24,
    'LCM_Back_50_M': 24,
    'LCM_Breast_100_M': 24,
    'LCM_Breast_50_F': 24,
    'LCM_Fly_100_M': 24,
    'LCM_Free_50_F': 24,
    'LCM_Medley_200_M': 24,
    # Final age 25
    'LCM_Fly_50_F': 25,
    'LCM_Fly_50_M': 25,
    'LCM_Free_50_M': 25,
    # Final age 26
    'LCM_Breast_50_M': 26,
}


def get_podium_times(conn):
    """Get podium target times for most recent year."""
    cur = conn.cursor()
    cur.execute("SELECT MAX(sea_games_year) FROM podium_target_times")
    most_recent_year = cur.fetchone()[0]

    cur.execute("""
        SELECT event_id, target_time_seconds
        FROM podium_target_times
        WHERE sea_games_year = ?
    """, (most_recent_year,))

    podium = {row[0]: row[1] for row in cur.fetchall()}
    print(f"[OK] Loaded {len(podium)} podium times for year {most_recent_year}")
    return podium


def get_canada_track_times(conn):
    """
    Get Canada On Track times organized by event, track, and age.
    Returns: {event_id: {track: {age: time_seconds}}}
    """
    cur = conn.cursor()
    cur.execute("""
        SELECT event_id, canada_track, canada_track_age, canada_track_time_seconds
        FROM canada_on_track
    """)

    canada = {}
    for event_id, track, age, time_sec in cur.fetchall():
        if event_id not in canada:
            canada[event_id] = {}
        if track not in canada[event_id]:
            canada[event_id][track] = {}
        canada[event_id][track][age] = time_sec

    print(f"[OK] Loaded Canada On Track data for {len(canada)} events")
    return canada


def get_usa_delta_medians(conn):
    """
    Get USA delta medians by event and age transition.
    Returns: {event_id: {(age_start, age_end): median}}
    """
    cur = conn.cursor()
    cur.execute("""
        SELECT usa_delta_event_id, usa_delta_age_start, usa_delta_age_end, usa_delta_median
        FROM usa_delta_data
        WHERE usa_delta_median IS NOT NULL
        GROUP BY usa_delta_event_id, usa_delta_age_start, usa_delta_age_end
    """)

    usa = {}
    for event_id, age_start, age_end, median in cur.fetchall():
        if event_id not in usa:
            usa[event_id] = {}
        usa[event_id][(age_start, age_end)] = median

    print(f"[OK] Loaded USA delta medians for {len(usa)} events")
    return usa


def get_track_delta(canada, event_id, track, age_from, age_to):
    """
    Calculate track delta (improvement) between two ages.
    Returns None if either age is missing for this track.

    Delta = time_at_younger_age - time_at_older_age
    (Positive delta means improvement/faster at older age)
    """
    if event_id not in canada:
        return None
    if track not in canada[event_id]:
        return None

    track_data = canada[event_id][track]

    if age_from not in track_data or age_to not in track_data:
        return None

    return track_data[age_from] - track_data[age_to]


def calculate_age_time(mot_times, canada, event_id, target_age, source_age, tracks_to_use):
    """
    Calculate MOT time for target_age using source_age and specified tracks.

    Formula: mot_time[target_age] = mot_time[source_age] + avg(track_deltas)

    Going backwards (younger ages), times get SLOWER (larger), so we ADD the delta.
    Delta = track_time[younger] - track_time[older] (positive = younger is slower)

    tracks_to_use: list of track numbers to average, e.g., [3] or [3, 2] or [3, 2, 1]
    """
    if source_age not in mot_times:
        return None

    source_time = mot_times[source_age]

    # Calculate deltas for each specified track
    deltas = []
    for track in tracks_to_use:
        delta = get_track_delta(canada, event_id, track, target_age, source_age)
        if delta is not None:
            deltas.append(delta)

    if not deltas:
        print(f"  [WARNING] No track deltas available for {event_id} age {target_age}->{source_age}")
        return None

    avg_delta = sum(deltas) / len(deltas)
    return source_time + avg_delta


def populate_event(conn, event_id, podium_time, canada, usa):
    """Populate MOT times for a single event."""
    cur = conn.cursor()

    final_age = FINAL_AGES.get(event_id)
    if final_age is None:
        print(f"  [WARNING] No final age defined for {event_id}")
        return 0

    mot_times = {}

    # Step 1: Age 23 = podium target
    mot_times[23] = podium_time

    # Step 2: Plateau ages (final_age to 22) = podium target
    for age in range(final_age, 23):
        mot_times[age] = podium_time

    # Step 3: Ages 18-22 based on final age formulas
    # Working backwards from the first non-plateau age

    if final_age == 21:
        # Age 20: Track 3 only
        mot_times[20] = calculate_age_time(mot_times, canada, event_id, 20, 21, [3])
        # Age 19: Track 3 only
        mot_times[19] = calculate_age_time(mot_times, canada, event_id, 19, 20, [3])
        # Age 18: Track 3 + Track 2
        mot_times[18] = calculate_age_time(mot_times, canada, event_id, 18, 19, [3, 2])

    elif final_age == 22:
        # Age 21: Track 3 only
        mot_times[21] = calculate_age_time(mot_times, canada, event_id, 21, 22, [3])
        # Age 20: Track 3 only
        mot_times[20] = calculate_age_time(mot_times, canada, event_id, 20, 21, [3])
        # Age 19: Track 3 + Track 2
        mot_times[19] = calculate_age_time(mot_times, canada, event_id, 19, 20, [3, 2])
        # Age 18: Track 3 + Track 2
        mot_times[18] = calculate_age_time(mot_times, canada, event_id, 18, 19, [3, 2])

    elif final_age == 23:
        # Age 22: Track 3 only
        mot_times[22] = calculate_age_time(mot_times, canada, event_id, 22, 23, [3])
        # Age 21: Track 3 only
        mot_times[21] = calculate_age_time(mot_times, canada, event_id, 21, 22, [3])
        # Age 20: Track 3 + Track 2
        mot_times[20] = calculate_age_time(mot_times, canada, event_id, 20, 21, [3, 2])
        # Age 19: Track 3 + Track 2
        mot_times[19] = calculate_age_time(mot_times, canada, event_id, 19, 20, [3, 2])
        # Age 18: Track 3 + Track 2 + Track 1
        mot_times[18] = calculate_age_time(mot_times, canada, event_id, 18, 19, [3, 2, 1])

    elif final_age == 24:
        # Age 22: Track 3 only
        mot_times[22] = calculate_age_time(mot_times, canada, event_id, 22, 23, [3])
        # Age 21: Track 3 + Track 2
        mot_times[21] = calculate_age_time(mot_times, canada, event_id, 21, 22, [3, 2])
        # Age 20: Track 3 + Track 2
        mot_times[20] = calculate_age_time(mot_times, canada, event_id, 20, 21, [3, 2])
        # Age 19: Track 3 + Track 2 + Track 1
        mot_times[19] = calculate_age_time(mot_times, canada, event_id, 19, 20, [3, 2, 1])
        # Age 18: Track 3 + Track 2 + Track 1
        mot_times[18] = calculate_age_time(mot_times, canada, event_id, 18, 19, [3, 2, 1])

    elif final_age == 25:
        # Age 22: Track 3 + Track 2
        mot_times[22] = calculate_age_time(mot_times, canada, event_id, 22, 23, [3, 2])
        # Age 21: Track 3 + Track 2
        mot_times[21] = calculate_age_time(mot_times, canada, event_id, 21, 22, [3, 2])
        # Age 20: Track 3 + Track 2 + Track 1
        mot_times[20] = calculate_age_time(mot_times, canada, event_id, 20, 21, [3, 2, 1])
        # Age 19: Track 3 + Track 2 + Track 1
        mot_times[19] = calculate_age_time(mot_times, canada, event_id, 19, 20, [3, 2, 1])
        # Age 18: Track 2 + Track 1 (no Track 3)
        mot_times[18] = calculate_age_time(mot_times, canada, event_id, 18, 19, [2, 1])

    elif final_age == 26:
        # Age 22: Track 3 + Track 2
        mot_times[22] = calculate_age_time(mot_times, canada, event_id, 22, 23, [3, 2])
        # Age 21: Track 3 + Track 2 + Track 1
        mot_times[21] = calculate_age_time(mot_times, canada, event_id, 21, 22, [3, 2, 1])
        # Age 20: Track 3 + Track 2 + Track 1
        mot_times[20] = calculate_age_time(mot_times, canada, event_id, 20, 21, [3, 2, 1])
        # Age 19: Track 3 + Track 2 (no Track 1 for this transition)
        mot_times[19] = calculate_age_time(mot_times, canada, event_id, 19, 20, [3, 2])
        # Age 18: Track 2 only
        mot_times[18] = calculate_age_time(mot_times, canada, event_id, 18, 19, [2])

    # Step 4: Ages 15-17 using USA delta medians
    # Skip for 50m events - USA doesn't have 50m LCM age-group data
    is_50m_event = '_50_' in event_id

    if not is_50m_event:
        # Going backwards (younger ages), times get SLOWER, so we ADD the median
        usa_event = usa.get(event_id, {})

        # Age 17
        if 18 in mot_times and mot_times[18] is not None:
            median_17_18 = usa_event.get((17, 18))
            if median_17_18 is not None:
                mot_times[17] = mot_times[18] + median_17_18
            else:
                print(f"  [WARNING] No USA median for {event_id} 17->18")

        # Age 16
        if 17 in mot_times and mot_times[17] is not None:
            median_16_17 = usa_event.get((16, 17))
            if median_16_17 is not None:
                mot_times[16] = mot_times[17] + median_16_17
            else:
                print(f"  [WARNING] No USA median for {event_id} 16->17")

        # Age 15
        if 16 in mot_times and mot_times[16] is not None:
            median_15_16 = usa_event.get((15, 16))
            if median_15_16 is not None:
                mot_times[15] = mot_times[16] + median_15_16
            else:
                print(f"  [WARNING] No USA median for {event_id} 15->16")

    # Update database
    update_count = 0
    for age in range(15, 24):
        time_sec = mot_times.get(age)
        if time_sec is not None:
            cur.execute("""
                UPDATE mot_base_times
                SET mot_time_seconds = ?
                WHERE mot_event_id = ? AND mot_age = ?
            """, (time_sec, event_id, age))
            update_count += cur.rowcount

    conn.commit()
    return update_count


def main():
    print("=" * 60)
    print("Populating MOT Base Times")
    print("=" * 60)

    conn = sqlite3.connect(DB_PATH)

    # Load data
    podium = get_podium_times(conn)
    canada = get_canada_track_times(conn)
    usa = get_usa_delta_medians(conn)

    # Process each event
    total_updates = 0
    events_processed = 0

    print("\nProcessing events...")
    for event_id in sorted(FINAL_AGES.keys()):
        if event_id not in podium:
            print(f"  [SKIP] {event_id} - no podium target time")
            continue

        podium_time = podium[event_id]
        updates = populate_event(conn, event_id, podium_time, canada, usa)
        total_updates += updates
        events_processed += 1

        final_age = FINAL_AGES[event_id]
        print(f"  [OK] {event_id} (final age {final_age}): {updates} rows updated")

    # Summary
    print(f"\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Events processed: {events_processed}")
    print(f"Total rows updated: {total_updates}")

    # Verification
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM mot_base_times WHERE mot_time_seconds IS NOT NULL")
    with_times = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM mot_base_times WHERE mot_time_seconds IS NULL")
    without_times = cur.fetchone()[0]

    print(f"Rows with times: {with_times}")
    print(f"Rows without times: {without_times}")

    # Sample output
    print(f"\nSample MOT times (LCM_Back_100_F - Final Age 21):")
    cur.execute("""
        SELECT mot_age, mot_time_seconds
        FROM mot_base_times
        WHERE mot_event_id = 'LCM_Back_100_F'
        ORDER BY mot_age
    """)
    for age, time_sec in cur.fetchall():
        if time_sec:
            mins = int(time_sec // 60)
            secs = time_sec % 60
            time_str = f"{mins}:{secs:05.2f}" if mins else f"{secs:.2f}"
            print(f"  Age {age}: {time_sec:.2f} ({time_str})")
        else:
            print(f"  Age {age}: NULL")

    print(f"\nSample MOT times (LCM_Free_50_M - Final Age 25):")
    cur.execute("""
        SELECT mot_age, mot_time_seconds
        FROM mot_base_times
        WHERE mot_event_id = 'LCM_Free_50_M'
        ORDER BY mot_age
    """)
    for age, time_sec in cur.fetchall():
        if time_sec:
            mins = int(time_sec // 60)
            secs = time_sec % 60
            time_str = f"{mins}:{secs:05.2f}" if mins else f"{secs:.2f}"
            print(f"  Age {age}: {time_sec:.2f} ({time_str})")
        else:
            print(f"  Age {age}: NULL")

    conn.close()
    print("\n[OK] Done!")


if __name__ == "__main__":
    main()
