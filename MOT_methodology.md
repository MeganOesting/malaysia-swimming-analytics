# Malaysia On Track (MOT) Base Times Methodology

**Last Updated:** 2025-11-28

---

## Overview

The Malaysia On Track (MOT) system provides age-appropriate target times for Malaysian swimmers ages 15-23. These targets help coaches and athletes understand what times are needed at each age to be "on track" to achieve SEA Games podium performance by peak age.

---

## Data Sources

| Source | Purpose | Table |
|--------|---------|-------|
| SEA Games Podium Target Times | Final target (peak performance) | `podium_target_times` |
| Canada Swimming On Track | Age progression deltas (ages 18-23) | `canada_on_track` |
| USA Swimming Delta Data | Age progression deltas (ages 15-18) | `usa_delta_data` |

---

## Key Concept: Final Age (Peak Performance Age)

Different events have different "final ages" - the age at which swimmers typically reach peak performance. This is determined by the Canada On Track data, which provides Track 1, 2, and 3 times up to the expected peak age.

| Final Age | Events |
|-----------|--------|
| 21 | LCM_Back_100_F, LCM_Back_200_F, LCM_Medley_400_F |
| 22 | LCM_Fly_200_F, LCM_Free_1500_F, LCM_Free_200_F, LCM_Free_400_F, LCM_Free_800_F |
| 23 | LCM_Back_200_M, LCM_Back_50_F, LCM_Breast_100_F, LCM_Breast_200_F, LCM_Breast_200_M, LCM_Fly_100_F, LCM_Fly_200_M, LCM_Free_100_F, LCM_Free_100_M, LCM_Free_1500_M, LCM_Free_200_M, LCM_Free_400_M, LCM_Free_800_M, LCM_Medley_200_F, LCM_Medley_400_M |
| 24 | LCM_Back_100_M, LCM_Back_50_M, LCM_Breast_100_M, LCM_Breast_50_F, LCM_Fly_100_M, LCM_Free_50_F, LCM_Medley_200_M |
| 25 | LCM_Fly_50_F, LCM_Fly_50_M, LCM_Free_50_M |
| 26 | LCM_Breast_50_M |

---

## Calculation Method

### Step 1: Anchor Point (Age 23)

All calculations start from the **podium target time** for the most recent SEA Games year. This is stored at age 23 regardless of final age.

```
mot_time[23] = podium_target_time (most recent year)
```

### Step 2: Plateau Ages (Final Age to 23)

For events where final age < 23, the podium target time is also used for ages between final age and 23 (inclusive). Athletes are expected to maintain peak performance during this plateau.

**Example - Final Age 21:**
```
mot_time[23] = podium_target_time
mot_time[22] = podium_target_time
mot_time[21] = podium_target_time
```

### Step 3: Ages 18-22 (Canada On Track Deltas)

Working backwards from the plateau, we use Canada On Track data to calculate expected times. The formula uses **track deltas** - the difference in time between consecutive ages within a track.

**Track Delta Formula:**
```
track_delta(track, age_from, age_to) = canada_track_time[age_from] - canada_track_time[age_to]
```

**Key Rule:** We can only use a track's delta if the track has times for BOTH ages in the transition.

The number of tracks averaged depends on the final age and current age being calculated:

---

### Final Age 21 Events

| Age | Formula |
|-----|---------|
| 23 | podium_target_time |
| 22 | podium_target_time |
| 21 | podium_target_time |
| 20 | age_21 + (Track3_20 - Track3_21) |
| 19 | age_20 + (Track3_19 - Track3_20) |
| 18 | age_19 + [(Track3_18 - Track3_19) + (Track2_18 - Track2_19)] / 2 |

---

### Final Age 22 Events

| Age | Formula |
|-----|---------|
| 23 | podium_target_time |
| 22 | podium_target_time |
| 21 | age_22 + (Track3_21 - Track3_22) |
| 20 | age_21 + (Track3_20 - Track3_21) |
| 19 | age_20 + [(Track3_19 - Track3_20) + (Track2_19 - Track2_20)] / 2 |
| 18 | age_19 + [(Track3_18 - Track3_19) + (Track2_18 - Track2_19)] / 2 |

---

### Final Age 23 Events

| Age | Formula |
|-----|---------|
| 23 | podium_target_time |
| 22 | age_23 + (Track3_22 - Track3_23) |
| 21 | age_22 + (Track3_21 - Track3_22) |
| 20 | age_21 + [(Track3_20 - Track3_21) + (Track2_20 - Track2_21)] / 2 |
| 19 | age_20 + [(Track3_19 - Track3_20) + (Track2_19 - Track2_20)] / 2 |
| 18 | age_19 + [(Track3_18 - Track3_19) + (Track2_18 - Track2_19) + (Track1_18 - Track1_19)] / 3 |

---

### Final Age 24 Events

