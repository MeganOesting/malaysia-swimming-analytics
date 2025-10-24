#!/usr/bin/env python3
"""
Malaysia Swimming Analytics - Data Migration Script
Migrates Excel data to PostgreSQL database
"""

import pandas as pd
import sqlalchemy as sa
from sqlalchemy import create_engine, text
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

def get_database_connection():
    """Get database connection"""
    database_url = os.getenv(
        "DATABASE_URL", 
        "postgresql://swimming_user:swimming_pass@localhost:5432/malaysia_swimming"
    )
    return create_engine(database_url)

def migrate_athletes():
    """Migrate athlete data from CSV to database"""
    print("Migrating athletes...")
    
    # Read athlete data
    athletes_file = project_root / "data" / "athletes" / "AthleteINFO.csv"
    if not athletes_file.exists():
        print(f"Warning: {athletes_file} not found")
        return
    
    df = pd.read_csv(athletes_file)
    print(f"Found {len(df)} athletes")
    
    # TODO: Implement athlete migration to database
    # This will be implemented once database schema is created
    
def migrate_meets():
    """Migrate meet data from Excel files to database"""
    print("Migrating meets...")
    
    meets_dir = project_root / "data" / "meets"
    excel_files = list(meets_dir.glob("*.xls*"))
    
    print(f"Found {len(excel_files)} meet files")
    
    for file_path in excel_files:
        print(f"Processing {file_path.name}...")
        # TODO: Implement meet data parsing and migration
        
def migrate_reference_data():
    """Migrate reference data (clubs, AQUA targets)"""
    print("Migrating reference data...")
    
    # TODO: Implement reference data migration
    
def main():
    """Main migration function"""
    print("Starting data migration...")
    
    try:
        # Test database connection
        engine = get_database_connection()
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("Database connection successful")
        
        # Run migrations
        migrate_athletes()
        migrate_meets()
        migrate_reference_data()
        
        print("Migration completed successfully!")
        
    except Exception as e:
        print(f"Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()


