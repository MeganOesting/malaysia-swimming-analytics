# Web Design Notes for MOT Delta Analysis

## Landing Page Structure

The landing page (`MOT_Delta_Analysis_Index.html`) should be organized as follows:

### 1. **Header Section**
- Title: "Malaysia On Track (MOT) Delta Analysis"
- Subtitle: Brief description
- Summary statistics in cards: Total analyses, total athlete records, average sample size

### 2. **Methodology Overview Section** (Above the fold)
- **Purpose:** Explain key assumptions and data characteristics BEFORE users dive into specific event data
- **Key Information to Include:**
  - Elite sample only (top 500 swimmers)
  - What percentage of total population this represents (~7-12% for popular events)
  - Distribution shape explanation (highly right-skewed full population, left-truncated elite sample)
  - Why this is NOT normal, and why that's OK
  - Why elite-focused data is appropriate for MOT standards
- **Link:** Full methodology report for detailed explanations

### 3. **Navigation Section**
- Quick links to:
  - USA vs Canada Comparison Report
  - Full Methodology & Assumptions Report
  - Event-specific reports (organized by event)

### 4. **Event-Based Table**
- Group rows by event for easier navigation
- Each event should have a header row
- Clickable links to:
  - Individual delta analysis reports (CSV and HTML)
  - Delta data folders
- Use icons for better UX (📁 folder, 📊 CSV, 📄 report)

## Key Design Principles

1. **Information Hierarchy:**
   - Methodology FIRST (above table)
   - Then navigation
   - Then detailed data table

2. **Progressive Disclosure:**
   - Landing page: High-level overview + methodology
   - Event selection: Click to see specific event details
   - Individual reports: Deep dive into specific transitions

3. **Consistent Navigation:**
   - All pages should link back to landing page
   - Methodology report linked prominently
   - Comparison reports easily accessible

4. **Visual Hierarchy:**
   - Use color coding for sections (methodology box, navigation section)
   - Clear typography hierarchy (h1, h2, h3)
   - Statistics displayed in cards for quick scanning

## Files Structure

```
MOT_Delta_Analysis_Index.html          # Landing page (main entry point)
├── MOT_Data_Methodology_and_Assumptions.html  # Full methodology report
├── Delta_Comparison_USA_vs_Canada.html        # USA vs Canada comparison
└── [Event-specific reports]
    ├── F_50_Free_MOT_Delta_Analysis.html
    ├── F_50_Free_Age15_Distribution.html
    └── ... (other event-specific reports)
```

## User Flow

1. **Landing Page** → User reads methodology overview
2. **Select Event** → User clicks on specific event in table
3. **Event Report** → User views detailed analysis for that event
4. **Additional Resources** → User can access comparison reports or methodology details

## Notes for Future Development

- Consider adding a search/filter function for the table
- Event-specific landing pages could group all transitions for that event
- Interactive charts could be embedded directly on landing page
- Consider adding a "Quick Start Guide" for first-time users




