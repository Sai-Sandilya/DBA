#!/usr/bin/env python3
"""
Test common MySQL root passwords
"""

import mysql.connector
from mysql.connector import Error

def test_root_passwords():
    """Test common root passwords"""
    
    common_passwords = [
        '',           # Empty password
        'root',       # Common root password
        'password',   # Common password
        'admin',      # Common admin password
        'mysql',      # MySQL default
        '123456',     # Common numeric password
        'root123',    # Root with numbers
        'admin123',   # Admin with numbers
        'password123' # Password with numbers
    ]
    
    print("Testing common MySQL root passwords...")
    print("=" * 50)
    
    for password in common_passwords:
        try:
            print(f"Trying password: '{password if password else '(empty)'}'")
            
            connection = mysql.connector.connect(
                host='localhost',
                port=3306,
                user='root',
                password=password
            )
            
            if connection.is_connected():
                print(f"✅ SUCCESS! Root password is: '{password if password else '(empty)'}'")
                
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
                
                cursor.close()
                connection.close()
                
                # Now create the sandy user
                print("\nCreating 'sandy' user...")
                create_sandy_user(password)
                
                return password
                
        except Error as e:
            print(f"❌ Failed: {e}")
            continue
    
    print("\n❌ None of the common passwords worked.")
    print("You'll need to:")
    print("1. Remember your root password from installation")
    print("2. Or reset the MySQL root password")
    return None

def create_sandy_user(root_password):
    """Create the sandy user with proper permissions"""
    try:
        connection = mysql.connector.connect(
            host='localhost',
            port=3306,
            user='root',
            password=root_password
        )
        
        cursor = connection.cursor()
        
        # Create user if it doesn't exist
        cursor.execute("CREATE USER IF NOT EXISTS 'sandy'@'localhost' IDENTIFIED BY 'sandy@123'")
        
        # Grant privileges
        cursor.execute("GRANT ALL PRIVILEGES ON *.* TO 'sandy'@'localhost'")
        cursor.execute("FLUSH PRIVILEGES")
        
        print("✅ Successfully created 'sandy' user with password 'sandy@123'")
        
        cursor.close()
        connection.close()
        
    except Error as e:
        print(f"❌ Error creating user: {e}")

if __name__ == "__main__":
    test_root_passwords() 