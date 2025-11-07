# Malaysian Data Integration Plan

## Overview
This plan outlines the progressive integration of Malaysian swimmer data into the MOT Delta Analysis system, starting with easy foundational elements and building to full longitudinal analysis.

---

## Phase 1: Foundation (Easy - Do First) ✅

### 1.1 Malaysian Raw Data Analysis
**Goal**: Compare Malaysian swimmers' current performance to USA reference curves

**What We Have**:
- Current year's raw data from Malaysian meets in the database
- Age on first day of competition (calculated from meet date - birth date)

**Steps**:
1. **Extract Malaysian Results**
   - Query `results` table for Malaysian swimmers (where `is_foreign = 0`)
   - Include: name, gender, age (on first day of competition), event, time_seconds, meet_date
   - Group by event, gender, age (15, 16, 17, 18)

2. **Calculate Z-Scores Against USA Reference**
   - For each Malaysian swimmer's time:
     - Find corresponding USA Period Data (e.g., "F 50 Free 15" from appropriate period)
     - Calculate mean and std dev of USA times
     - Calculate z-score: `z = (USA_mean - Malaysian_time) / USA_std`
     - Positive z = faster than USA mean (better)
     - Negative z = slower than USA mean

3. **Generate Initial Comparison Report**
   - Show Malaysian swimmers' z-score distribution
   - Compare to USA z-score distribution
   - Identify which z-score ranges Malaysian swimmers fall into
   - Create visualization: Malaysian swimmers overlaid on USA curve

**Output**: `Malaysian_vs_USA_ZScore_Comparison.html`

---

## Phase 2: Malaysian Performance Analysis (Medium)

### 2.1 Malaysian Swimmer Distribution by Z-Score Range
**Goal**: Understand where Malaysian swimmers sit relative to USA benchmarks

**Analysis**:
- Count Malaysian swimmers in each z-score range:
  - Bottom 15.9% (z < -1.0)
  - Lower (-1.0 ≤ z < -0.5)
  - Below Average (-0.5 ≤ z < 0)
  - Average (0 ≤ z < 0.5)
  - Above Average (0.5 ≤ z < 1.0)
  - Top 15.9% (1.0 ≤ z < 1.5)
  - Top 6.7% (1.5 ≤ z < 2.0)
  - Top 2.5% (z ≥ 2.0)

- Compare distribution percentages to USA (all USA swimmers are by definition in "top 500")
- Identify gaps and opportunities

### 2.2 Event-Specific Malaysian Analysis
**Goal**: See which events Malaysian swimmers perform best/worst in relative to USA

**Analysis**:
- For each event/gender:
  - Number of Malaysian swimmers
  - Average z-score of Malaysian swimmers
  - Best Malaysian z-score
  - Distribution across z-score ranges
  - Percentage of Malaysian swimmers in "on track" ranges (1.5-2.0+ z)

**Output**: Add section to each event-specific MOT report showing Malaysian swimmers' positions

---

## Phase 3: Longitudinal Malaysian Analysis (Harder - Requires Multiple Years)

### 3.1 Malaysian Delta Analysis (Future)
**Goal**: Calculate Malaysian swimmers' actual improvement deltas

**Requirements**:
- Need multiple years of Malaysian data (2+ years minimum)
- Need to track same swimmers across years (by name matching)
- Calculate age transitions: 15→16, 16→17, 17→18

**What This Will Show**:
- Do Malaysian swimmers improve at similar rates to USA?
- Are Malaysian deltas different from USA deltas?
- Should MOT times be adjusted based on Malaysian actual performance?

**Output**: `Malaysian_Delta_Analysis.csv` and event-specific sections

---

## Implementation: Phase 1 Script

### Script: `analyze_malaysian_zscores.py`

```python
"""
Analyze Malaysian swimmers' z-scores against USA reference data
"""

Steps:
1. Load Malaysian results from database
2. For each Malaysian result:
   - Determine USA reference period data file
   - Calculate z-score
   - Categorize into z-score range
3. Generate summary statistics
4. Create comparison visualization
5. Output HTML report
```

### Database Query Structure

```sql
-- Get Malaysian swimmers with their results
SELECT 
    r.athlete_name,
    r.gender,
    r.age,  -- Age on first day of competition
    r.distance,
    r.stroke,
    r.time_seconds,
    r.meet_date,
    CASE 
        WHEN r.distance = 50 AND r.stroke = 'FREE' THEN '50 Free'
        WHEN r.distance = 100 AND r.stroke = 'FREE' THEN '100 Free'
        -- ... etc for all events
    END as event
FROM results r
WHERE r.is_foreign = 0  -- Malaysian swimmers only
    AND r.age BETWEEN 15 AND 18
    AND r.time_seconds IS NOT NULL
ORDER BY r.gender, event, r.age, r.time_seconds
```

---

## Where Reports Should Go

### Recommendation:

1. **Overarching Guide** (`DATA_INTERPRETATION_GUIDE.md`):
   - ✅ Already on landing page (linked next to Methodology)
   - Contains universal patterns and insights

2. **Event-Specific Reports** (`{Gender}_{Event}_MOT_Delta_Analysis.html`):
   - ✅ Already linked from landing page table
   - Location: `statistical_analysis/reports/`
   - **Add Malaysian section** when Phase 1 complete

3. **Malaysian Comparison Report**:
   - New: `Malaysian_vs_USA_ZScore_Comparison.html`
   - Location: `statistical_analysis/reports/`
   - Link from landing page in new "Malaysian Data Analysis" section

4. **Landing Page Updates**:
   - Add link to Data Interpretation Guide (✅ done)
   - Add new section for Malaysian data (when Phase 1 complete)

---

## Progress Checklist

- [x] Add Section 8 to event-specific reports
- [x] Create gender patterns summary
- [x] Update landing page with Data Interpretation Guide link
- [ ] **Phase 1**: Create `analyze_malaysian_zscores.py` script
- [ ] **Phase 1**: Generate initial Malaysian vs USA comparison
- [ ] **Phase 1**: Add Malaysian section to event-specific reports
- [ ] **Phase 2**: Add Malaysian distribution analysis
- [ ] **Phase 3**: (Future) Calculate Malaysian deltas when multi-year data available

---

## Questions to Answer with Phase 1 Analysis

1. **Where do Malaysian swimmers fall on the USA curve?**
   - Are they concentrated in certain z-score ranges?
   - How many are in "on track" ranges (1.5-2.0+ z)?

2. **Which events show strongest Malaysian performance?**
   - Relative to USA benchmarks
   - Which events need most development?

3. **Age distribution patterns?**
   - Do Malaysian swimmers at age 15, 16, 17, 18 show different patterns?
   - Are there gaps at certain ages?

4. **Gender differences in Malaysian data?**
   - Do Malaysian female swimmers show similar patterns to USA females?
   - Do Malaysian male swimmers show similar patterns to USA males?

---

## Next Steps

1. **Create Phase 1 script** (`analyze_malaysian_zscores.py`)
2. **Run initial analysis** on current Malaysian data
3. **Generate comparison report**
4. **Add Malaysian section to event reports**
5. **Update landing page** with Malaysian data section

Once Phase 1 is complete, we'll have valuable insights comparing Malaysian swimmers to USA benchmarks, which will inform MOT time setting even before we have Malaysian delta data.














