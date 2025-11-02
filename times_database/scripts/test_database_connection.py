#!/usr/bin/env python3
"""
Test database connection and verify schema
"""

import os
import sys
from pathlib import Path
from sqlalchemy import create_engine, text

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

def test_database_connection():
    """Test database connection"""
    print("🔍 Testing database connection...")
    
    # Try different connection strings
    connection_strings = [
        "postgresql://swimming_user:swimming_pass@localhost:5432/malaysia_swimming",
        "postgresql://swimming_user:swimming_pass@postgres:5432/malaysia_swimming",
        "postgresql://swimming_user:swimming_pass@127.0.0.1:5432/malaysia_swimming"
    ]
    
    for conn_str in connection_strings:
        try:
            print(f"Trying: {conn_str}")
            engine = create_engine(conn_str)
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                print(f"✅ Connection successful: {conn_str}")
                return engine
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            continue
    
    print("❌ All connection attempts failed")
    return None

def test_schema():
    """Test if schema exists"""
    print("\n🔍 Testing database schema...")
    
    engine = test_database_connection()
    if not engine:
        return False
    
    try:
        with engine.connect() as conn:
            # Check if tables exist
            tables = ['athletes', 'meets', 'results', 'events', 'clubs']
            for table in tables:
                result = conn.execute(text(f"""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = '{table}'
                    )
                """))
                exists = result.fetchone()[0]
                print(f"  {table}: {'✅' if exists else '❌'}")
            
            # Check table structure
            print("\n📊 Table structures:")
            for table in tables:
                try:
                    result = conn.execute(text(f"""
                        SELECT column_name, data_type 
                        FROM information_schema.columns 
                        WHERE table_name = '{table}'
                        ORDER BY ordinal_position
                    """))
                    columns = result.fetchall()
                    print(f"  {table}: {len(columns)} columns")
                    for col_name, col_type in columns:
                        print(f"    - {col_name}: {col_type}")
                except Exception as e:
                    print(f"    Error reading {table}: {e}")
            
            return True
            
    except Exception as e:
        print(f"❌ Schema test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 Malaysia Swimming Analytics - Database Connection Test")
    print("=" * 60)
    
    # Test connection
    engine = test_database_connection()
    if not engine:
        print("\n❌ Cannot proceed without database connection")
        print("Make sure Docker is running and database is accessible")
        return False
    
    # Test schema
    schema_ok = test_schema()
    if not schema_ok:
        print("\n❌ Schema issues detected")
        print("Run the init.sql script to create the schema")
        return False
    
    print("\n✅ Database connection and schema are ready!")
    print("You can now run the conversion script")
    return True

if __name__ == "__main__":
    main()



