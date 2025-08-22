#!/usr/bin/env python3
"""
Test MongoDB Collections Demo
Verifies that our new NoSQL collections are working correctly
"""

import asyncio
import json
from pathlib import Path

async def test_mongodb_collections():
    """Test the MongoDB collections demo"""
    
    print("🧪 Testing MongoDB Collections Demo...")
    
    # Check if demo data exists
    demo_dir = Path("demo_data")
    if not demo_dir.exists():
        print("❌ Demo data directory not found!")
        return
    
    # List all demo files
    print(f"\n📁 Demo data directory: {demo_dir.absolute()}")
    demo_files = list(demo_dir.glob("*.json"))
    print(f"📄 Found {len(demo_files)} demo files:")
    
    for file in demo_files:
        print(f"   • {file.name}")
    
    # Load and verify each collection
    print("\n🔍 Verifying collections...")
    
    collections = [
        "user_profiles",
        "product_catalog", 
        "order_transactions",
        "analytics_events",
        "content_management"
    ]
    
    total_documents = 0
    
    for collection_name in collections:
        file_path = demo_dir / f"{collection_name}.json"
        
        if file_path.exists():
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                
                doc_count = len(data)
                total_documents += doc_count
                
                # Show sample document structure
                if data:
                    sample_doc = data[0]
                    print(f"\n✅ {collection_name}: {doc_count:,} documents")
                    print(f"   📊 Sample document keys: {list(sample_doc.keys())[:5]}...")
                    
                    # Show nested structure examples
                    if collection_name == "user_profiles" and "profile" in sample_doc:
                        print(f"   🏠 Nested profile structure: {list(sample_doc['profile'].keys())}")
                    elif collection_name == "product_catalog" and "variants" in sample_doc:
                        print(f"   🎨 Array field (variants): {len(sample_doc['variants'])} variants")
                    elif collection_name == "order_transactions" and "order_items" in sample_doc:
                        print(f"   📦 Array field (order_items): {len(sample_doc['order_items'])} items")
                    elif collection_name == "analytics_events" and "device" in sample_doc:
                        print(f"   📱 Nested device structure: {list(sample_doc['device'].keys())}")
                    elif collection_name == "content_management" and "content" in sample_doc:
                        print(f"   📝 Nested content structure: {list(sample_doc['content'].keys())}")
                        
            except Exception as e:
                print(f"❌ Error loading {collection_name}: {e}")
        else:
            print(f"❌ {collection_name}.json not found")
    
    print(f"\n📊 Total Documents Across All Collections: {total_documents:,}")
    
    # Load and display example queries
    queries_file = demo_dir / "mongodb_queries.json"
    if queries_file.exists():
        print(f"\n🔍 Example MongoDB Queries:")
        try:
            with open(queries_file, 'r') as f:
                queries = json.load(f)
            
            for collection_name, collection_queries in queries.items():
                print(f"\n📁 {collection_name}:")
                for query_name, query_info in collection_queries.items():
                    print(f"   • {query_info['description']}")
                    print(f"     Query: {query_info['query']}")
                    print(f"     Explanation: {query_info['explanation']}")
                    
        except Exception as e:
            print(f"❌ Error loading queries: {e}")
    
    # Show NoSQL features
    print(f"\n🎉 MongoDB NoSQL Features Demonstrated:")
    print("   • 📊 Nested Documents: Complex object structures")
    print("   • 🔢 Arrays: Multiple values in single fields")
    print("   • 🎭 Flexible Schema: Different document structures")
    print("   • 🔗 Complex Relationships: Embedded data")
    print("   • ⏰ Time-Series Data: Timestamp-based analytics")
    print("   • 📝 Rich Content: Mixed data types")
    
    print(f"\n💡 Next Steps:")
    print("   1. Open DBA-GPT web interface")
    print("   2. Go to 'NoSQL Assistant' section")
    print("   3. Select 'mongodb_demo' database")
    print("   4. Explore the new collections!")
    print("   5. Try the example queries")
    
    return True

if __name__ == "__main__":
    asyncio.run(test_mongodb_collections())
