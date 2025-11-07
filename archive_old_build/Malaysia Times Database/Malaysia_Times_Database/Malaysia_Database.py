import os
import sys
from flask import Flask
try:
    # When run as a module: python -m Malaysia_Times_Database.Malaysia_Database
    from Malaysia_Times_Database.age_points_blueprint import age_points
except ImportError:
    # When run as a script: python Malaysia_Times_Database\Malaysia_Database.py
    from age_points_blueprint import age_points

# Minimal landing app for the Malaysia Times Database
# Shows two choices: On Track or Age Points.

app = Flask(__name__)


# Mount the existing On Track Flask app under /on-track (robust import)
ontrack_app = None
try:
    from On_Track_Calculator.On_Track_Code import app as ontrack_app  # when project root on sys.path
except Exception:
    try:
        # Add project root (parent of this file's directory) and retry
        _pkg_dir = os.path.dirname(__file__)
        _proj_root = os.path.abspath(os.path.join(_pkg_dir, os.pardir))
        if _proj_root not in sys.path:
            sys.path.insert(0, _proj_root)
        from On_Track_Calculator.On_Track_Code import app as ontrack_app  # type: ignore
    except Exception:
        ontrack_app = None


if __name__ == "__main__":
    # Single-page site: run On Track app at root if available
    if ontrack_app is not None:
        ontrack_app.run(host="127.0.0.1", port=5000, debug=True)
    else:
        app.run(host="127.0.0.1", port=5000, debug=True)
