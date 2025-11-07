# Malaysia vs USA Swimming Comparison - Placeholder

## Purpose

This document is a placeholder for future functionality that will compare Malaysia swimmer times with USA Swimming distribution curves.

## Planned Functionality

When Malaysia swimmer data is available, we will create reports that show:

1. **Where Malaysia Swimmers Rank:** For each age/event/gender combination, display where each Malaysia swimmer's time places them among the USA top 500 distribution.

2. **Z-Score Comparison:** Calculate the z-score for each Malaysia swimmer relative to the USA distribution, showing:
   - How many standard deviations above/below the USA mean
   - What percentile they fall into (if within the top 500)
   - Whether they fall into elite performance ranges (z ≥ 1.5, etc.)

3. **Visualization:** 
   - Overlay Malaysia swimmer markers on the USA distribution curves
   - Show scatter plots with Malaysia swimmers highlighted
   - Generate comparison tables showing rank positions

4. **Example Output:**
   - "Swimmer X's time of 26.50s places them at rank 120 in the USA 15-year-old female 50 Free distribution"
   - "This corresponds to a z-score of +2.15, meaning they are faster than 98% of USA swimmers in this age group"
   - Visual graph showing their position on the curve

## Data Requirements

- Malaysia swimmer times by age, event, gender
- USA distribution data (already available in database)
- Matching logic to ensure correct age/event/gender comparisons

## Implementation Status

**Status:** ⏳ Pending Malaysia data input

**When Ready:**
- This placeholder will be replaced with actual comparison reports
- Script will be created: `compare_malaysia_to_usa.py`
- Reports will be generated similar to event-specific MOT delta reports
- Integration with existing z-score distribution graphs

## Reminder

This task is on the project TODO list. When Malaysia swimmer data becomes available, implement the comparison functionality as described above.




