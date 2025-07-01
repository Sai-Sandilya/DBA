#!/usr/bin/env python3
"""
Simple MySQL connection test script
"""

import mysql.connector
from mysql.connector import Error

def test_mysql_connection():
    """Test MySQL connection with current credentials"""
    
    # Test with current config
    config = {
        'host': 'localhost',
        'port': 3306,
        'database': 'DBT',
        'user': 'sandy',
        'password': 'sandy@123'
    }
    
    print("Testing MySQL connection...")
    print(f"Host: {config['host']}")
    print(f"Port: {config['port']}")
    print(f"Database: {config['database']}")
    print(f"User: {config['user']}")
    print("-" * 50)
    
    try:
        # First try without specifying database
        connection = mysql.connector.connect(
            host=config['host'],
            port=config['port'],
            user=config['user'],
            password=config['password']
        )
        
        if connection.is_connected():
            print("✅ SUCCESS: Connected to MySQL server!")
            
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
            
            # Try to connect to specific database
            cursor.close()
            connection.close()
            
            print("\nTrying to connect to specific database 'DBT'...")
            connection = mysql.connector.connect(**config)
            
            if connection.is_connected():
                print("✅ SUCCESS: Connected to database 'DBT'!")
                cursor = connection.cursor()
                
                # Show tables
                cursor.execute("SHOW TABLES")
                tables = cursor.fetchall()
                print(f"\nTables in 'DBT' database:")
                if tables:
                    for table in tables:
                        print(f"  - {table[0]}")
                else:
                    print("  (No tables found)")
                
                cursor.close()
                connection.close()
            else:
                print("❌ FAILED: Could not connect to database 'DBT'")
                
    except Error as e:
        print(f"❌ ERROR: {e}")
        
        # Try with root user
        print("\nTrying with root user...")
        try:
            root_config = {
                'host': 'localhost',
                'port': 3306,
                'user': 'root',
                'password': ''  # Try empty password
            }
            
            connection = mysql.connector.connect(**root_config)
            if connection.is_connected():
                print("✅ SUCCESS: Connected as root!")
                
                cursor = connection.cursor()
                cursor.execute("SELECT VERSION()")
                version = cursor.fetchone()
                print(f"MySQL Version: {version[0]}")
                
                # Show users
                cursor.execute("SELECT User, Host FROM mysql.user")
                users = cursor.fetchall()
                print("\nMySQL users:")
                for user in users:
                    print(f"  - {user[0]}@{user[1]}")
                
                cursor.close()
                connection.close()
            else:
                print("❌ FAILED: Could not connect as root")
                
        except Error as root_error:
            print(f"❌ ROOT ERROR: {root_error}")

if __name__ == "__main__":
    test_mysql_connection() 