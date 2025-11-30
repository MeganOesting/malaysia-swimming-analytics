# Malaysia On Track (MOT) Base Times Methodology

**Last Updated:** 2025-11-30

---

## Overview

The Malaysia On Track (MOT) system provides age-appropriate target times for Malaysian swimmers ages 15-23 (18-23 for 50m events). These targets help coaches and athletes understand what times are needed at each age to be "on track" to achieve international elite performance.

---

## Data Sources

| Source | Purpose | Table |
|--------|---------|-------|
| Canada Swimming On Track | Base times and age progression deltas | `canada_on_track` |
| USA Swimming Delta Data | Age progression deltas (ages 15-18) | `usa_delta_data` |

---

## Core Methodology

### Delta Source Rules

| Age Transition | Primary Source | Fallback |
|----------------|----------------|----------|
| 15 to 16 | USA Swimming median | Canada average delta |
| 16 to 17 | USA Swimming median | Canada average delta |
| 17 to 18 | USA Swimming median | Canada average delta |
| 18 to 19 | Canada average delta | - |
| 19 to 20 | Canada average delta | - |
| 20+ | Canada average delta | - |

**Key Rules:**
1. **Ages 15-18 transitions:** Use USA Swimming median delta
2. **If USA median is NEGATIVE:** Fall back to Canada On Track average delta
3. **Ages 18+ transitions:** Always use Canada On Track average delta
4. **Canada average delta:** Average across all tracks that have data for that transition

---

## Calculation Method

### Step 1: Anchor Point

We anchor at the **final time of Canada Track 1** (the earliest-developing track). This is the target time at the Track 1 final age.

```
anchor_time = Canada Track 1 time at its final age
```

### Step 2: Work Backwards

Starting from the anchor point, work backwards to younger ages by adding the appropriate delta:

```
mot_time[age] = mot_time[age + 1] + delta[age to age+1]
```

**Note:** Adding the delta makes the younger age time slower (as expected - younger swimmers are slower).

### Step 3: Determine Delta Sources

For each age transition:

1. **Check if Canada has data for this transition**
   - A Canada delta exists if ANY track has times for both ages
   - Average all available track deltas

2. **For ages 15-17 (requiring USA delta):**
   - Look up USA median delta for this event/transition
   - If USA median >= 0: Use USA median
   - If USA median < 0: Use Canada average delta (fallback)

3. **For ages 18+:**
   - Always use Canada average delta

---

## 50m Events - Special Handling

**MOT times for 50m events begin at age 18 only.**

Reasons:
1. USA Swimming does not commonly contest 50m events at ages 15-17
2. Sprint performance at ages 15-17 does not correlate strongly with senior elite potential
3. Physical maturation plays a larger role in sprint events, making early predictions less reliable

50m events affected:
- LCM_Free_50_F, LCM_Free_50_M
- LCM_Back_50_F, LCM_Back_50_M
- LCM_Breast_50_F, LCM_Breast_50_M
- LCM_Fly_50_F, LCM_Fly_50_M

---

## Why This Approach?

### USA Swimming Data (Ages 15-18)
- Largest dataset of age-group swimmers globally
- Top 500 swimmers per event/age/gender across 4 seasons (2021-2025)
- Median values reduce impact of outliers
- Represents realistic improvement expectations

### Canada On Track Data (Ages 18+)
- Evidence-based progression tracks from Swimming Canada
- Three tracks (1, 2, 3) represent different development pathways
- Track 1 = earliest developers, Track 3 = latest developers
- All tracks converge to same elite target time

**History of Canada On Track:**
- **2013:** Swimming Canada introduced On Track times to identify developing swimmers
  - Used international competition data and Canadian age group progression rates
  - Three tracks to capture early to late developers
- **2014:** Partnership with Canadian Tire Financial Services and Own The Podium
  - Sports analytics group analyzed 2+ million results from world-class athletes
  - Provided insights into career progression patterns
- **2017:** Version 2 introduced for Tokyo 2020 quad
  - Continued same principles with enhanced analytics
- **Current:** Updated annually after each long course World Championships
  - Incorporates latest World Aquatics A standards as final On Track time
  - Provides seamless pathway from athlete identification to senior team qualification

### Negative USA Delta Fallback
- Some events show negative USA median at 17-18 (swimmers getting slower)
- This reflects developmental plateau, NOT realistic targets
- Canada tracks show continued improvement at 17-18
- Fallback ensures all MOT times show proper progression (older = faster)

---

## Example Calculation: F 100 Free

**Canada Track 1 for F 100 Free:**
- Age 14: 58.43s
- Age 15: 56.55s
- Age 16: 55.29s
- Age 17: 54.55s
- Age 18: 54.09s
- Age 19: 53.77s
- Age 20: 53.54s (final)

**USA Deltas:**
- 15-16: +0.76s (positive, use this)
- 16-17: +0.37s (positive, use this)
- 17-18: -0.15s (NEGATIVE, fallback to Canada)

**Canada 17-18 Average:**
- Track 1: 54.55 - 54.09 = 0.46s
- Track 2: (has both ages) = 0.46s
- Average = 0.46s

**Calculation (working backwards from Track 1 age 20):**
```
Age 20: 53.54s (anchor)
Age 19: 53.54 + 0.23 = 53.77s (Canada avg 19-20)
Age 18: 53.77 + 0.32 = 54.09s (Canada avg 18-19)
Age 17: 54.09 + 0.46 = 54.55s (Canada avg - fallback)
Age 16: 54.55 + 0.37 = 54.92s (USA median)
Age 15: 54.92 + 0.76 = 55.68s (USA median)
```

---

## Database Tables

### mot_base_times
```sql
CREATE TABLE mot_base_times (
    id INTEGER PRIMARY KEY,
    mot_event_id TEXT NOT NULL,      -- e.g., LCM_Back_100_F
    mot_age INTEGER NOT NULL,         -- 15-23 (or 18-23 for 50m)
    mot_time_seconds REAL,            -- target time in seconds
    UNIQUE(mot_event_id, mot_age)
);
```

### Supporting Tables
- `canada_on_track` - Canada Swimming track times by event, track, and age
- `usa_delta_data` - USA Swimming improvement data by event and age transition

---

## Data Quality Notes

### Swimmers Who "Dropped Out" of Top 500
When analyzing USA data, "dropped out" refers to swimmers who fell out of the top 500 rankings for their age/event, not swimmers who quit the sport. Many of these swimmers reappear in later years:
- ~32% of 15-16 top-500 dropouts reappear by age 18
- ~38% of 16-17 top-500 dropouts reappear at age 18

### Improvement Percentages
When comparing improvement across events, use percentages rather than raw seconds:
- 0.5s improvement in 50 Free (~2%) is more significant than
- 0.5s improvement in 400 Free (~0.1%)

---

## Validation

All MOT times are validated to ensure:
1. Older ages always have faster times than younger ages
2. No NULL values except 50m events at ages 15-17
3. Times fall within reasonable bounds for each event

---

## Maintenance

When updating MOT base times:
1. Ensure Canada On Track data is current
2. Verify USA delta data is loaded
3. Run recalculation script
4. Validate no progression errors (older must be faster)

---

## References

- [Swimming Canada On Track Times](https://www.swimming.ca/on-track-times/)
- [2025 Canada On Track Times PDF](https://www.swimming.ca/wp-content/uploads/2025/04/On-Track-Times-for-SNC-Website-APRIL-2025.pdf)
- USA Swimming season rankings (2021-2025)

---

## Author
Malaysia Swimming Analytics System
