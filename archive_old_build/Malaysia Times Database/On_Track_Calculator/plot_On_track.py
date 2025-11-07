import os`r`nimport pandas as pd
import matplotlib
matplotlib.use('TkAgg')          # ensures plots open on Windows
import matplotlib.pyplot as plt

# Load workbook (prefer top-level file in repo root)`r`n_BASE_DIR = os.path.dirname(__file__)`r`n_CANDIDATES = [`r`n    os.path.abspath(os.path.join(_BASE_DIR, "..", "Malaysia On Track Times Spreadsheet Workbook (1).xlsx")),`r`n    os.path.abspath(os.path.join(os.getcwd(), "Malaysia On Track Times Spreadsheet Workbook (1).xlsx")),`r`n    "Malaysia On Track Times Spreadsheet Workbook (1).xlsx",`r`n]`r`nfile_path = None`r`nfor _p in _CANDIDATES:`r`n    if os.path.exists(_p):`r`n        file_path = _p`r`n        break`r`nif not file_path:`r`n    file_path = _CANDIDATES[0]`r`npelapis = pd.read_excel(file_path, sheet_name="Pelapis Athlete Evaluation")
mot = pd.read_excel(file_path, sheet_name="MOT Tables 25")

# Clean column names
pelapis.columns = pelapis.columns.str.strip()
mot.columns = mot.columns.str.strip()

# Optional: print column names to check
print("Pelapis columns:", pelapis.columns.tolist())
print("MOT columns:", mot.columns.tolist())

# Filter for event and gender
pelapis_filtered = pelapis[(pelapis['Event'] == '100 Free') & (pelapis['Gender'] == 'F')]
mot_filtered = mot[(mot['Event'] == '100 Free') & (mot['Gender'] == 'F')]

# Exclude rows without valid time
pelapis_filtered = pelapis_filtered[pd.notnull(pelapis_filtered['Time'])]

# X and Y for Pelapis
pelapis_x = pelapis_filtered['Age']
pelapis_y = pelapis_filtered['AQUA']

# Determine line colors based on Qualifying Trigger
colors = pelapis_filtered['Qualifying Trigger'].apply(lambda x: 'orange' if str(x).upper() == 'Y' else 'black')

# X and Y for MOT benchmark
mot_x = mot_filtered['Age']
mot_y = mot_filtered['Malaysia Track AQUA']

# Determine Y-axis limits
y_min = min(pelapis_y.min(), mot_y.min()) - 10
y_max = 760  # hard-code the top of the Y-axis

# Create figure and axis
fig, ax = plt.subplots(figsize=(10,6))

# Plot Pelapis points as vertical lines using ax.plot (replaces vlines)
for x, y, c in zip(pelapis_x, pelapis_y, colors):
    y_clipped = min(y, y_max)
    ax.plot([x, x], [y_min, y_clipped], color=c, linewidth=2)

# Plot MOT benchmark
ax.plot(mot_x, mot_y, color='orange', linewidth=2, label='Malaysia On Track AQUA')

# Styling
ax.set_xlim(14.8, 21)
ax.set_xlabel("Age")
ax.set_ylabel("AQUA Points")
ax.set_title("Zi Xian Khew 100 Free: Progression vs Malaysia On Track")
ax.grid(True)
ax.legend()

# Adjust figure padding to reduce top margin
plt.subplots_adjust(top=0.95, bottom=0.1, left=0.1, right=0.95)

# Force exact Y-axis limits
ax.set_ylim(y_min, y_max)
ax.autoscale(enable=False)
plt.draw()                # render figure
ax.set_ylim(y_min, y_max) # enforce exact limits

plt.show()



