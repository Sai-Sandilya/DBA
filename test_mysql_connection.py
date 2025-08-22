#!/usr/bin/env python3
"""
Quick MySQL connection test
"""

import mysql.connector
from mysql.connector import Error

def test_mysql():
    """Test MySQL connection"""
    
    print("🔍 Testing MySQL Connection...")
    print("=" * 50)
    
    config = {
        'host': 'localhost',
        'port': 3306,
        'user': 'sandy',
        'password': 'sandy@123',
        'database': 'DBT'
    }
    
    try:
        # Try connecting
        connection = mysql.connector.connect(**config)
        
        if connection.is_connected():
            print("✅ SUCCESS: MySQL is working!")
            
            cursor = connection.cursor()
            
            # Show databases
            cursor.execute("SHOW DATABASES")
            databases = cursor.fetchall()
            print(f"\n📊 Available databases:")
            for db in databases:
                print(f"  - {db[0]}")
            
            # Show tables in DBT
            cursor.execute("USE DBT")
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            print(f"\n📋 Tables in 'DBT' database:")
            if tables:
                for table in tables:
                    print(f"  - {table[0]}")
            else:
                print("  (No tables found)")
            
            cursor.close()
            connection.close()
            
            print("\n🎉 MySQL is ready! You can now use it in the web UI.")
            print("   Go to http://localhost:8501 and select 'mysql_dbt' from the dropdown.")
            
        else:
            print("❌ FAILED: Could not connect to MySQL")
            
    except Error as e:
        print(f"❌ ERROR: {e}")
        print("\n🔧 To fix this:")
        print("1. Install XAMPP: https://www.apachefriends.org/download.html")
        print("2. Start MySQL in XAMPP Control Panel")
        print("3. Run this script again")
        print("\n   OR")
        print("1. Use the SQLite database (already working)")
        print("2. Go to http://localhost:8501 and use 'sqlite_demo'")

if __name__ == "__main__":
    test_mysql()
