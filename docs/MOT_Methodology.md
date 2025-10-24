# Malaysia On Track (MOT) Methodology

## Overview
The Malaysia On Track (MOT) system is a data-driven pathway to identify swimmers with the highest potential to deliver international medals for Malaysia. Based on Canada's successful On Track methodology, it provides age-specific progression benchmarks from entry age (15) to arrival age (25).

## Purpose
- **Medal Potential Identification**: Identify swimmers with verified medal potential
- **Development Pathway**: Track progression from age 15 to 25
- **Resource Allocation**: Guide funding to athletes with highest medal potential
- **Performance Benchmarking**: Compare swimmers against international progression standards

## System Components

### Entry Age: 15
- **Physical Maturity**: By age 15, physical maturity has evened out
- **Predictive Performance**: Training and skill become main drivers of improvement
- **Reliable Tracking**: Performance tracking becomes meaningful and predictive

### Arrival Age: 25
- **Development Window**: Swimmers who haven't reached benchmarks by 25 are statistically unlikely to do so
- **Peak Performance**: Covers the typical age range for international medal success
- **Extended Support**: Provides support through critical development years

### Age Range: 15-23
- **Entry Age**: 15 (when tracking becomes predictive)
- **MOT Calculation**: Up to age 23 (senior level times comparable to AQUA points)
- **Senior Level**: MOT uses senior level times that can be compared to AQUA points

## Calculation Methodology

### Progression Curve Development
```python
# Build age-based improvement curve using Canada data
# Combined yearly changes from all tracks into single average progression
progression_curve = build_progression_curve(gender, event, entry_age=15, arrival_age=25)
```

### Target Time Calculation
```python
# Anchor each event's progression curve
entry_age = 15
arrival_age = 25
arrival_time = previous_sea_games_bronze_time

# Build progression curve with Canada data
target_times = calculate_target_times(gender, event, age, progression_curve)
```

### AQUA Points Standardization
```python
# Convert times to AQUA points for standardized comparison
base_seconds = get_aqua_base_time(gender, event)
target_seconds = convert_time_to_seconds(target_time)
aqua_points = int(1000 * (base_seconds / target_seconds) ** 3)
```

### On Track Assessment
```python
# Compare swimmer's performance to age-appropriate target
swimmer_aqua = calculate_aqua_points(swimmer_time, gender, event)
target_aqua = get_target_aqua_for_age(gender, event, age)
difference = swimmer_aqua - target_aqua

# Positive = ahead of track, Zero = on track, Negative = behind track
```

## Data Sources
- **Canada On Track Data**: Over 2 million world-class performances from international competitions
- **Progression Benchmarks**: Average progression rates of Canadian age-group swimmers
- **SEA Games Bronze Times**: Arrival time benchmarks for each event
- **AQUA Base Times**: World Aquatics base times for standardization

## Implementation Notes
- **Track 1**: 4-year progression length (early developers)
- **Track 2**: 5-year progression length (normal developers)  
- **Track 3**: 6-year progression length (late developers)
- **Standardization**: All times converted to AQUA points for fair comparison
- **Extended Support**: MOT provides support through age 23, extending beyond current Malaysia cutoff of 21

## Key Benefits
- **Extended Development Window**: Support through critical years (15-25)
- **Data-Driven Decisions**: Based on proven international progression data
- **Medal Focus**: Specifically designed to identify medal potential
- **Resource Optimization**: Direct funding to athletes with highest medal potential

## Success Metrics
- **Canada's Results**: 
  - Rio 2016: 1 Gold, 1 Silver, 2 Bronze
  - Tokyo 2021: 1 Gold, 2 Silver, 2 Bronze  
  - Paris 2024: 4 Gold, 1 Silver, 0 Bronze
- **Pipeline Development**: Seamless path from talent identification to podium qualification
- **Medal Return**: Maximized medal return on investment

---
*This methodology is based on Canada's successful On Track system and adapted for Malaysian swimming development pathways.*
