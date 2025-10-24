# AQUA Points System Methodology

## Overview
The AQUA Points System is the official World Aquatics (formerly FINA) points system used internationally to compare swimming performances across different events, genders, and time periods. This system provides a standardized way to evaluate swimming performance on a global scale.

## Purpose
- **International Comparison**: Compare performances across different countries and time periods
- **Event Standardization**: Standardize scoring across all swimming events
- **Performance Ranking**: Create global rankings of swimming performances
- **Olympic Qualification**: Used in Olympic and World Championship qualification processes

## System Components

### Base Times
- **Senior Level**: Base times for senior swimmers (no age groups)
- **Gender Specific**: Separate base times for male and female swimmers
- **Event Coverage**: All Olympic and World Championship events
- **Time Standards**: Based on world record performances and elite competition results

### Scoring Formula (From your code and World Aquatics)
```
AQUA Points = 1000 × (Base Time / Actual Time)³
```

### Parameters
- **Base Time**: World Aquatics established base time for the event (senior level)
- **Actual Time**: Swimmer's recorded time
- **Cubic Formula**: Same formula used by World Aquatics for international comparison

### Implementation Details
- **Pre-calculated**: AQUA points are read directly from column K in meet files
- **Base Times**: From AQUA POINTS sheet in Podium_On_Track_Target_AQUA.xlsx
- **Headers**: Row 1; base times: row 2 (male), row 3 (female)
- **Formula**: `AQUA = int(1000 * (baseSec / tSec)^3)`

## World Aquatics Standards

### Base Time Establishment
- **World Records**: Based on current world record performances
- **Elite Competition**: Analysis of top international performances
- **Statistical Analysis**: Comprehensive analysis of elite swimming data
- **Regular Updates**: Annual review and updates by World Aquatics

### Event Categories
- **Freestyle**: 50m, 100m, 200m, 400m, 800m, 1500m
- **Backstroke**: 50m, 100m, 200m
- **Breaststroke**: 50m, 100m, 200m
- **Butterfly**: 50m, 100m, 200m
- **Individual Medley**: 200m, 400m
- **Relay Events**: 4x100m, 4x200m Freestyle, 4x100m Medley

## Implementation in Malaysia Swimming Analytics

### Database Integration
- **Table**: `map_mot_aqua` (AQUA base times)
- **Real-time Calculation**: Automatic AQUA points calculation
- **Performance Tracking**: Integration with performance analytics

### Update Schedule
- **Annual Updates**: Updates following World Aquatics annual review
- **Administrator Managed**: Updates managed by system administrator
- **Automatic Sync**: Integration with World Aquatics official updates

## Scoring Interpretation

### Point Ranges
- **1000+ Points**: World record level performance
- **900-999 Points**: Elite international level
- **800-899 Points**: Strong international level
- **700-799 Points**: Good international level
- **600-699 Points**: Competitive international level
- **Below 600 Points**: Development level

### Performance Categories
- **Elite**: 900+ AQUA points
- **International**: 800-899 AQUA points
- **National**: 700-799 AQUA points
- **Competitive**: 600-699 AQUA points
- **Development**: Below 600 AQUA points

## Quality Assurance
- **World Aquatics Validation**: Official World Aquatics standards
- **Regular Updates**: Annual updates from World Aquatics
- **International Alignment**: Consistent with global swimming standards
- **Performance Validation**: Regular validation against international results

## Future Considerations
- **System Evolution**: Adaptation to World Aquatics system changes
- **Technology Integration**: Enhanced calculation and reporting tools
- **International Alignment**: Continued alignment with global standards

---
*This methodology document reflects the official World Aquatics AQUA Points System as implemented in the Malaysia Swimming Analytics platform.*
