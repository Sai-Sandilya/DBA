#!/usr/bin/env python3
"""
Setup MySQL user with correct credentials
"""

import mysql.connector
from mysql.connector import Error

def setup_mysql_user():
    """Setup the sandy user with correct credentials"""
    
    root_password = "Sandy@123"
    
    print("Testing MySQL root connection...")
    print("=" * 50)
    
    try:
        # Test root connection
        connection = mysql.connector.connect(
            host='localhost',
            port=3306,
            user='root',
            password=root_password
        )
        
        if connection.is_connected():
            print("✅ SUCCESS: Connected to MySQL as root!")
            
            cursor = connection.cursor()
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()
            print(f"MySQL Version: {version[0]}")
            
            # Show databases
            cursor.execute("SHOW DATABASES")
            databases = cursor.fetchall()
            print("\nAvailable databases:")
            for db in databases:
                print(f"  - {db[0]}")
            
            # Check if DBT database exists
            dbt_exists = any(db[0] == 'DBT' for db in databases)
            if not dbt_exists:
                print("\nCreating DBT database...")
                cursor.execute("CREATE DATABASE IF NOT EXISTS DBT")
                print("✅ Created DBT database")
            
            # Create sandy user
            print("\nSetting up 'sandy' user...")
            
            # Drop user if exists (to recreate with new password)
            try:
                cursor.execute("DROP USER IF EXISTS 'sandy'@'localhost'")
            except:
                pass
            
            # Create user
            cursor.execute("CREATE USER 'sandy'@'localhost' IDENTIFIED BY 'sandy@123'")
            
            # Grant privileges
            cursor.execute("GRANT ALL PRIVILEGES ON *.* TO 'sandy'@'localhost'")
            cursor.execute("FLUSH PRIVILEGES")
            
            print("✅ Successfully created 'sandy' user with password 'sandy@123'")
            
            cursor.close()
            connection.close()
            
            # Test the new user
            print("\nTesting 'sandy' user connection...")
            test_sandy_connection()
            
        else:
            print("❌ FAILED: Could not connect as root")
            
    except Error as e:
        print(f"❌ ERROR: {e}")

def test_sandy_connection():
    """Test the sandy user connection"""
    try:
        connection = mysql.connector.connect(
            host='localhost',
            port=3306,
            database='DBT',
            user='sandy',
            password='sandy@123'
        )
        
        if connection.is_connected():
            print("✅ SUCCESS: 'sandy' user can connect to DBT database!")
            
            cursor = connection.cursor()
            
            # Show tables
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            print(f"\nTables in 'DBT' database:")
            if tables:
                for table in tables:
                    print(f"  - {table[0]}")
            else:
                print("  (No tables found - this is normal for a new database)")
            
            cursor.close()
            connection.close()
            
            print("\n🎉 MySQL setup complete! Your DBA-GPT application should now work.")
            
        else:
            print("❌ FAILED: 'sandy' user cannot connect")
            
    except Error as e:
        print(f"❌ ERROR testing sandy user: {e}")

if __name__ == "__main__":
    setup_mysql_user() 