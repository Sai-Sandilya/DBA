#!/usr/bin/env python3
"""
Setup script for MySQL demo database
Creates sample tables and data for DBA-GPT testing
"""

import mysql.connector
from mysql.connector import Error
import random
from datetime import datetime, timedelta

def create_demo_database():
    """Create demo database with sample tables and data"""
    
    # Database configuration from your config.yaml
    config = {
        'host': 'localhost',
        'port': 3306,
        'user': 'sandy',
        'password': 'sandy@123',
        'database': 'DBT'
    }
    
    try:
        # First connect without database to create it
        connection = mysql.connector.connect(
            host=config['host'],
            port=config['port'],
            user=config['user'],
            password=config['password']
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            
            # Create database if it doesn't exist
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {config['database']}")
            print(f"✅ Database '{config['database']}' created/verified")
            
            # Use the database
            cursor.execute(f"USE {config['database']}")
            
            # Create users table
            users_table = """
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                first_name VARCHAR(50) NOT NULL,
                last_name VARCHAR(50) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE,
                role ENUM('admin', 'user', 'moderator') DEFAULT 'user'
            )
            """
            cursor.execute(users_table)
            print("✅ Users table created")
            
            # Create orders table
            orders_table = """
            CREATE TABLE IF NOT EXISTS orders (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                order_number VARCHAR(20) UNIQUE NOT NULL,
                total_amount DECIMAL(10,2) NOT NULL,
                status ENUM('pending', 'processing', 'shipped', 'delivered', 'cancelled') DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                INDEX idx_user_id (user_id),
                INDEX idx_status (status),
                INDEX idx_created_at (created_at)
            )
            """
            cursor.execute(orders_table)
            print("✅ Orders table created")
            
            # Create products table
            products_table = """
            CREATE TABLE IF NOT EXISTS products (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                description TEXT,
                price DECIMAL(10,2) NOT NULL,
                category VARCHAR(50) NOT NULL,
                stock_quantity INT DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_category (category),
                INDEX idx_price (price)
            )
            """
            cursor.execute(products_table)
            print("✅ Products table created")
            
            # Create order_items table
            order_items_table = """
            CREATE TABLE IF NOT EXISTS order_items (
                id INT AUTO_INCREMENT PRIMARY KEY,
                order_id INT NOT NULL,
                product_id INT NOT NULL,
                quantity INT NOT NULL,
                unit_price DECIMAL(10,2) NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
                FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
                INDEX idx_order_id (order_id),
                INDEX idx_product_id (product_id)
            )
            """
            cursor.execute(order_items_table)
            print("✅ Order items table created")
            
            # Insert sample data
            print("\n📊 Inserting sample data...")
            
            # Sample users
            users_data = [
                ('john_doe', 'john@example.com', 'John', 'Doe', 'admin'),
                ('jane_smith', 'jane@example.com', 'Jane', 'Smith', 'user'),
                ('bob_wilson', 'bob@example.com', 'Bob', 'Wilson', 'user'),
                ('alice_brown', 'alice@example.com', 'Alice', 'Brown', 'moderator'),
                ('charlie_davis', 'charlie@example.com', 'Charlie', 'Davis', 'user')
            ]
            
            for user in users_data:
                cursor.execute("""
                    INSERT IGNORE INTO users (username, email, first_name, last_name, role)
                    VALUES (%s, %s, %s, %s, %s)
                """, user)
            
            # Sample products
            products_data = [
                ('Laptop Pro', 'High-performance laptop', 1299.99, 'Electronics', 50),
                ('Wireless Mouse', 'Ergonomic wireless mouse', 29.99, 'Electronics', 100),
                ('Coffee Mug', 'Ceramic coffee mug', 12.99, 'Home', 200),
                ('Running Shoes', 'Comfortable running shoes', 89.99, 'Sports', 75),
                ('Backpack', 'Durable laptop backpack', 49.99, 'Accessories', 60)
            ]
            
            for product in products_data:
                cursor.execute("""
                    INSERT IGNORE INTO products (name, description, price, category, stock_quantity)
                    VALUES (%s, %s, %s, %s, %s)
                """, product)
            
            # Sample orders
            for i in range(1, 21):  # 20 sample orders
                user_id = random.randint(1, 5)
                order_number = f"ORD-{i:06d}"
                total_amount = round(random.uniform(50, 500), 2)
                status = random.choice(['pending', 'processing', 'shipped', 'delivered'])
                created_at = datetime.now() - timedelta(days=random.randint(0, 30))
                
                cursor.execute("""
                    INSERT IGNORE INTO orders (user_id, order_number, total_amount, status, created_at)
                    VALUES (%s, %s, %s, %s, %s)
                """, (user_id, order_number, total_amount, status, created_at))
                
                # Add 1-3 items per order
                num_items = random.randint(1, 3)
                for j in range(num_items):
                    product_id = random.randint(1, 5)
                    quantity = random.randint(1, 3)
                    unit_price = round(random.uniform(10, 100), 2)
                    
                    cursor.execute("""
                        INSERT IGNORE INTO order_items (order_id, product_id, quantity, unit_price)
                        VALUES (%s, %s, %s, %s)
                    """, (i, product_id, quantity, unit_price))
            
            connection.commit()
            print("✅ Sample data inserted successfully")
            
            # Show table statistics
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            
            print(f"\n📋 Database '{config['database']}' contains {len(tables)} tables:")
            for table in tables:
                table_name = table[0]
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                print(f"   - {table_name}: {count} records")
            
            print(f"\n🎉 Demo database setup complete!")
            print(f"   Database: {config['database']}")
            print(f"   Host: {config['host']}:{config['port']}")
            print(f"   User: {config['user']}")
            
    except Error as e:
        print(f"❌ Error: {e}")
        print("\n🔧 Troubleshooting tips:")
        print("1. Make sure MySQL server is running")
        print("2. Check if user 'sandy' exists and has proper permissions")
        print("3. Verify the password is correct")
        print("4. Ensure MySQL is listening on localhost:3306")
        
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("✅ Database connection closed")

if __name__ == "__main__":
    print("🚀 Setting up MySQL demo database for DBA-GPT...")
    create_demo_database()