| Age | Formula |
|-----|---------|
| 23 | podium_target_time |
| 22 | age_23 + (Track3_22 - Track3_23) |
| 21 | age_22 + [(Track3_21 - Track3_22) + (Track2_21 - Track2_22)] / 2 |
| 20 | age_21 + [(Track3_20 - Track3_21) + (Track2_20 - Track2_21)] / 2 |
| 19 | age_20 + [(Track3_19 - Track3_20) + (Track2_19 - Track2_20) + (Track1_19 - Track1_20)] / 3 |
| 18 | age_19 + [(Track3_18 - Track3_19) + (Track2_18 - Track2_19) + (Track1_18 - Track1_19)] / 3 |

---

### Final Age 25 Events

| Age | Formula |
|-----|---------|
| 23 | podium_target_time |
| 22 | age_23 + [(Track3_22 - Track3_23) + (Track2_22 - Track2_23)] / 2 |
| 21 | age_22 + [(Track3_21 - Track3_22) + (Track2_21 - Track2_22)] / 2 |
| 20 | age_21 + [(Track3_20 - Track3_21) + (Track2_20 - Track2_21) + (Track1_20 - Track1_21)] / 3 |
| 19 | age_20 + [(Track3_19 - Track3_20) + (Track2_19 - Track2_20) + (Track1_19 - Track1_20)] / 3 |
| 18 | age_19 + [(Track2_18 - Track2_19) + (Track1_18 - Track1_19)] / 2 |

---

### Final Age 26 Events

| Age | Formula |
|-----|---------|
| 23 | podium_target_time |
| 22 | age_23 + [(Track3_22 - Track3_23) + (Track2_22 - Track2_23)] / 2 |
| 21 | age_22 + [(Track3_21 - Track3_22) + (Track2_21 - Track2_22) + (Track1_21 - Track1_22)] / 3 |
| 20 | age_21 + [(Track3_20 - Track3_21) + (Track2_20 - Track2_21) + (Track1_20 - Track1_21)] / 3 |
| 19 | age_20 + [(Track3_19 - Track3_20) + (Track2_19 - Track2_20)] / 2 |
| 18 | age_19 + (Track2_18 - Track2_19) |

---

### Step 4: Ages 15-17 (USA Delta Medians)

For ages 15-17, we use the **median improvement** from USA Swimming data. This represents the typical improvement seen in USA age-group swimmers transitioning between ages.

| Age | Formula |
|-----|---------|
| 17 | age_18 + usa_delta_median(17→18) |
| 16 | age_17 + usa_delta_median(16→17) |
| 15 | age_16 + usa_delta_median(15→16) |

**Note:** The usa_delta_median is the median of `improvement_seconds` from the `usa_delta_data` table for the specific event and age transition.

### Exception: 50m Events

**50m events do NOT have ages 15-17 populated.** USA Swimming does not race 50m LCM events in age-group competition (they primarily race yards), so there is no USA delta data for these events.

For 50m events, MOT times are only calculated for ages 18-23 using Canada On Track data:
- LCM_Back_50_F (Final age 23): Ages 18-23
- LCM_Back_50_M (Final age 24): Ages 18-23
- LCM_Breast_50_F (Final age 24): Ages 18-23
- LCM_Breast_50_M (Final age 26): Ages 18-23 (age 18 may be NULL if Track 2 data unavailable)
- LCM_Fly_50_F (Final age 25): Ages 18-23
- LCM_Fly_50_M (Final age 25): Ages 18-23
- LCM_Free_50_F (Final age 24): Ages 18-23
- LCM_Free_50_M (Final age 25): Ages 18-23

---

## Why This Approach?

### Canada On Track for Ages 18-23
- Canada Swimming has developed evidence-based progression tracks
- Three tracks (1, 2, 3) represent different development pathways
- Track 1 = fastest development, Track 3 = slowest
- Using multiple tracks and averaging provides realistic targets

### USA Delta Data for Ages 15-17
- Largest dataset of age-group swimmers globally
- Median values reduce impact of outliers
- Represents realistic improvement expectations for developing swimmers

### Track Blending Logic
- **Near peak age:** Use slower tracks (Track 3) - swimmers are refining, not making large gains
- **Further from peak:** Blend more tracks - swimmers can be on various development paths
- **Youngest ages (15-17):** Use USA data as Canada tracks don't extend this young

---

## Database Tables

### mot_base_times
```sql
CREATE TABLE mot_base_times (
    id INTEGER PRIMARY KEY,
    mot_event_id TEXT NOT NULL,      -- e.g., LCM_Back_100_F
    mot_age INTEGER NOT NULL,         -- 15-23
    mot_time_seconds REAL,            -- target time in seconds
    UNIQUE(mot_event_id, mot_age)
);
```

### Supporting Tables
- `podium_target_times` - SEA Games podium times by event and year
- `canada_on_track` - Canada Swimming track times by event, track, and age
- `usa_delta_data` - USA Swimming improvement data by event and age transition

---

## Maintenance

When podium_target_times is updated (e.g., after SEA Games 2025):
1. The script automatically uses the most recent `sea_games_year`
2. All MOT times cascade from the new podium target
3. Re-run `populate_mot_base_times.py` to update

---

## Author
Malaysia Swimming Analytics System
