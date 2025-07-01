#!/usr/bin/env python3
"""
Add sample data to DBT database for testing
"""

import mysql.connector
from mysql.connector import Error

def add_sample_data():
    """Add sample tables and data to DBT database"""
    
    try:
        connection = mysql.connector.connect(
            host='localhost',
            port=3306,
            database='DBT',
            user='sandy',
            password='sandy@123'
        )
        
        if connection.is_connected():
            print("✅ Connected to DBT database")
            
            cursor = connection.cursor()
            
            # Create users table
            print("Creating users table...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(50) NOT NULL UNIQUE,
                    email VARCHAR(100) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP NULL,
                    is_active BOOLEAN DEFAULT TRUE
                )
            """)
            
            # Create orders table
            print("Creating orders table...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    total_amount DECIMAL(10,2) NOT NULL,
                    status ENUM('pending', 'processing', 'shipped', 'delivered', 'cancelled') DEFAULT 'pending',
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            
            # Create products table
            print("Creating products table...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    description TEXT,
                    price DECIMAL(10,2) NOT NULL,
                    stock_quantity INT DEFAULT 0,
                    category VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Insert sample users
            print("Adding sample users...")
            users_data = [
                ('john_doe', 'john@example.com'),
                ('jane_smith', 'jane@example.com'),
                ('bob_wilson', 'bob@example.com'),
                ('alice_brown', 'alice@example.com'),
                ('charlie_davis', 'charlie@example.com')
            ]
            
            cursor.executemany("""
                INSERT INTO users (username, email) VALUES (%s, %s)
            """, users_data)
            
            # Insert sample products
            print("Adding sample products...")
            products_data = [
                ('Laptop', 'High-performance laptop', 999.99, 50, 'Electronics'),
                ('Smartphone', 'Latest smartphone model', 699.99, 100, 'Electronics'),
                ('Coffee Maker', 'Automatic coffee machine', 89.99, 25, 'Home'),
                ('Running Shoes', 'Comfortable athletic shoes', 129.99, 75, 'Sports'),
                ('Backpack', 'Durable travel backpack', 59.99, 30, 'Travel')
            ]
            
            cursor.executemany("""
                INSERT INTO products (name, description, price, stock_quantity, category) 
                VALUES (%s, %s, %s, %s, %s)
            """, products_data)
            
            # Insert sample orders
            print("Adding sample orders...")
            orders_data = [
                (1, 999.99, 'delivered'),
                (2, 699.99, 'shipped'),
                (3, 89.99, 'processing'),
                (1, 129.99, 'pending'),
                (4, 59.99, 'delivered'),
                (2, 1299.98, 'shipped'),
                (5, 89.99, 'cancelled')
            ]
            
            cursor.executemany("""
                INSERT INTO orders (user_id, total_amount, status) 
                VALUES (%s, %s, %s)
            """, orders_data)
            
            connection.commit()
            print("✅ Sample data added successfully!")
            
            # Show table statistics
            print("\n📊 Database Statistics:")
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]
            print(f"  - Users: {user_count}")
            
            cursor.execute("SELECT COUNT(*) FROM products")
            product_count = cursor.fetchone()[0]
            print(f"  - Products: {product_count}")
            
            cursor.execute("SELECT COUNT(*) FROM orders")
            order_count = cursor.fetchone()[0]
            print(f"  - Orders: {order_count}")
            
            cursor.close()
            connection.close()
            
            print("\n🎉 Sample database is ready for testing!")
            print("You can now:")
            print("1. Test the Chat feature with questions about this data")
            print("2. Run Analysis to see performance insights")
            print("3. Ask the AI about optimizing these tables")
            
        else:
            print("❌ Failed to connect to database")
            
    except Error as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    add_sample_data() 