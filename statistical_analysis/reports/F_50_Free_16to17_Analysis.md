# F 50 Free 16→17 Transition Analysis

## Purpose
This document shows the data needed to determine the Malaysia On Track (MOT) delta for F 50 Free 16→17 transition, comparing Canada On Track reference data with USA swimming improvement statistics.

---

## Canada On Track Data (Track 1 - Early Developers)

### Track 1 Times
- **Age 16**: 25.66 seconds
- **Age 17**: 25.40 seconds
- **Delta (improvement)**: 25.66 - 25.40 = **0.26 seconds**

### Track Information
- **Track Type**: Track 1 (Early) - 4-year progression path
- **Entry Age**: 16 (Track 1 starts at age 16 for F 50 Free)
- **Note**: Track 1 represents early developers who enter the system at age 16 and follow a 4-year progression to medal potential

### Z-Score Information
*Note: Z-scores are not currently stored in the database. To calculate z-scores, we would need:*
- Population mean time for age 16 (F 50 Free)
- Population standard deviation for age 16 (F 50 Free)
- Population mean time for age 17 (F 50 Free)  
- Population standard deviation for age 17 (F 50 Free)

*If z-score data is needed, we can calculate it from the Canada On Track reference distribution or USA swimming population statistics.*

---

## USA Swimming Delta Analysis

### USA Median Improvement (16→17)
- **Median Delta**: **0.15 seconds**
- **Mean Delta**: 0.175 seconds
- **Sample Size**: 339 matched athletes
- **Standard Deviation**: 0.384 seconds
- **IQR (Q25 to Q75)**: -0.07 to 0.39 seconds

### Methodology
- **Data Source**: USA Swimming season rankings (top 500 per age/event/gender)
- **Matching**: Athletes who swam in both consecutive seasons were matched
- **Period Comparison**: Season 2223 (age 16) → Season 2324 (age 17)
- **Improvement Calculation**: time(age 16) - time(age 17) for each matched athlete

### Key Insight
USA median improvement (0.15s) is **smaller** than Canada Track 1 delta (0.26s), suggesting:
- Canada Track 1 represents a more aggressive/faster improvement pathway
- USA improvement represents the median of all swimmers (mix of development patterns)
- This difference will inform the MOT delta calculation

---

## Comparison Summary

| Metric | Canada Track 1 | USA Median | Difference |
|--------|---------------|------------|------------|
| **Delta (16→17)** | 0.26s | 0.15s | **0.11s** |
| **Pathway** | Early developers (4-year track) | All swimmers (median) | - |
| **Sample** | Reference benchmark | 339 athletes | - |

---

## Next Steps for MOT Delta Determination

To determine the MOT delta for F 50 Free 16→17:

1. **Consider Track Options**:
   - Use Canada Track 1 delta (0.26s) for early developer pathway
   - Use USA median (0.15s) for general population pathway
   - Create weighted average or alternative calculation

2. **Additional Context Needed**:
   - Canada Track 2 (Middle) and Track 3 (Late) deltas for this transition (if available)
   - USA distribution percentiles (to match Track 1 = top X% of USA swimmers)
   - Regional/SEA Games context for final MOT target times

3. **Z-Score Analysis** (if needed):
   - Calculate z-scores for Canada Track 1 times relative to USA population
   - This would show: "Track 1 represents the Xth percentile of USA swimmers"

---

## Data Sources

- **Canada On Track**: `statistical_analysis/database/statistical.db` → `canada_on_track` table
- **USA Deltas**: `statistical_analysis/database/statistical.db` → `usa_age_deltas` table
- **Query Date**: Generated from latest database snapshot

---

*This analysis is part of the MOT Delta Analysis Project to reconstruct Malaysia On Track reference times using USA swimming improvement statistics and Canada On Track methodology.*




