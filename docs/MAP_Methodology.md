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

## Update Schedule
- **Annual Review**: Comprehensive review of target times
- **Data Analysis**: Analysis of improvement deltas between age groups
- **Target Adjustment**: Updates for ages 13, 15, and 17 based on data analysis

## Implementation
- **Database Integration**: Stored in `map_mot_aqua` table
- **Real-time Calculation**: Automatic points calculation during result entry
- **Reporting**: Integration with performance analytics dashboard

## Quality Assurance
- **Validation**: Regular validation against actual performance data
- **Calibration**: Adjustment based on observed performance patterns
- **Review Process**: Annual review by swimming technical committee

---
*This methodology document will be updated as the system evolves and new data becomes available.*
