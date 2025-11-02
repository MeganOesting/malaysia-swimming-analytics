# Migration Log - Folder Reorganization
## Started: Today

## Stage 1: Fix Critical Scripts
- [ ] Fix build_delta_html.py to use relative paths
- [ ] Fix db_schema.py database path
- [ ] Update docker-compose.yml paths
- [ ] Update FastAPI main.py database path

## Stage 2: Create New Folder Structure
- [ ] Create reference_data/ folder structure
- [ ] Create meets/ folder structure  
- [ ] Create statistical_analysis/ folder structure
- [ ] Create times_database/ folder structure
- [ ] Create meet_reports/ folder structure (empty template)

## Stage 3: Move Reference Data
- [ ] Move data/reference/ → reference_data/imports/

## Stage 4: Move Meet Data
- [ ] Move data/meets/ → meets/active/2024-25/

## Stage 5: Move Statistical Analysis
- [ ] Move Statistical Analysis/ → statistical_analysis/
- [ ] Copy database for statistical analysis

## Stage 6: Move Times Database Project
- [ ] Move src/ → times_database/src/
- [ ] Move scripts/ → times_database/scripts/
- [ ] Move docker-compose.yml → times_database/
- [ ] Move other web app files

## Stage 7: Update All Paths
- [ ] Update all script imports
- [ ] Update database paths
- [ ] Update file references

## Stage 8: Verify & Test
- [ ] Test database connections
- [ ] Test scripts execute
- [ ] Verify HTML links work
- [ ] Check Docker configuration




