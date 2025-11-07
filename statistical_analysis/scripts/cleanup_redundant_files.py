# -*- coding: utf-8 -*-
"""
Clean up redundant files from old folder structure
"""
import os
import shutil
from pathlib import Path

# Get project root
project_root = Path(__file__).parent.parent.parent

# Files to delete (redundant copies from old structure)
files_to_delete = [
    # Old Statistical Analysis folder (if it exists)
    project_root / "Statistical Analysis" / "Delta_Comparison_USA_vs_Canada.csv",
    project_root / "Statistical Analysis" / "Delta_Comparison_USA_vs_Canada.html",
    project_root / "Statistical Analysis" / "MOT_Delta_Analysis_Results.csv",
    project_root / "Statistical Analysis" / "MOT_Delta_Index.csv",
    project_root / "Statistical Analysis" / "MOT_Delta_Index.html",
    
    # Parent reports folder (should be in statistical_analysis/reports/)
    project_root / "reports" / "Delta_Comparison_USA_vs_Canada.csv",
    project_root / "reports" / "Delta_Comparison_USA_vs_Canada.html",
    
    # Test file
    project_root / "statistical_analysis" / "reports" / "test_output.csv",
]

# Directories to check (to see if they should be deleted entirely)
dirs_to_check = [
    project_root / "Statistical Analysis",  # Entire old folder
]

print("🧹 Cleaning up redundant files...\n")

deleted_count = 0
for file_path in files_to_delete:
    if file_path.exists():
        try:
            file_path.unlink()
            print(f"✅ Deleted: {file_path.relative_to(project_root)}")
            deleted_count += 1
        except Exception as e:
            print(f"⚠️  Could not delete {file_path.relative_to(project_root)}: {e}")

# Check if old Statistical Analysis directory is empty or can be removed
old_stat_dir = project_root / "Statistical Analysis"
if old_stat_dir.exists():
    # Check if directory has important files or is just legacy
    important_files = list(old_stat_dir.glob("*.py")) + list(old_stat_dir.glob("*.txt"))
    important_files += list((old_stat_dir / "Delta Data").glob("**/*")) if (old_stat_dir / "Delta Data").exists() else []
    
    if len(important_files) > 10:  # Has data, just warn
        print(f"\n⚠️  Old 'Statistical Analysis' folder still exists with {len(important_files)} files")
        print(f"   Location: {old_stat_dir}")
        print(f"   Consider migrating any remaining files to 'statistical_analysis/' folder")
    else:
        print(f"\n✅ Old 'Statistical Analysis' folder appears to be empty or minimal")

print(f"\n✅ Cleanup complete: {deleted_count} files deleted")

