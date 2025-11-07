Bakat Age Points — Interactive Web App
=================================================

Files in this package:
- bakat_web_lookup_app.py : Flask app. Edit WORKBOOK_FILENAME if your Excel file has a different name or path.
- templates/index.html    : Front-end template served by Flask.
- Malaysia On Track Times Spreadsheet Workbook (1).xlsx : Excel workbook with base times (must contain a sheet named "Bakat Base Times").
- Bakat_Age_Points_Interactive_Documentation.txt : Full technical and user documentation.
- (Optional) run_instructions.txt : Quick start commands.

-------------------------------------------------
How to Run (Basic)
-------------------------------------------------
1. Create a Python environment and install dependencies:
   pip install flask pandas openpyxl

2. Ensure your Excel workbook (the one with the "Bakat Base Times" sheet) is accessible.
   - Either place it one level above the app folder, as the default code expects:
       Malaysia On Track/
       ├── Malaysia On Track Times Spreadsheet Workbook (1).xlsx
       └── bakat_age_points-interactive_app/
           └── bakat_web_lookup_app.py
   - Or edit the WORKBOOK_FILENAME variable in bakat_web_lookup_app.py to point to your file’s path.

3. Run the Flask app:
   export FLASK_APP=bakat_web_lookup_app.py   (Windows: set FLASK_APP=bakat_web_lookup_app.py)
   flask run --host=0.0.0.0 --port=5000

4. Open your browser to:
   http://127.0.0.1:5000/

-------------------------------------------------
Notes
-------------------------------------------------
- The app auto-detects the Gender, Age, and Event columns from the Excel sheet.
- The base time column is assumed to be column E if headers are not descriptive.
- Swimmer time input accepts both mm:ss.ss (e.g., 2:13.45) and plain seconds (e.g., 133.45).
- Results display base time, swimmer time, and calculated points dynamically in the browser.
- The tool uses the formula:
    Points = 1000 × (Base Time / Swimmer Time)^3
- For deeper technical details, refer to Bakat_Age_Points_Interactive_Documentation.txt.
