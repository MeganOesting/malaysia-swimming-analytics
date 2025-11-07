# Data Validation Issue and Distribution Analysis

## The Problem You Discovered

You noticed that the density distribution graphs were showing impossible times like **0.03, 0.06, 0.07 seconds** for the 50 Free event, when the fastest time should be around **25.38 seconds**.

## Root Cause Analysis

### Why This Happened

**Two issues combined:**

1. **Chart.js Visualization Bug**: The Chart.js bar chart was using a `labels` array for bin centers, which Chart.js treated as categorical (string) labels. When the bin centers were small numbers (like 0.03, 0.06), Chart.js may have been displaying them incorrectly or using array indices instead of the actual values.

2. **Missing Data Validation**: There was no validation to catch and filter out invalid times that might have been parsed incorrectly from the source data files.

### The Fix

1. **Fixed Chart.js Configuration**: Changed from using `labels` array to using `{x, y}` data pairs with a `linear` scale type. This ensures Chart.js treats the x-axis values as actual numeric values, not categorical labels.

2. **Added Time Range Validation**: Added validation logic that:
   - Checks parsed times against expected ranges for each event
   - Filters out times that are outside reasonable bounds
   - Reports warnings when invalid times are found

### Events and Their Expected Time Ranges

```python
'50 Free': (18, 65) seconds      # ~18-65 seconds is reasonable for 15-year-olds
'100 Free': (45, 120) seconds
'200 Free': (110, 300) seconds
'400 Free': (240, 600) seconds
'800 Free': (540, 1200) seconds
'1500 Free': (960, 2400) seconds
'100 Back': (50, 130) seconds
'200 Back': (110, 300) seconds
'100 Breast': (55, 140) seconds
'200 Breast': (120, 320) seconds
'100 Fly': (50, 130) seconds
'200 Fly': (110, 300) seconds
'200 IM': (120, 320) seconds
'400 IM': (280, 720) seconds
```

## Fix Applied To

✅ `create_zscore_distribution_graph.py` - **FIXED**
- Added time validation
- Fixed Chart.js configuration

⚠️ **Other scripts that parse times need the same validation:**
- `run_mot_delta_analysis.py` - NEEDS VALIDATION ADDED
- `analyze_improvement_by_zscore.py` - NEEDS VALIDATION ADDED
- `validate_all_period_data.py` - Already has validation

## Distribution Shape Analysis

### Question: Is the Distribution Normal?

**Answer: NO** - and this is important!

### Why It's Not Normal

1. **Competitive Population**: We're looking at competitive swimmers, not all swimmers
   - Not all people swim
   - Not all swimmers compete
   - Not all competitors are at the same level
   - We're seeing the TOP 500 (elite performers)

2. **Truncated Sample**: We have a **left-truncated** or **right-tail** sample:
   - We only see the FASTEST 500 swimmers
   - The full distribution would include many slower swimmers
   - This creates a "cut-off" effect on the left side

3. **Expected Shape**: The full distribution would be **highly right-skewed**:
   - Most swimmers are slower
   - Few swimmers are very fast (elite)
   - Long tail of slower times

### What We're Actually Seeing

The **top 500** represents:
- The **right tail** (fastest end) of the true distribution
- An **elite competitive sample**
- Likely **1-5%** of all competitive swimmers in that age group/event

### Estimated Total Participation

**Conservative Estimates:**
- USA Swimming has ~400,000 registered members
- Competitive age group (15-18): ~80,000-120,000 active
- Per gender: ~40,000-60,000
- Per age (15, 16, 17, 18): ~10,000-15,000 per age
- Event participation varies:
  - 50 Free: ~40-45% = **4,000-6,750** total participants
  - 1500 Free: ~8-10% = **800-1,500** total participants

**Our Sample:**
- Top 500 swimmers
- Percentage captured: **~7-12%** for popular events (50 Free)
- Percentage captured: **~33-62%** for less popular events (1500 Free)

### Implications for Analysis

**Good News - This Works For MOT:**

1. ✅ **Z-scores are still valid** within the elite sample
   - We're comparing swimmers to other elite swimmers
   - Relative rankings are meaningful

2. ✅ **Percentiles are meaningful**
   - "Top 10%" of top 500 = truly elite
   - This is appropriate for setting standards

3. ✅ **Truncation doesn't hurt MOT**
   - We WANT elite standards
   - Setting standards based on top 500 is correct
   - We don't need slower swimmers for this purpose

4. ⚠️ **Cannot extrapolate to full population**
   - Z-scores in our sample ≠ z-scores in full population
   - Our "average" is really "elite average"
   - This is fine - we're not trying to represent all swimmers

### Distribution Shape Summary

**Full Population (hypothetical):**
- Shape: Highly right-skewed (long tail of slower times)
- Mean >> Median (mean pulled right by slow times)
- Most swimmers are slower

**Our Top 500 Sample:**
- Shape: Less skewed (truncated from left)
- May appear somewhat normal within this range
- Represents elite competitive swimmers
- Appropriate for setting MOT standards

## Next Steps

1. ✅ **Run validation script** to check ALL datasets for invalid times
2. ⚠️ **Add validation to all analysis scripts** that parse times
3. ✅ **Re-run analyses** with clean, validated data
4. 📊 **Run distribution shape analysis** for key events to confirm findings

## Files Created/Modified

- ✅ `create_zscore_distribution_graph.py` - Added validation + fixed Chart.js
- ✅ `validate_all_period_data.py` - Validates all period data files
- ✅ `analyze_distribution_shape.py` - Analyzes distribution shape and participation estimates




