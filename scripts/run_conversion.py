#!/usr/bin/env python3
"""
Malaysia Swimming Analytics - Complete Data Conversion Process
Runs the full conversion from Excel to PostgreSQL
"""

import os
import sys
import subprocess
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"\n🔄 {description}")
    print(f"Running: {command}")
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        if result.stdout:
            print(f"Output: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed")
        print(f"Error: {e.stderr}")
        return False

def check_docker_running():
    """Check if Docker is running"""
    print("🔍 Checking Docker status...")
    
    try:
        result = subprocess.run("docker ps", shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Docker is running")
            return True
        else:
            print("❌ Docker is not running")
            return False
    except Exception as e:
        print(f"❌ Docker check failed: {e}")
        return False

def start_docker_services():
    """Start Docker services"""
    print("\n🐳 Starting Docker services...")
    
    # Change to project directory
    os.chdir(project_root)
    
    # Start services
    if run_command("docker-compose up -d", "Starting Docker services"):
        print("✅ Docker services started")
        return True
    else:
        print("❌ Failed to start Docker services")
        return False

def wait_for_database():
    """Wait for database to be ready"""
    print("\n⏳ Waiting for database to be ready...")
    
    import time
    from sqlalchemy import create_engine, text
    
    # Try to connect to database
    for attempt in range(30):  # Wait up to 30 seconds
        try:
            engine = create_engine("postgresql://swimming_user:swimming_pass@localhost:5432/malaysia_swimming")
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print("✅ Database is ready")
            return True
        except Exception:
            print(f"  Attempt {attempt + 1}/30: Database not ready yet...")
            time.sleep(1)
    
    print("❌ Database not ready after 30 seconds")
    return False

def run_conversion():
    """Run the data conversion"""
    print("\n🔄 Running data conversion...")
    
    # Change to project directory
    os.chdir(project_root)
    
    # Run the conversion script
    if run_command("python scripts/convert_meets_to_sql.py", "Converting Excel files to PostgreSQL"):
        print("✅ Data conversion completed")
        return True
    else:
        print("❌ Data conversion failed")
        return False

def verify_data():
    """Verify the converted data"""
    print("\n🔍 Verifying converted data...")
    
    from sqlalchemy import create_engine, text
    
    try:
        engine = create_engine("postgresql://swimming_user:swimming_pass@localhost:5432/malaysia_swimming")
        with engine.connect() as conn:
            # Check athlete count
            result = conn.execute(text("SELECT COUNT(*) FROM athletes"))
            athlete_count = result.fetchone()[0]
            print(f"  Athletes: {athlete_count}")
            
            # Check meet count
            result = conn.execute(text("SELECT COUNT(*) FROM meets"))
            meet_count = result.fetchone()[0]
            print(f"  Meets: {meet_count}")
            
            # Check result count
            result = conn.execute(text("SELECT COUNT(*) FROM results"))
            result_count = result.fetchone()[0]
            print(f"  Results: {result_count}")
            
            # Check event count
            result = conn.execute(text("SELECT COUNT(*) FROM events"))
            event_count = result.fetchone()[0]
            print(f"  Events: {event_count}")
            
            print("✅ Data verification completed")
            return True
            
    except Exception as e:
        print(f"❌ Data verification failed: {e}")
        return False

def main():
    """Main conversion process"""
    print("🏊‍♀️ Malaysia Swimming Analytics - Complete Data Conversion")
    print("=" * 60)
    
    # Check Docker
    if not check_docker_running():
        print("\n❌ Docker is not running. Please start Docker and try again.")
        return False
    
    # Start services
    if not start_docker_services():
        print("\n❌ Failed to start Docker services")
        return False
    
    # Wait for database
    if not wait_for_database():
        print("\n❌ Database is not ready")
        return False
    
    # Run conversion
    if not run_conversion():
        print("\n❌ Data conversion failed")
        return False
    
    # Verify data
    if not verify_data():
        print("\n❌ Data verification failed")
        return False
    
    print("\n🎉 Complete data conversion process finished successfully!")
    print("\n⚠️  IMPORTANT: Run these commands in TWO separate terminals:")
    print("\nTerminal 1 (Backend):")
    print("  cd \"C:\\Users\\megan\\OneDrive\\Documents\\Malaysia Swimming Analytics\"")
    print("  uvicorn src.web.main:app --reload --host 0.0.0.0 --port 8000")
    print("\nTerminal 2 (Frontend):")
    print("  cd \"C:\\Users\\megan\\OneDrive\\Documents\\Malaysia Swimming Analytics\"")
    print("  npm run dev")
    print("\nAccess points:")
    print("  - Frontend: http://localhost:3000 (or http://localhost:3001)")
    print("  - Backend API: http://localhost:8000")
    print("  - Admin Panel: http://localhost:3000/admin")
    print("\nTo restart backend: Press Ctrl+C and run the uvicorn command again")
    print("To restart frontend: Press Ctrl+C and run npm run dev again")
    
    return True

if __name__ == "__main__":
    main()









