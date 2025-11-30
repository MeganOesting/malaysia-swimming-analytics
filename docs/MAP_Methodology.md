# Malaysia Age Points (MAP) Methodology

## Overview
The Malaysia Age Points (MAP) system evaluates swimming performance across age groups 12-18 using age-anchored base times from USA Swimming's all-time top 100 times. It uses the AQUA points formula but with age-specific base times rather than senior level times.

## Purpose
- **Age Group Comparison**: Allow fair comparison between swimmers of different ages
- **Performance Tracking**: Track improvement across age groups
- **Talent Identification**: Identify promising swimmers at various age levels
- **Development Planning**: Guide training and development programs

## System Components

### Age Groups
- **12-18 years**: Primary age groups for MAP calculation
- **Gender Specific**: Separate calculations for male and female swimmers
- **Event Specific**: Different target times for each swimming event
- **Note**: MOT points extend up to age 23, but MAP focuses on age group development (12-18)

### Base Times Source
- **USA Swimming Database**: 100th all-time times for each gender/age group
- **Age 13**: Using the younger time minus the difference times × 0.65
- **Age 15**: Using the younger time minus the difference times × 0.60
- **Age 17**: Using the younger time minus the difference times × 0.55
- **Event Coverage**: All standard swimming events (Freestyle, Backstroke, Breaststroke, Butterfly, Individual Medley)

## Calculation Methodology

### Formula (From age_points_core.py)
```python
points = round(1000.0 * (base_seconds / swimmer_seconds) ** 3.0)
```

### Parameters
- **base_seconds**: Age-appropriate base time in seconds from MAP tables
- **swimmer_seconds**: Swimmer's recorded time in seconds
- **Cubic Formula**: Same as World Aquatics AQUA points (1000 * (base/time)³)

### Implementation Details
- **Gender Normalization**: Converts 'M'/'F' or 'Male'/'Female' to standard codes
- **Age Validation**: Integer age values only
- **Time Parsing**: Converts time strings to seconds
- **Error Handling**: Returns None for invalid inputs

## Data Sources
- **USA Swimming Database**: Largest available dataset spanning 30 years
- **100th All-Time Times**: Base times for each gender/age group
- **Age Group Categories**: 11-12, 13-14, 15-16, 17-18 (USA Swimming format)
- **Calculation Method**: Interpolation between age groups using specific multipliers

### When to Update MAP Base Times
- September of each calendar year whenn new 100th all-time times are published for age groups

### Update Process
1. Update the "Base:12-14-16-18" fields with the latest USA Swimming 100th all-time times for ages 12, 14, 16, 18 manually through the Update MAP Table Button
2. Interpolated ages (13, 15, 17) will auto-calculate using:
   - Age 13 = Age12 - (Age12 - Age14) x 0.65
   - Age 15 = Age14 - (Age14 - Age16) x 0.60
   - Age 17 = Age16 - (Age16 - Age18) x 0.55
3. Export "Base in Seconds" column to database `map_base_times` table

### Interpolation Rationale
The decreasing multipliers (0.65 -> 0.60 -> 0.55) reflect:
- Greater improvement rate in younger ages (12-14)
- Gradual slowdown in improvement rate as athletes mature
- Physiological development patterns in competitive swimmers

## Implementation
- **Database Table**: `map_base_times` (gender, event, age, base_time_seconds, increment)
- **Calculation Function**: `calculate_map_points()` in `src/web/utils/calculation_utils.py`
- **Formula**: `1000 x (base_seconds / swimmer_seconds)^3`
- **Reporting**: Integration with main page results table and Base Table Management exports

## Quality Assurance
- **Validation**: Regular validation against actual performance data
- **Calibration**: Adjustment based on observed performance patterns
- **Review Process**: Annual review by swimming technical director

---
*This methodology document will be updated as the system evolves and new data becomes available.*
