#!/usr/bin/env python3
"""
Setup SQLite demo database for DBA-GPT
Creates sample tables and data for testing
"""

import sqlite3
import random
from datetime import datetime, timedelta
import os

def create_sqlite_demo():
    """Create SQLite demo database with sample tables and data"""
    
    db_path = "demo.db"
    
    print("🚀 Setting up SQLite demo database for DBA-GPT...")
    print(f"Database file: {db_path}")
    
    try:
        # Create/connect to SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("✅ Connected to SQLite database")
        
        # Create users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                role TEXT DEFAULT 'user' CHECK (role IN ('admin', 'user', 'moderator'))
            )
        """)
        print("✅ Users table created")
        
        # Create products table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                price REAL NOT NULL,
                category TEXT NOT NULL,
                stock_quantity INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✅ Products table created")
        
        # Create orders table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                order_number TEXT UNIQUE NOT NULL,
                total_amount REAL NOT NULL,
                status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'shipped', 'delivered', 'cancelled')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        print("✅ Orders table created")
        
        # Create order_items table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price REAL NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders (id),
                FOREIGN KEY (product_id) REFERENCES products (id)
            )
        """)
        print("✅ Order items table created")
        
        # Create indexes for better performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_category ON products(category)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON order_items(order_id)")
        print("✅ Indexes created")
        
        # Insert sample data
        print("\n📊 Inserting sample data...")
        
        # Sample users
        users_data = [
            ('john_doe', 'john@example.com', 'John', 'Doe', 'admin'),
            ('jane_smith', 'jane@example.com', 'Jane', 'Smith', 'user'),
            ('bob_wilson', 'bob@example.com', 'Bob', 'Wilson', 'user'),
            ('alice_brown', 'alice@example.com', 'Alice', 'Brown', 'moderator'),
            ('charlie_davis', 'charlie@example.com', 'Charlie', 'Davis', 'user'),
            ('diana_evans', 'diana@example.com', 'Diana', 'Evans', 'user'),
            ('frank_garcia', 'frank@example.com', 'Frank', 'Garcia', 'user'),
            ('grace_harris', 'grace@example.com', 'Grace', 'Harris', 'moderator')
        ]
        
        cursor.executemany("""
            INSERT OR IGNORE INTO users (username, email, first_name, last_name, role)
            VALUES (?, ?, ?, ?, ?)
        """, users_data)
        
        # Sample products
        products_data = [
            ('Laptop Pro', 'High-performance laptop with latest specs', 1299.99, 'Electronics', 50),
            ('Wireless Mouse', 'Ergonomic wireless mouse with precision tracking', 29.99, 'Electronics', 100),
            ('Coffee Mug', 'Ceramic coffee mug with handle', 12.99, 'Home', 200),
            ('Running Shoes', 'Comfortable running shoes for athletes', 89.99, 'Sports', 75),
            ('Backpack', 'Durable laptop backpack with multiple compartments', 49.99, 'Accessories', 60),
            ('Smartphone', 'Latest smartphone with advanced features', 799.99, 'Electronics', 30),
            ('Desk Lamp', 'LED desk lamp with adjustable brightness', 39.99, 'Home', 80),
            ('Yoga Mat', 'Non-slip yoga mat for fitness enthusiasts', 24.99, 'Sports', 120)
        ]
        
        cursor.executemany("""
            INSERT OR IGNORE INTO products (name, description, price, category, stock_quantity)
            VALUES (?, ?, ?, ?, ?)
        """, products_data)
        
        # Sample orders
        for i in range(1, 31):  # 30 sample orders
            user_id = random.randint(1, 8)
            order_number = f"ORD-{i:06d}"
            total_amount = round(random.uniform(50, 800), 2)
            status = random.choice(['pending', 'processing', 'shipped', 'delivered'])
            created_at = datetime.now() - timedelta(days=random.randint(0, 60))
            
            cursor.execute("""
                INSERT OR IGNORE INTO orders (user_id, order_number, total_amount, status, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, order_number, total_amount, status, created_at))
            
            # Add 1-4 items per order
            num_items = random.randint(1, 4)
            for j in range(num_items):
                product_id = random.randint(1, 8)
                quantity = random.randint(1, 3)
                unit_price = round(random.uniform(10, 150), 2)
                
                cursor.execute("""
                    INSERT OR IGNORE INTO order_items (order_id, product_id, quantity, unit_price)
                    VALUES (?, ?, ?, ?)
                """, (i, product_id, quantity, unit_price))
        
        # Commit all changes
        conn.commit()
        print("✅ Sample data inserted successfully")
        
        # Show table statistics
        tables = ['users', 'products', 'orders', 'order_items']
        
        print(f"\n📋 Database contains {len(tables)} tables:")
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"   - {table}: {count} records")
        
        # Show some sample queries
        print(f"\n🔍 Sample queries you can try:")
        print("   - 'What tables do I have in my database?'")
        print("   - 'Show me the schema of the users table'")
        print("   - 'How many orders are in my database?'")
        print("   - 'What products are in the Electronics category?'")
        print("   - 'Show me recent orders with their status'")
        
        print(f"\n🎉 SQLite demo database setup complete!")
        print(f"   Database file: {os.path.abspath(db_path)}")
        print(f"   Size: {os.path.getsize(db_path) / 1024:.1f} KB")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
        
    finally:
        if 'conn' in locals():
            conn.close()
            print("✅ Database connection closed")

if __name__ == "__main__":
    success = create_sqlite_demo()
    if success:
        print("\n🎉 Your SQLite database is ready for DBA-GPT!")
        print("   Go back to the web UI and try your query again.")
        print("   Make sure to select 'sqlite_demo' from the database dropdown.")
    else:
        print("\n❌ Failed to create database. Please check the error above.")
