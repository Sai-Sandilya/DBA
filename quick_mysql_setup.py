#!/usr/bin/env python3
"""
Quick MySQL connection test and setup
"""

import mysql.connector
from mysql.connector import Error
import subprocess
import sys

def test_mysql_connection():
    """Test MySQL connection with your config"""
    
    config = {
        'host': 'localhost',
        'port': 3306,
        'user': 'sandy',
        'password': 'sandy@123',
        'database': 'DBT'
    }
    
    print("🔍 Testing MySQL connection...")
    print(f"   Host: {config['host']}:{config['port']}")
    print(f"   User: {config['user']}")
    print(f"   Database: {config['database']}")
    print()
    
    try:
        # Try connecting without database first
        connection = mysql.connector.connect(
            host=config['host'],
            port=config['port'],
            user=config['user'],
            password=config['password']
        )
        
        if connection.is_connected():
            print("✅ Successfully connected to MySQL server!")
            
            cursor = connection.cursor()
            
            # Create database if it doesn't exist
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {config['database']}")
            print(f"✅ Database '{config['database']}' ready")
            
            # Create a simple test table
            cursor.execute(f"USE {config['database']}")
            
            test_table = """
            CREATE TABLE IF NOT EXISTS test_table (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            cursor.execute(test_table)
            
            # Insert test data
            cursor.execute("INSERT IGNORE INTO test_table (name) VALUES ('Test Record')")
            connection.commit()
            
            # Verify data
            cursor.execute("SELECT COUNT(*) FROM test_table")
            count = cursor.fetchone()[0]
            
            print(f"✅ Test table created with {count} records")
            print("🎉 MySQL is working perfectly!")
            
            return True
            
    except Error as e:
        print(f"❌ Connection failed: {e}")
        print("\n🔧 Let's troubleshoot:")
        
        if "Can't connect to MySQL server" in str(e):
            print("1. MySQL server is not running")
            print("2. Start MySQL service:")
            print("   - Open Services (services.msc)")
            print("   - Find 'MySQL' or 'MySQL80' service")
            print("   - Right-click → Start")
            print()
            print("   OR use command line:")
            print("   net start MySQL80")
            print("   net start MySQL")
            
        elif "Access denied" in str(e):
            print("1. Wrong username/password")
            print("2. User doesn't exist")
            print("3. User doesn't have permissions")
            print()
            print("Try connecting as root:")
            print("mysql -u root -p")
            
        elif "Unknown database" in str(e):
            print("1. Database doesn't exist")
            print("2. Create it manually:")
            print("   CREATE DATABASE DBT;")
            
        return False
        
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

def check_mysql_installation():
    """Check if MySQL is installed"""
    print("🔍 Checking MySQL installation...")
    
    # Check common MySQL paths
    mysql_paths = [
        r"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe",
        r"C:\Program Files\MySQL\MySQL Server 5.7\bin\mysql.exe",
        r"C:\xampp\mysql\bin\mysql.exe",
        r"C:\wamp64\bin\mysql\mysql8.0.31\bin\mysql.exe",
        r"C:\laragon\bin\mysql\mysql-8.0.30-winx64\bin\mysql.exe"
    ]
    
    for path in mysql_paths:
        try:
            result = subprocess.run([path, "--version"], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print(f"✅ MySQL found at: {path}")
                return path
        except:
            continue
    
    print("❌ MySQL not found in common locations")
    return None

def main():
    print("🚀 MySQL Connection Test for DBA-GPT")
    print("=" * 50)
    
    # Check if MySQL is installed
    mysql_path = check_mysql_installation()
    
    if not mysql_path:
        print("\n📥 MySQL not found. Install options:")
        print("1. Download from: https://dev.mysql.com/downloads/mysql/")
        print("2. Use XAMPP: https://www.apachefriends.org/")
        print("3. Use WAMP: https://www.wampserver.com/")
        print("4. Use Laragon: https://laragon.org/")
        return
    
    # Test connection
    success = test_mysql_connection()
    
    if success:
        print("\n🎉 Your MySQL is ready for DBA-GPT!")
        print("   Go back to the web UI and try your query again.")
    else:
        print("\n💡 Quick fixes to try:")
        print("1. Start MySQL service")
        print("2. Check if port 3306 is free")
        print("3. Verify username/password")
        print("4. Try connecting with MySQL Workbench")

if __name__ == "__main__":
    main()
