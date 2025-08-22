#!/usr/bin/env python3
"""
MongoDB Collections Setup Script
Creates distinctive NoSQL collections with nested documents, arrays, and flexible schemas
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta
import random
import json

async def setup_mongodb_collections():
    """Set up MongoDB collections with NoSQL-specific data structures"""
    
    # Connect to MongoDB
    client = AsyncIOMotorClient('mongodb://localhost:27017/')
    db = client['testdb']
    
    print("🚀 Setting up MongoDB collections with NoSQL features...")
    
    # 1. User Profiles Collection - Nested documents and arrays
    print("\n📝 Creating 'user_profiles' collection...")
    user_profiles = []
    
    for i in range(100):
        user_profile = {
            "_id": f"user_{i+1:04d}",
            "username": f"user{i+1}",
            "email": f"user{i+1}@example.com",
            "profile": {
                "first_name": f"User{i+1}",
                "last_name": f"LastName{i+1}",
                "age": random.randint(18, 65),
                "location": {
                    "city": random.choice(["New York", "London", "Tokyo", "Paris", "Sydney"]),
                    "country": random.choice(["USA", "UK", "Japan", "France", "Australia"]),
                    "coordinates": {
                        "latitude": round(random.uniform(-90, 90), 6),
                        "longitude": round(random.uniform(-180, 180), 6)
                    }
                },
                "interests": random.sample([
                    "technology", "sports", "music", "cooking", "travel", 
                    "photography", "reading", "gaming", "fitness", "art"
                ], random.randint(2, 5)),
                "social_media": {
                    "twitter": f"@user{i+1}",
                    "linkedin": f"linkedin.com/in/user{i+1}",
                    "instagram": f"@user{i+1}_insta"
                }
            },
            "preferences": {
                "theme": random.choice(["light", "dark", "auto"]),
                "language": random.choice(["en", "es", "fr", "de", "ja"]),
                "notifications": {
                    "email": random.choice([True, False]),
                    "push": random.choice([True, False]),
                    "sms": random.choice([True, False])
                }
            },
            "created_at": datetime.now() - timedelta(days=random.randint(1, 365)),
            "last_login": datetime.now() - timedelta(hours=random.randint(1, 168)),
            "is_active": random.choice([True, False]),
            "tags": random.sample([
                "premium", "verified", "early_adopter", "beta_tester", 
                "power_user", "newbie", "moderator", "admin"
            ], random.randint(1, 3))
        }
        user_profiles.append(user_profile)
    
    # Insert user profiles
    await db.user_profiles.insert_many(user_profiles)
    print(f"✅ Created {len(user_profiles)} user profiles with nested documents")
    
    # 2. Product Catalog Collection - Array fields and mixed data types
    print("\n🛍️ Creating 'product_catalog' collection...")
    product_catalog = []
    
    categories = ["electronics", "clothing", "books", "home", "sports", "beauty", "toys", "automotive"]
    brands = ["TechCorp", "StyleBrand", "BookWorld", "HomeEssentials", "SportMax", "BeautyGlow", "ToyLand", "AutoTech"]
    
    for i in range(200):
        # Generate random product data
        category = random.choice(categories)
        brand = random.choice(brands)
        
        product = {
            "_id": f"prod_{i+1:06d}",
            "name": f"{brand} {category.title()} Product {i+1}",
            "category": category,
            "brand": brand,
            "sku": f"{brand[:3].upper()}-{category[:3].upper()}-{i+1:06d}",
            "pricing": {
                "base_price": round(random.uniform(10.0, 1000.0), 2),
                "currency": "USD",
                "discount_percentage": random.randint(0, 50) if random.random() > 0.7 else 0,
                "tax_rate": round(random.uniform(0.05, 0.15), 3)
            },
            "inventory": {
                "quantity": random.randint(0, 1000),
                "reserved": random.randint(0, 50),
                "warehouse_locations": random.sample([
                    "NYC-East", "NYC-West", "LA-Central", "Chicago-North", 
                    "Houston-South", "Miami-East", "Seattle-West", "Denver-Central"
                ], random.randint(1, 3))
            },
            "specifications": {
                "dimensions": {
                    "length": round(random.uniform(1, 100), 2),
                    "width": round(random.uniform(1, 100), 2),
                    "height": round(random.uniform(1, 100), 2),
                    "unit": "cm"
                },
                "weight": {
                    "value": round(random.uniform(0.1, 50.0), 2),
                    "unit": "kg"
                },
                "materials": random.sample([
                    "plastic", "metal", "wood", "fabric", "glass", "ceramic", "leather", "silicone"
                ], random.randint(1, 4))
            },
            "variants": [
                {
                    "color": random.choice(["red", "blue", "green", "black", "white", "yellow", "purple", "orange"]),
                    "size": random.choice(["XS", "S", "M", "L", "XL", "XXL"]) if category == "clothing" else "standard",
                    "price_adjustment": round(random.uniform(-20.0, 20.0), 2),
                    "stock": random.randint(0, 200)
                } for _ in range(random.randint(1, 5))
            ],
            "ratings": [
                {
                    "user_id": f"user_{random.randint(1, 100):04d}",
                    "rating": random.randint(1, 5),
                    "comment": random.choice([
                        "Great product!", "Good quality", "Could be better", "Excellent!", "Not bad"
                    ]),
                    "date": datetime.now() - timedelta(days=random.randint(1, 30))
                } for _ in range(random.randint(0, 8))
            ],
            "tags": random.sample([
                "featured", "bestseller", "new", "trending", "limited_edition", 
                "eco_friendly", "premium", "budget", "gift", "seasonal"
            ], random.randint(2, 5)),
            "created_at": datetime.now() - timedelta(days=random.randint(1, 365)),
            "updated_at": datetime.now() - timedelta(days=random.randint(1, 30))
        }
        product_catalog.append(product)
    
    # Insert product catalog
    await db.product_catalog.insert_many(product_catalog)
    print(f"✅ Created {len(product_catalog)} products with arrays and mixed data types")
    
    # 3. Order Transactions Collection - Complex nested structures and arrays
    print("\n📦 Creating 'order_transactions' collection...")
    order_transactions = []
    
    for i in range(500):
        # Generate order items
        num_items = random.randint(1, 5)
        order_items = []
        subtotal = 0
        
        for j in range(num_items):
            product_id = f"prod_{random.randint(1, 200):06d}"
            quantity = random.randint(1, 5)
            unit_price = round(random.uniform(15.0, 500.0), 2)
            item_total = quantity * unit_price
            subtotal += item_total
            
            order_item = {
                "product_id": product_id,
                "product_name": f"Product {product_id.split('_')[1]}",
                "quantity": quantity,
                "unit_price": unit_price,
                "item_total": item_total,
                "options": {
                    "color": random.choice(["red", "blue", "green", "black", "white"]),
                    "size": random.choice(["S", "M", "L", "XL"]) if random.random() > 0.5 else None
                }
            }
            order_items.append(order_item)
        
        # Calculate totals
        tax_rate = round(random.uniform(0.05, 0.15), 3)
        tax_amount = round(subtotal * tax_rate, 2)
        shipping_cost = round(random.uniform(5.0, 25.0), 2) if subtotal < 100 else 0
        total = subtotal + tax_amount + shipping_cost
        
        # Generate shipping address
        shipping_address = {
            "type": random.choice(["home", "work", "other"]),
            "street": f"{random.randint(100, 9999)} {random.choice(['Main St', 'Oak Ave', 'Pine Rd', 'Elm Blvd'])}",
            "city": random.choice(["New York", "Los Angeles", "Chicago", "Houston", "Phoenix"]),
            "state": random.choice(["NY", "CA", "IL", "TX", "AZ", "FL", "PA", "OH"]),
            "zip_code": f"{random.randint(10000, 99999)}",
            "country": "USA"
        }
        
        # Generate payment info
        payment_methods = ["credit_card", "debit_card", "paypal", "apple_pay", "google_pay"]
        payment_info = {
            "method": random.choice(payment_methods),
            "transaction_id": f"txn_{random.randint(100000, 999999)}",
            "status": random.choice(["completed", "pending", "failed"]),
            "last_four": f"{random.randint(1000, 9999)}" if "card" in random.choice(payment_methods) else None
        }
        
        order = {
            "_id": f"order_{i+1:08d}",
            "order_number": f"ORD-{datetime.now().year}-{i+1:06d}",
            "customer_id": f"user_{random.randint(1, 100):04d}",
            "customer_email": f"customer{i+1}@example.com",
            "order_date": datetime.now() - timedelta(days=random.randint(1, 365)),
            "status": random.choice(["pending", "processing", "shipped", "delivered", "cancelled"]),
            "order_items": order_items,
            "pricing": {
                "subtotal": round(subtotal, 2),
                "tax_rate": tax_rate,
                "tax_amount": tax_amount,
                "shipping_cost": shipping_cost,
                "discount_amount": round(random.uniform(0, subtotal * 0.2), 2) if random.random() > 0.8 else 0,
                "total": round(total, 2)
            },
            "shipping": {
                "address": shipping_address,
                "method": random.choice(["standard", "express", "overnight"]),
                "tracking_number": f"TRK{random.randint(100000000, 999999999)}" if random.random() > 0.3 else None,
                "estimated_delivery": datetime.now() + timedelta(days=random.randint(1, 14))
            },
            "payment": payment_info,
            "notes": random.choice([
                "Please deliver during business hours",
                "Leave at front door if no answer",
                "Gift for birthday",
                "Handle with care",
                None
            ]),
            "metadata": {
                "source": random.choice(["web", "mobile_app", "phone", "in_store"]),
                "campaign": random.choice(["summer_sale", "holiday_special", "new_customer", "loyalty_reward", None]),
                "referrer": random.choice(["google", "facebook", "instagram", "email", "direct", None])
            }
        }
        order_transactions.append(order)
    
    # Insert order transactions
    await db.order_transactions.insert_many(order_transactions)
    print(f"✅ Created {len(order_transactions)} orders with complex nested structures")
    
    # 4. Analytics Events Collection - Time-series data and flexible schema
    print("\n📊 Creating 'analytics_events' collection...")
    analytics_events = []
    
    event_types = ["page_view", "product_view", "add_to_cart", "purchase", "search", "click", "scroll", "form_submit"]
    page_names = ["home", "products", "product_detail", "cart", "checkout", "search_results", "category", "about"]
    
    for i in range(1000):
        event_time = datetime.now() - timedelta(
            days=random.randint(0, 30),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59)
        )
        
        event = {
            "_id": f"event_{i+1:010d}",
            "timestamp": event_time,
            "event_type": random.choice(event_types),
            "session_id": f"session_{random.randint(1, 1000):06d}",
            "user_id": f"user_{random.randint(1, 100):04d}" if random.random() > 0.3 else None,
            "anonymous_id": f"anon_{random.randint(100000, 999999)}" if random.random() > 0.7 else None,
            "page": {
                "name": random.choice(page_names),
                "url": f"https://example.com/{random.choice(page_names)}",
                "referrer": random.choice([
                    "https://google.com", "https://facebook.com", "https://twitter.com", 
                    "https://linkedin.com", "direct", None
                ])
            },
            "device": {
                "type": random.choice(["desktop", "mobile", "tablet"]),
                "browser": random.choice(["Chrome", "Firefox", "Safari", "Edge"]),
                "os": random.choice(["Windows", "macOS", "iOS", "Android", "Linux"]),
                "screen_resolution": random.choice(["1920x1080", "1366x768", "375x667", "768x1024"])
            },
            "location": {
                "country": random.choice(["USA", "UK", "Canada", "Germany", "France", "Japan", "Australia"]),
                "region": random.choice(["CA", "NY", "TX", "FL", "ON", "BC", "England", "Bavaria"]),
                "city": random.choice(["New York", "Los Angeles", "Chicago", "Toronto", "London", "Berlin", "Paris"])
            },
            "properties": {
                "product_id": f"prod_{random.randint(1, 200):06d}" if random.random() > 0.5 else None,
                "category": random.choice(["electronics", "clothing", "books", "home"]) if random.random() > 0.6 else None,
                "search_query": random.choice(["laptop", "shoes", "cookbook", "furniture"]) if random.random() > 0.8 else None,
                "value": round(random.uniform(10.0, 500.0), 2) if random.random() > 0.7 else None
            },
            "user_agent": f"Mozilla/5.0 ({random.choice(['Windows NT 10.0', 'Macintosh; Intel Mac OS X 10_15', 'iPhone; CPU iPhone OS 14_0'])}; rv:{random.randint(80, 100)}.0) Gecko/20100101 Firefox/{random.randint(80, 100)}.0",
            "ip_address": f"{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}",
            "session_duration": random.randint(0, 3600) if random.random() > 0.5 else None
        }
        analytics_events.append(event)
    
    # Insert analytics events
    await db.analytics_events.insert_many(analytics_events)
    print(f"✅ Created {len(analytics_events)} analytics events with flexible schema")
    
    # 5. Content Management Collection - Rich text and media references
    print("\n📝 Creating 'content_management' collection...")
    content_management = []
    
    content_types = ["blog_post", "product_page", "landing_page", "help_article", "news_item", "tutorial"]
    authors = ["John Smith", "Jane Doe", "Mike Johnson", "Sarah Wilson", "David Brown", "Lisa Garcia"]
    
    for i in range(150):
        content_type = random.choice(content_types)
        
        # Generate content based on type
        if content_type == "blog_post":
            title = f"Amazing Blog Post About {random.choice(['Technology', 'Business', 'Lifestyle', 'Travel', 'Food'])} {i+1}"
            content = f"This is a detailed blog post about {random.choice(['technology trends', 'business strategies', 'lifestyle tips', 'travel destinations', 'cooking recipes'])}. It contains multiple paragraphs with valuable information for our readers."
        elif content_type == "product_page":
            title = f"Product Page for {random.choice(['Premium Laptop', 'Smart Watch', 'Wireless Headphones', 'Gaming Console'])}"
            content = f"Detailed product description with features, specifications, and benefits. Includes high-quality images and customer reviews."
        else:
            title = f"{content_type.replace('_', ' ').title()} {i+1}"
            content = f"Content for {content_type} with relevant information and details."
        
        content_doc = {
            "_id": f"content_{i+1:06d}",
            "title": title,
            "slug": title.lower().replace(" ", "-").replace("'", "").replace(",", ""),
            "content_type": content_type,
            "status": random.choice(["draft", "published", "archived", "scheduled"]),
            "author": {
                "name": random.choice(authors),
                "id": f"author_{random.randint(1, 6):02d}",
                "email": f"author{random.randint(1, 6)}@example.com"
            },
            "content": {
                "body": content,
                "excerpt": content[:150] + "..." if len(content) > 150 else content,
                "word_count": len(content.split()),
                "reading_time": round(len(content.split()) / 200, 1)  # 200 words per minute
            },
            "seo": {
                "meta_title": f"SEO Title for {title}",
                "meta_description": f"SEO description for {title} with relevant keywords",
                "keywords": random.sample([
                    "technology", "business", "lifestyle", "travel", "food", "health", "fitness", "education"
                ], random.randint(3, 6)),
                "canonical_url": f"https://example.com/{content_type.replace('_', '/')}/{i+1}"
            },
            "media": {
                "featured_image": f"https://example.com/images/{content_type}_{i+1}.jpg",
                "gallery": [
                    f"https://example.com/images/{content_type}_{i+1}_1.jpg",
                    f"https://example.com/images/{content_type}_{i+1}_2.jpg"
                ] if random.random() > 0.5 else [],
                "video_url": f"https://example.com/videos/{content_type}_{i+1}.mp4" if random.random() > 0.8 else None
            },
            "publishing": {
                "created_at": datetime.now() - timedelta(days=random.randint(1, 365)),
                "published_at": datetime.now() - timedelta(days=random.randint(1, 30)) if random.random() > 0.3 else None,
                "scheduled_for": datetime.now() + timedelta(days=random.randint(1, 30)) if random.random() > 0.1 else None,
                "last_modified": datetime.now() - timedelta(days=random.randint(1, 7))
            },
            "categories": random.sample([
                "technology", "business", "lifestyle", "travel", "food", "health", "fitness", "education"
            ], random.randint(1, 3)),
            "tags": random.sample([
                "featured", "trending", "popular", "new", "updated", "premium", "exclusive"
            ], random.randint(1, 3)),
            "engagement": {
                "views": random.randint(100, 10000),
                "likes": random.randint(10, 500),
                "shares": random.randint(5, 100),
                "comments": random.randint(0, 50)
            },
            "access_control": {
                "is_public": random.choice([True, False]),
                "requires_login": random.choice([True, False]),
                "user_groups": random.sample([
                    "admin", "moderator", "premium", "regular", "guest"
                ], random.randint(1, 3)) if random.random() > 0.7 else []
            }
        }
        content_management.append(content_doc)
    
    # Insert content management
    await db.content_management.insert_many(content_management)
    print(f"✅ Created {len(content_management)} content documents with rich text and media")
    
    # Create indexes for better performance
    print("\n🔍 Creating database indexes...")
    
    # User profiles indexes
    await db.user_profiles.create_index("profile.location.city")
    await db.user_profiles.create_index("profile.interests")
    await db.user_profiles.create_index("created_at")
    
    # Product catalog indexes
    await db.product_catalog.create_index("category")
    await db.product_catalog.create_index("brand")
    await db.product_catalog.create_index("pricing.base_price")
    await db.product_catalog.create_index("tags")
    
    # Order transactions indexes
    await db.order_transactions.create_index("customer_id")
    await db.order_transactions.create_index("order_date")
    await db.order_transactions.create_index("status")
    await db.order_transactions.create_index("pricing.total")
    
    # Analytics events indexes
    await db.analytics_events.create_index("timestamp")
    await db.analytics_events.create_index("event_type")
    await db.analytics_events.create_index("user_id")
    await db.analytics_events.create_index("page.name")
    
    # Content management indexes
    await db.content_management.create_index("content_type")
    await db.content_management.create_index("status")
    await db.content_management.create_index("author.id")
    await db.content_management.create_index("publishing.published_at")
    
    print("✅ Created database indexes for optimal performance")
    
    # Print collection statistics
    print("\n📊 MongoDB Collections Summary:")
    print("=" * 50)
    
    collections = ["user_profiles", "product_catalog", "order_transactions", "analytics_events", "content_management"]
    
    for collection_name in collections:
        count = await db[collection_name].count_documents({})
        print(f"📁 {collection_name}: {count:,} documents")
    
    print("\n🎉 MongoDB NoSQL collections setup complete!")
    print("💡 These collections showcase MongoDB's NoSQL features:")
    print("   • Nested documents and arrays")
    print("   • Flexible schemas")
    print("   • Mixed data types")
    print("   • Complex relationships")
    print("   • Time-series data")
    print("   • Rich content structures")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(setup_mongodb_collections())
