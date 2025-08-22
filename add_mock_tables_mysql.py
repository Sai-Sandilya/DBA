#!/usr/bin/env python3
"""
Add mock tables with 5000 rows and 15 columns to MySQL database
"""

import mysql.connector
from mysql.connector import Error
import random
from datetime import datetime, timedelta
import time

def create_mock_tables():
    """Create two mock tables with 5000 rows and 15 columns each"""
    
    config = {
        'host': 'localhost',
        'port': 3306,
        'user': 'sandy',
        'password': 'sandy@123',
        'database': 'DBT'
    }
    
    print("🚀 Creating mock tables with 5000 rows and 15 columns each...")
    print("=" * 60)
    
    try:
        connection = mysql.connector.connect(**config)
        
        if connection.is_connected():
            print("✅ Connected to MySQL database")
            cursor = connection.cursor()
            
            # Create first table: customer_transactions
            print("\n📊 Creating customer_transactions table...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS customer_transactions (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    customer_id INT NOT NULL,
                    transaction_date DATETIME NOT NULL,
                    amount DECIMAL(10,2) NOT NULL,
                    currency VARCHAR(3) DEFAULT 'USD',
                    transaction_type VARCHAR(20) NOT NULL,
                    merchant_name VARCHAR(100),
                    category VARCHAR(50),
                    status VARCHAR(20) DEFAULT 'completed',
                    payment_method VARCHAR(30),
                    card_last_four VARCHAR(4),
                    location_city VARCHAR(50),
                    location_country VARCHAR(50),
                    fraud_score DECIMAL(3,2),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create second table: product_inventory
            print("📦 Creating product_inventory table...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS product_inventory (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    product_code VARCHAR(20) UNIQUE NOT NULL,
                    product_name VARCHAR(100) NOT NULL,
                    category VARCHAR(50) NOT NULL,
                    brand VARCHAR(50),
                    supplier_id INT,
                    unit_price DECIMAL(10,2) NOT NULL,
                    cost_price DECIMAL(10,2),
                    quantity_in_stock INT NOT NULL,
                    reorder_level INT DEFAULT 10,
                    warehouse_location VARCHAR(50),
                    expiry_date DATE,
                    weight_kg DECIMAL(5,2),
                    dimensions_cm VARCHAR(20),
                    is_active BOOLEAN DEFAULT TRUE,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
            """)
            
            print("✅ Tables created successfully!")
            
            # Generate sample data for customer_transactions
            print("\n🔄 Generating 5000 rows for customer_transactions...")
            
            transaction_types = ['purchase', 'refund', 'transfer', 'withdrawal', 'deposit']
            merchants = ['Amazon', 'Walmart', 'Target', 'Best Buy', 'Home Depot', 'Starbucks', 'McDonald\'s', 'Netflix', 'Spotify', 'Uber']
            categories = ['electronics', 'clothing', 'food', 'entertainment', 'transportation', 'home', 'health', 'education']
            payment_methods = ['credit_card', 'debit_card', 'paypal', 'apple_pay', 'google_pay', 'bank_transfer']
            cities = ['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix', 'Philadelphia', 'San Antonio', 'San Diego', 'Dallas', 'San Jose']
            countries = ['USA', 'Canada', 'UK', 'Germany', 'France', 'Australia', 'Japan', 'Brazil', 'India', 'Mexico']
            
            # Batch insert for better performance
            batch_size = 100
            for batch in range(0, 5000, batch_size):
                values = []
                for i in range(batch, min(batch + batch_size, 5000)):
                    transaction_date = datetime.now() - timedelta(days=random.randint(0, 365))
                    amount = round(random.uniform(10.0, 1000.0), 2)
                    
                    values.append((
                        random.randint(1000, 9999),  # customer_id
                        transaction_date,  # transaction_date
                        amount,  # amount
                        random.choice(['USD', 'EUR', 'GBP', 'CAD']),  # currency
                        random.choice(transaction_types),  # transaction_type
                        random.choice(merchants),  # merchant_name
                        random.choice(categories),  # category
                        random.choice(['completed', 'pending', 'failed']),  # status
                        random.choice(payment_methods),  # payment_method
                        str(random.randint(1000, 9999)),  # card_last_four
                        random.choice(cities),  # location_city
                        random.choice(countries),  # location_country
                        round(random.uniform(0.0, 1.0), 2),  # fraud_score
                    ))
                
                cursor.executemany("""
                    INSERT INTO customer_transactions 
                    (customer_id, transaction_date, amount, currency, transaction_type, 
                     merchant_name, category, status, payment_method, card_last_four, 
                     location_city, location_country, fraud_score)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, values)
                
                if batch % 1000 == 0:
                    print(f"   Inserted {batch + batch_size} rows...")
            
            # Generate sample data for product_inventory
            print("\n🔄 Generating 5000 rows for product_inventory...")
            
            brands = ['Apple', 'Samsung', 'Sony', 'LG', 'Nike', 'Adidas', 'Coca-Cola', 'Pepsi', 'Nestle', 'Unilever']
            categories = ['electronics', 'clothing', 'food', 'beverages', 'home', 'sports', 'beauty', 'automotive']
            warehouses = ['Warehouse A', 'Warehouse B', 'Warehouse C', 'Warehouse D', 'Warehouse E']
            
            for batch in range(0, 5000, batch_size):
                values = []
                for i in range(batch, min(batch + batch_size, 5000)):
                    product_code = f"PROD{str(i+1).zfill(6)}"
                    unit_price = round(random.uniform(5.0, 500.0), 2)
                    cost_price = round(unit_price * random.uniform(0.4, 0.8), 2)
                    
                    values.append((
                        product_code,  # product_code
                        f"Product {i+1}",  # product_name
                        random.choice(categories),  # category
                        random.choice(brands),  # brand
                        random.randint(1, 100),  # supplier_id
                        unit_price,  # unit_price
                        cost_price,  # cost_price
                        random.randint(0, 1000),  # quantity_in_stock
                        random.randint(5, 50),  # reorder_level
                        random.choice(warehouses),  # warehouse_location
                        datetime.now().date() + timedelta(days=random.randint(30, 365)),  # expiry_date
                        round(random.uniform(0.1, 10.0), 2),  # weight_kg
                        f"{random.randint(10,50)}x{random.randint(10,50)}x{random.randint(5,30)}",  # dimensions_cm
                        random.choice([True, False]),  # is_active
                    ))
                
                cursor.executemany("""
                    INSERT INTO product_inventory 
                    (product_code, product_name, category, brand, supplier_id, unit_price, 
                     cost_price, quantity_in_stock, reorder_level, warehouse_location, 
                     expiry_date, weight_kg, dimensions_cm, is_active)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, values)
                
                if batch % 1000 == 0:
                    print(f"   Inserted {batch + batch_size} rows...")
            
            # Commit the changes
            connection.commit()
            
            # Verify the data
            print("\n🔍 Verifying data...")
            cursor.execute("SELECT COUNT(*) FROM customer_transactions")
            trans_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM product_inventory")
            inv_count = cursor.fetchone()[0]
            
            print(f"✅ customer_transactions: {trans_count} rows")
            print(f"✅ product_inventory: {inv_count} rows")
            
            # Show table structure
            print("\n📋 Table Structure:")
            cursor.execute("DESCRIBE customer_transactions")
            print("\ncustomer_transactions columns:")
            for col in cursor.fetchall():
                print(f"  - {col[0]} ({col[1]})")
            
            cursor.execute("DESCRIBE product_inventory")
            print("\nproduct_inventory columns:")
            for col in cursor.fetchall():
                print(f"  - {col[0]} ({col[1]})")
            
            cursor.close()
            connection.close()
            
            print("\n🎉 SUCCESS! Two mock tables created with 5000 rows each!")
            print("   You can now query these tables in your DBA-GPT web interface.")
            print("   Go to http://localhost:8501 and select 'mysql_dbt' database.")
            
        else:
            print("❌ Failed to connect to MySQL")
            
    except Error as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    create_mock_tables()
