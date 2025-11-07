
README
======

Files in this package:
- app.py              : Flask app. Edit WORKBOOK_FILENAME if your Excel file has a different name.
- templates/index.html: Frontend template served by Flask.
- Bakat_Base_Times.xlsx: (NOT included) Place your workbook in the same folder and name it Bakat_Base_Times.xlsx
- run_instructions.txt: quick run commands.

How to run (basic):
1. Create a Python environment and install dependencies:
   pip install flask pandas openpyxl

2. Put your Excel workbook (the one with the "Bakat Base Times" sheet) in the same folder and name it 'Bakat_Base_Times.xlsx' or edit the WORKBOOK_FILENAME in app.py.

3. Run the app:
   export FLASK_APP=app.py   (Windows: set FLASK_APP=app.py)
   flask run --host=0.0.0.0 --port=5000

4. Open your browser to http://127.0.0.1:5000/

Notes:
- The app will try to detect the Gender, Age, and Event columns heuristically.
- The base time column is assumed to be column E if headers are non-descriptive. If your sheet has clearer headers, it will use them.
- Swimmer time input accepts mm:ss.ff or plain seconds.
