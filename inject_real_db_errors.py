#!/usr/bin/env python3
"""
Inject Real Database Errors into Running Web Interface
This creates actual database errors that will show in the UI's Recent Errors counter
"""

import asyncio
import sys
import os
import time
from datetime import datetime
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the same classes the web interface uses
from core.ai.dba_assistant import DBAAssistant
from core.config import Config
from core.database.connector import DatabaseError
from core.utils.logger import setup_logger

logger = setup_logger(__name__)

async def inject_real_database_errors():
    """Inject real database errors that will appear in the web interface"""
    
    print("🚨 INJECTING REAL DATABASE ERRORS")
    print("=" * 50)
    print("This will create ACTUAL MySQL errors in your database")
    print("that will be captured and show up in your web interface.")
    print()
    
    # Use the EXACT same configuration as the web interface
    config = Config()
    
    # Create a DBA Assistant instance (same as web interface)
    assistant = DBAAssistant(config)
    
    # Get MySQL database config
    db_config = config.databases.get("mysql")
    if not db_config:
        print("❌ No MySQL database found in configuration!")
        return 0
    
    print(f"✅ Connected to database: {db_config.database}")
    print(f"📊 Current errors in assistant: {len(assistant.recent_errors)}")
    print()
    
    # List of SQL queries that will cause REAL database errors
    error_queries = [
        {
            "name": "TABLE NOT FOUND",
            "query": "SELECT * FROM totally_missing_table_xyz123",
            "expected_error": "1146"
        },
        {
            "name": "SYNTAX ERROR", 
            "query": "SELECT * FROM WHERE INVALID SYNTAX",
            "expected_error": "1064"
        },
        {
            "name": "COLUMN NOT FOUND",
            "query": "SELECT non_existent_column_abc FROM users",
            "expected_error": "1054"
        },
        {
            "name": "INVALID FUNCTION",
            "query": "SELECT INVALID_FUNCTION(id) FROM users",
            "expected_error": "1305"
        },
        {
            "name": "PERMISSION ERROR",
            "query": "DROP DATABASE mysql",
            "expected_error": "1044"
        }
    ]
    
    captured_errors = 0
    
    for i, error_test in enumerate(error_queries, 1):
        print(f"🔥 ERROR {i}: {error_test['name']}")
        print(f"   Query: {error_test['query']}")
        
        try:
            # Get a fresh connection for each error
            connection = await assistant.db_connector.get_connection(db_config)
            
            # Execute the query that will fail
            await connection.execute_query(error_test['query'])
            
            print(f"   ⚠️  Unexpected: Query succeeded (should have failed)")
            
        except Exception as e:
            print(f"   ✅ Error captured: {type(e).__name__}: {str(e)[:80]}...")
            captured_errors += 1
            
        # Check how many errors are now stored
        current_error_count = len(assistant.recent_errors)
        print(f"   📊 Total errors captured: {current_error_count}")
        print()
        
        # Small delay between errors
        await asyncio.sleep(0.5)
    
    print("🎯 INJECTION COMPLETE")
    print("-" * 40)
    print(f"💥 Errors attempted: {len(error_queries)}")
    print(f"✅ Errors captured: {captured_errors}")
    print(f"📊 Total in assistant: {len(assistant.recent_errors)}")
    print()
    
    if assistant.recent_errors:
        print("🔍 CAPTURED ERROR DETAILS:")
        print("-" * 40)
        for i, error in enumerate(assistant.recent_errors, 1):
            print(f"{i}. {error.error_type} (Code: {error.error_code})")
            print(f"   Time: {error.timestamp.strftime('%H:%M:%S')}")
            print(f"   Query: {error.query[:50] if error.query else 'None'}...")
            print()
    
    print("🌐 NOW CHECK YOUR WEB INTERFACE:")
    print("   → Go to http://localhost:8502")
    print("   → Navigate to 'Monitoring' tab")
    print("   → Look at 'Auto-Error Resolution System'")
    print(f"   → Should show 'Recent Errors: {len(assistant.recent_errors)}'")
    print()
    
    return len(assistant.recent_errors)

async def test_web_interface_sync():
    """Test if errors sync with web interface"""
    print("🔄 TESTING WEB INTERFACE SYNCHRONIZATION")
    print("-" * 40)
    
    # Create multiple assistant instances to test sync
    config = Config()
    assistant1 = DBAAssistant(config)
    assistant2 = DBAAssistant(config)
    
    print(f"Assistant 1 errors: {len(assistant1.recent_errors)}")
    print(f"Assistant 2 errors: {len(assistant2.recent_errors)}")
    
    # Try to generate an error with assistant1
    try:
        db_config = config.databases.get("mysql")
        connection = await assistant1.db_connector.get_connection(db_config)
        await connection.execute_query("SELECT * FROM sync_test_table_missing")
    except Exception as e:
        print(f"Error generated with assistant1: {e}")
    
    print(f"After error - Assistant 1: {len(assistant1.recent_errors)}")
    print(f"After error - Assistant 2: {len(assistant2.recent_errors)}")
    
    if len(assistant1.recent_errors) != len(assistant2.recent_errors):
        print("⚠️  ERROR: Assistants not synchronized!")
        print("   Each DBA Assistant instance has separate error storage.")
        print("   Web interface may be using a different instance.")
    else:
        print("✅ Assistants are synchronized!")

if __name__ == "__main__":
    print("🚀 Starting Real Database Error Injection...")
    print(f"🕒 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # Run the error injection
        error_count = asyncio.run(inject_real_database_errors())
        
        # Test synchronization
        print("\n" + "=" * 60)
        asyncio.run(test_web_interface_sync())
        
        print("\n" + "=" * 60)
        if error_count > 0:
            print(f"🎉 SUCCESS! {error_count} real database errors injected!")
            print("🔄 Refresh your web interface to see the errors!")
            print("📊 Check the 'Recent Errors' counter in Monitoring tab!")
        else:
            print("❌ FAILED! No errors were captured.")
            print("🔧 There may be an issue with error capture system.")
            
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Script error: {e}")
        import traceback
        traceback.print_exc() 